"""Subscription tiering and payment integration for PanganLaba.

This module is backend-only: it never changes the Streamlit UI. It layers
paid plans, payment records and optional Stripe webhook handling on top of
the existing local `accounts` store (src/pangan_forecast/accounts.py).

Design notes:
- No new third-party dependency: Stripe webhook signatures are verified with
  stdlib ``hmac``/``hashlib`` (Stripe uses HMAC-SHA256 over ``t.<payload>``).
- If no payment provider is configured, the module degrades gracefully to the
  existing manual admin activation flow (scripts/activate_subscription.py), so
  the current behaviour is preserved.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Default plan catalogue. Prices are in Rupiah per interval.
PLANS: list[dict] = [
    {
        "id": "starter",
        "name": "Starter",
        "price_idr": 150_000,
        "interval": "month",
        "interval_count": 1,
        "features": ["1 pengguna", "3 komoditas", "Dashboard dasar"],
    },
    {
        "id": "pro",
        "name": "Pro",
        "price_idr": 300_000,
        "interval": "month",
        "interval_count": 1,
        "features": ["3 pengguna", "10 komoditas", "Akses API", "Support prioritas"],
    },
    {
        "id": "enterprise",
        "name": "Enterprise",
        "price_idr": 750_000,
        "interval": "month",
        "interval_count": 1,
        "features": ["Pengguna tak terbatas", "Komoditas tak terbatas", "Support VIP"],
    },
]

SUBSCRIPTION_STATUSES = {"active", "past_due", "canceled", "incomplete"}
PAYMENT_STATUSES = {"pending", "succeeded", "failed", "refunded"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat()


def _connect(database: str | Path) -> sqlite3.Connection:
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def initialize_billing(database: str | Path) -> None:
    """Create billing tables and seed the default plan catalogue."""
    with _connect(database) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS subscription_plans (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                price_idr INTEGER NOT NULL,
                interval TEXT NOT NULL CHECK (interval IN ('month', 'year')),
                interval_count INTEGER NOT NULL DEFAULT 1,
                features_json TEXT NOT NULL DEFAULT '[]',
                is_active INTEGER NOT NULL DEFAULT 1
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS subscriptions (
                email TEXT PRIMARY KEY COLLATE NOCASE,
                plan_id TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('active', 'past_due', 'canceled', 'incomplete')),
                current_period_start TEXT NOT NULL,
                current_period_end TEXT NOT NULL,
                cancel_at_period_end INTEGER NOT NULL DEFAULT 0,
                provider TEXT NOT NULL DEFAULT 'manual',
                provider_subscription_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL COLLATE NOCASE,
                amount_idr INTEGER NOT NULL,
                currency TEXT NOT NULL DEFAULT 'IDR',
                status TEXT NOT NULL CHECK (status IN ('pending', 'succeeded', 'failed', 'refunded')),
                provider TEXT NOT NULL DEFAULT 'manual',
                provider_transaction_id TEXT UNIQUE,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )"""
        )
        for plan in PLANS:
            connection.execute(
                """INSERT OR IGNORE INTO subscription_plans
                   (id, name, description, price_idr, interval, interval_count, features_json, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
                (
                    plan["id"], plan["name"], plan.get("description", ""),
                    plan["price_idr"], plan["interval"], plan["interval_count"],
                    json.dumps(plan["features"], ensure_ascii=False),
                ),
            )


def list_plans(database: str | Path, active_only: bool = True) -> list[dict]:
    initialize_billing(database)
    with _connect(database) as connection:
        query = "SELECT * FROM subscription_plans"
        if active_only:
            query += " WHERE is_active = 1"
        rows = connection.execute(query + " ORDER BY price_idr").fetchall()
    plans = []
    for row in rows:
        plan = dict(row)
        plan["features"] = json.loads(plan.pop("features_json") or "[]")
        plans.append(plan)
    return plans


def get_plan(database: str | Path, plan_id: str) -> dict | None:
    for plan in list_plans(database):
        if plan["id"] == plan_id:
            return plan
    return None


def _add_months(start: datetime, months: int) -> datetime:
    year = start.year + (start.month - 1 + months) // 12
    month = (start.month - 1 + months) % 12 + 1
    day = min(start.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                          31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return start.replace(year=year, month=month, day=day, hour=23, minute=59, second=59, microsecond=0)


def _period_end(plan: dict, start: datetime | None = None) -> datetime:
    start = start or _now()
    months = plan["interval_count"] if plan.get("interval") == "month" else plan["interval_count"] * 12
    return _add_months(start, months)


def get_subscription(database: str | Path, email: str) -> dict | None:
    normalized = email.strip().casefold()
    if not normalized:
        return None
    initialize_billing(database)
    with _connect(database) as connection:
        row = connection.execute(
            "SELECT * FROM subscriptions WHERE email = ? COLLATE NOCASE", (normalized,)
        ).fetchone()
    return dict(row) if row else None


def set_subscription(
    database: str | Path,
    email: str,
    plan_id: str,
    status: str = "active",
    period_start: str | None = None,
    period_end: str | None = None,
    provider: str = "manual",
    provider_subscription_id: str | None = None,
    cancel_at_period_end: int = 0,
) -> dict:
    """Create/update a paid subscription and sync access in the accounts table."""
    plan = get_plan(database, plan_id)
    if plan is None:
        raise ValueError(f"Paket tidak dikenal: {plan_id}")
    if status not in SUBSCRIPTION_STATUSES:
        raise ValueError(f"Status langganan tidak valid: {status}")
    normalized = email.strip().casefold()
    if not normalized or "@" not in normalized:
        raise ValueError("Alamat email tidak valid.")

    now = _now()
    start_dt = datetime.fromisoformat(period_start) if period_start else now
    end_dt = datetime.fromisoformat(period_end) if period_end else _period_end(plan, start_dt)

    with _connect(database) as connection:
        connection.execute(
            """INSERT INTO subscriptions
               (email, plan_id, status, current_period_start, current_period_end,
                cancel_at_period_end, provider, provider_subscription_id, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(email) DO UPDATE SET
                 plan_id = excluded.plan_id,
                 status = excluded.status,
                 current_period_start = excluded.current_period_start,
                 current_period_end = excluded.current_period_end,
                 cancel_at_period_end = excluded.cancel_at_period_end,
                 provider = excluded.provider,
                 provider_subscription_id = excluded.provider_subscription_id,
                 updated_at = excluded.updated_at""",
            (
                normalized, plan_id, status, _iso(start_dt), _iso(end_dt),
                cancel_at_period_end, provider, provider_subscription_id,
                _iso(now), _iso(now),
            ),
        )
        # Sync the existing accounts store so the Streamlit gate sees active
        # access. The accounts table may not exist yet (billing can run before
        # any login), so tolerate its absence.
        try:
            connection.execute(
                """UPDATE accounts SET status = 'active', updated_at = ?
                   WHERE email = ? COLLATE NOCASE AND access_until < ?""",
                (_iso(now), normalized, _iso(end_dt)),
            )
            connection.execute(
                """UPDATE accounts SET access_until = ?, status = 'active', updated_at = ?
                   WHERE email = ? COLLATE NOCASE AND access_until < ?""",
                (_iso(end_dt), _iso(now), normalized, _iso(end_dt)),
            )
        except sqlite3.OperationalError:
            pass  # accounts table not present yet; nothing to sync.
        row = connection.execute(
            "SELECT * FROM subscriptions WHERE email = ? COLLATE NOCASE", (normalized,)
        ).fetchone()
    return dict(row)


def record_payment(
    database: str | Path,
    email: str,
    amount_idr: int,
    status: str,
    provider: str = "manual",
    provider_transaction_id: str | None = None,
) -> int:
    if status not in PAYMENT_STATUSES:
        raise ValueError(f"Status pembayaran tidak valid: {status}")
    if amount_idr <= 0:
        raise ValueError("Jumlah pembayaran harus positif.")
    now = _now()
    with _connect(database) as connection:
        cursor = connection.execute(
            """INSERT INTO payments
               (email, amount_idr, currency, status, provider, provider_transaction_id, created_at, completed_at)
               VALUES (?, ?, 'IDR', ?, ?, ?, ?, ?)""",
            (
                email.strip().casefold(), int(amount_idr), status, provider,
                provider_transaction_id, _iso(now),
                _iso(now) if status in ("succeeded", "failed", "refunded") else None,
            ),
        )
        return int(cursor.lastrowid)


def check_account_access(database: str | Path, account: dict) -> dict:
    """Return an updated account record with paid-subscription awareness.

    The UI gate reads ``account["access_allowed"]`` and ``account["status"]``,
    so this keeps the Streamlit layout unchanged while letting a paid
    subscription extend access beyond the trial.
    """
    result = dict(account)
    subscription = get_subscription(database, account.get("email", ""))
    now = _now()

    trial_end = None
    try:
        trial_end = datetime.fromisoformat(account.get("access_until", ""))
    except (TypeError, ValueError):
        trial_end = None

    effective_end = trial_end
    if subscription and subscription["status"] == "active":
        try:
            sub_end = datetime.fromisoformat(subscription["current_period_end"])
        except (TypeError, ValueError):
            sub_end = None
        effective_end = max((end for end in (effective_end, sub_end) if end), default=None)

    if effective_end is None:
        result["status"] = "expired"
        result["days_remaining"] = 0
        result["access_allowed"] = False
        return result

    seconds_left = (effective_end - now).total_seconds()
    result["days_remaining"] = max(0, int((seconds_left + 86399) // 86400))
    base_status = account.get("status", "trial")
    result["status"] = "active" if subscription and subscription["status"] == "active" else base_status
    result["access_allowed"] = result["status"] in {"trial", "active"} and seconds_left >= 0
    if subscription:
        result["plan_id"] = subscription["plan_id"]
        result["subscription_status"] = subscription["status"]
    return result


def list_incomplete_subscriptions(database: str | Path) -> list[dict]:
    """Subscriptions waiting for manual (BCA) payment confirmation."""
    initialize_billing(database)
    with _connect(database) as connection:
        rows = connection.execute(
            """SELECT s.email, s.plan_id, s.created_at,
                      p.name AS plan_name, p.price_idr,
                      a.display_name
               FROM subscriptions s
               JOIN subscription_plans p ON p.id = s.plan_id
               LEFT JOIN accounts a ON LOWER(a.email) = LOWER(s.email)
               WHERE s.status = 'incomplete'
               ORDER BY s.created_at ASC"""
        ).fetchall()
    return [dict(row) for row in rows]


def list_all_subscriptions(database: str | Path) -> list[dict]:
    """All subscription rows for admin overview."""
    initialize_billing(database)
    with _connect(database) as connection:
        rows = connection.execute(
            """SELECT s.email, s.plan_id, s.status, s.current_period_end,
                      s.created_at, s.updated_at,
                      p.name AS plan_name, p.price_idr,
                      a.display_name
               FROM subscriptions s
               JOIN subscription_plans p ON p.id = s.plan_id
               LEFT JOIN accounts a ON LOWER(a.email) = LOWER(s.email)
               ORDER BY s.updated_at DESC"""
        ).fetchall()
    return [dict(row) for row in rows]


def list_pending_payments(database: str | Path) -> list[dict]:
    """Payment rows with status 'pending' (audit trail)."""
    initialize_billing(database)
    with _connect(database) as connection:
        rows = connection.execute(
            """SELECT * FROM payments WHERE status = 'pending' ORDER BY created_at ASC"""
        ).fetchall()
    return [dict(row) for row in rows]


def confirm_manual_payment(
    database: str | Path,
    email: str,
    plan_id: str,
    amount_idr: int | None = None,
    transaction_ref: str | None = None,
) -> dict:
    """Approve a manual BCA transfer: activate the subscription and record payment."""
    plan = get_plan(database, plan_id)
    if plan is None:
        raise ValueError(f"Paket tidak dikenal: {plan_id}")
    subscription = set_subscription(database, email, plan_id, status="active")
    record_payment(
        database, email,
        int(amount_idr) if amount_idr else int(plan["price_idr"]),
        "succeeded", provider="manual", provider_transaction_id=transaction_ref,
    )
    return subscription


# ---------------------------------------------------------------------------
# Stripe webhook handling (stdlib-only, no `stripe` package required).
# ---------------------------------------------------------------------------

def verify_stripe_signature(payload: bytes, sig_header: str, secret: str) -> bool:
    """Verify a Stripe webhook signature (HMAC-SHA256 over ``t.<payload>``)."""
    if not sig_header or not secret:
        return False
    parts = {}
    for item in sig_header.split(","):
        key, _, value = item.partition("=")
        if key:
            parts[key] = value
    timestamp = parts.get("t")
    expected = parts.get("v1")
    if not timestamp or not expected:
        return False
    signed_payload = f"{timestamp}.{payload.decode('utf-8')}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, expected)


def parse_stripe_event(payload: bytes, sig_header: str, secret: str) -> dict:
    """Verify and parse a Stripe event. Raises ValueError on bad signature."""
    if not verify_stripe_signature(payload, sig_header, secret):
        raise ValueError("Tanda tangan webhook Stripe tidak valid.")
    return json.loads(payload.decode("utf-8"))


def _price_to_plan_id(database: str | Path, price_id: str) -> str | None:
    """Map a Stripe price id to an internal plan id via env, else first match."""
    mapping = os.environ.get("STRIPE_PRICE_PLAN_MAP", "")
    if mapping:
        try:
            table = json.loads(mapping)
            return table.get(price_id)
        except json.JSONDecodeError:
            return None
    del database
    return None


def handle_stripe_event(database: str | Path, event: dict) -> str:
    """Dispatch a verified Stripe event to the matching handler."""
    event_type = event.get("type", "")
    data = event.get("data", {}).get("object", {})
    email = data.get("customer_email") or data.get("email")
    if not email and data.get("customer"):
        # In a real deployment a customer lookup would need the Stripe API.
        email = None

    if event_type in {"customer.subscription.created", "customer.subscription.updated"}:
        if not email:
            return "ignored"
        plan_id = _price_to_plan_id(database, data.get("items", {}).get("data", [{}])[0].get("price", ""))
        if not plan_id:
            return "ignored_no_plan_map"
        set_subscription(
            database, email, plan_id,
            status=data.get("status", "active"),
            period_start=data.get("current_period_start"),
            period_end=data.get("current_period_end"),
            provider="stripe",
            provider_subscription_id=data.get("id"),
            cancel_at_period_end=int(bool(data.get("cancel_at_period_end", False))),
        )
        return "subscription_synced"

    if event_type == "invoice.payment_succeeded":
        if email:
            record_payment(
                database, email,
                int(data.get("amount_paid", 0)) // 100,  # cents -> rupiah minor unit
                "succeeded", provider="stripe",
                provider_transaction_id=data.get("payment_intent"),
            )
        return "payment_recorded"

    if event_type == "invoice.payment_failed":
        if email:
            record_payment(
                database, email,
                int(data.get("amount_due", 0)) // 100,
                "failed", provider="stripe",
                provider_transaction_id=data.get("payment_intent"),
            )
        return "payment_failed_recorded"

    if event_type == "customer.subscription.deleted":
        if email:
            set_subscription(database, email, "starter", status="canceled",
                             provider="stripe", provider_subscription_id=data.get("id"))
        return "subscription_canceled"

    return "unhandled"


def handle_webhook(database: str | Path, payload: bytes, sig_header: str, secret: str) -> str:
    """Full pipeline: verify + parse + dispatch. Raises ValueError on bad signature."""
    event = parse_stripe_event(payload, sig_header, secret)
    return handle_stripe_event(database, event)
