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
        "features": ["1 pengguna", "Komoditas tak terbatas", "Dashboard dasar"],
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
                plan_id TEXT,
                amount_idr INTEGER NOT NULL,
                currency TEXT NOT NULL DEFAULT 'IDR',
                status TEXT NOT NULL CHECK (status IN ('pending', 'succeeded', 'failed', 'refunded')),
                provider TEXT NOT NULL DEFAULT 'manual',
                provider_transaction_id TEXT UNIQUE,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )"""
        )
        payment_columns = {row["name"] for row in connection.execute("PRAGMA table_info(payments)")}
        if "plan_id" not in payment_columns:
            connection.execute("ALTER TABLE payments ADD COLUMN plan_id TEXT")
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
        # Only a confirmed active subscription may grant account access.
        # Pending/incomplete payment requests must never extend a trial or
        # paid entitlement. The accounts table may not exist before login.
        if status == "active":
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
    plan_id: str | None = None,
) -> int:
    if status not in PAYMENT_STATUSES:
        raise ValueError(f"Status pembayaran tidak valid: {status}")
    if amount_idr <= 0:
        raise ValueError("Jumlah pembayaran harus positif.")
    now = _now()
    with _connect(database) as connection:
        cursor = connection.execute(
            """INSERT INTO payments
               (email, plan_id, amount_idr, currency, status, provider,
                provider_transaction_id, created_at, completed_at)
               VALUES (?, ?, ?, 'IDR', ?, ?, ?, ?, ?)""",
            (
                email.strip().casefold(), plan_id, int(amount_idr), status, provider,
                provider_transaction_id, _iso(now),
                _iso(now) if status in ("succeeded", "failed", "refunded") else None,
            ),
        )
        return int(cursor.lastrowid)


def check_account_access(database: str | Path, account: dict) -> dict:
    """Return current entitlement status using trial and paid-period end dates."""
    result = dict(account)
    subscription = get_subscription(database, account.get("email", ""))
    now = _now()

    try:
        trial_end = datetime.fromisoformat(account.get("access_until", ""))
    except (TypeError, ValueError):
        trial_end = None

    sub_end = None
    if subscription:
        try:
            sub_end = datetime.fromisoformat(subscription.get("current_period_end", ""))
        except (TypeError, ValueError):
            sub_end = None

    active_subscription = bool(
        subscription
        and subscription.get("status") == "active"
        and sub_end
        and sub_end > now
    )
    effective_end = trial_end
    if active_subscription:
        effective_end = max((end for end in (trial_end, sub_end) if end), default=None)

    seconds_left = (effective_end - now).total_seconds() if effective_end else -1
    allowed = effective_end is not None and seconds_left > 0
    if not allowed:
        status = "expired"
    elif active_subscription or account.get("status") == "active":
        status = "active"
    elif trial_end and trial_end > now:
        status = "trial"
    else:
        status = account.get("status", "trial")

    result["status"] = status
    result["days_remaining"] = max(0, int((seconds_left + 86399) // 86400)) if allowed else 0
    result["access_allowed"] = allowed
    if effective_end:
        result["access_until"] = effective_end.isoformat()
    if subscription:
        result["plan_id"] = subscription.get("plan_id")
        sub_status = subscription.get("status")
        if sub_status == "active" and sub_end and sub_end <= now:
            sub_status = "expired"
        result["subscription_status"] = sub_status
    if not allowed:
        result["expired_reason"] = (
            "subscription"
            if ((subscription and subscription.get("status") == "active" and sub_end and sub_end <= now)
                or account.get("status") == "active")
            else "trial"
        )
    else:
        result.pop("expired_reason", None)
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


def list_admin_payments(database: str | Path, limit: int = 200) -> list[dict]:
    """Return recent payment records with account and current plan details."""
    initialize_billing(database)
    limit = max(1, min(500, int(limit)))
    with _connect(database) as connection:
        rows = connection.execute(
            """SELECT p.id, p.email, COALESCE(p.plan_id, s.plan_id) AS plan_id,
                      p.amount_idr, p.currency, p.status AS payment_status,
                      p.provider, p.provider_transaction_id, p.created_at, p.completed_at,
                      a.display_name, pl.name AS plan_name,
                      s.status AS subscription_status, s.current_period_end
               FROM payments p
               LEFT JOIN accounts a ON LOWER(a.email) = LOWER(p.email)
               LEFT JOIN subscriptions s ON LOWER(s.email) = LOWER(p.email)
               LEFT JOIN subscription_plans pl ON pl.id = COALESCE(p.plan_id, s.plan_id)
               ORDER BY CASE p.status WHEN 'pending' THEN 0 ELSE 1 END,
                        p.created_at DESC, p.id DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def _settle_payment(database: str | Path, payment_id: int, expected_provider: str) -> dict:
    """Atomically settle one pending payment and activate its subscription."""
    initialize_billing(database)
    now = _now()
    now_text = _iso(now)
    with _connect(database) as connection:
        connection.execute("BEGIN IMMEDIATE")
        payment = connection.execute(
            "SELECT * FROM payments WHERE id = ?", (int(payment_id),)
        ).fetchone()
        if payment is None:
            raise ValueError("Transaksi tidak ditemukan.")
        if payment["provider"] != expected_provider:
            raise ValueError("Metode transaksi tidak cocok.")
        if payment["status"] == "succeeded":
            return {"already_paid": True, "email": payment["email"],
                    "amount_idr": payment["amount_idr"]}
        if payment["status"] != "pending":
            raise ValueError("Transaksi ini tidak berstatus menunggu pembayaran.")

        subscription = connection.execute(
            "SELECT * FROM subscriptions WHERE LOWER(email) = LOWER(?)",
            (payment["email"],),
        ).fetchone()
        if subscription is None or subscription["provider"] != expected_provider:
            raise ValueError("Permintaan langganan untuk transaksi ini tidak ditemukan.")
        if subscription["status"] not in {"incomplete", "active"}:
            raise ValueError("Status langganan tidak dapat diaktifkan dari transaksi ini.")

        start = now
        if subscription["status"] == "active":
            try:
                current_end = datetime.fromisoformat(subscription["current_period_end"])
                if current_end > start:
                    start = current_end
            except (TypeError, ValueError):
                pass
        plan_id = payment["plan_id"] or subscription["plan_id"]
        plan_row = connection.execute(
            "SELECT interval, interval_count, name FROM subscription_plans WHERE id = ?",
            (plan_id,),
        ).fetchone()
        if plan_row is None:
            raise ValueError("Paket transaksi tidak ditemukan.")
        plan = {"interval": plan_row["interval"],
                "interval_count": plan_row["interval_count"]}
        end = _period_end(plan, start)
        connection.execute(
            """UPDATE subscriptions SET plan_id = ?, status = 'active', current_period_start = ?,
                      current_period_end = ?, updated_at = ? WHERE LOWER(email) = LOWER(?)""",
            (plan_id, _iso(start), _iso(end), now_text, payment["email"]),
        )
        connection.execute(
            """UPDATE payments SET status = 'succeeded', completed_at = ?
               WHERE id = ? AND status = 'pending'""",
            (now_text, int(payment_id)),
        )
        try:
            connection.execute(
                """UPDATE accounts SET status = 'active', access_until = ?, updated_at = ?
                   WHERE LOWER(email) = LOWER(?) AND access_until < ?""",
                (_iso(end), now_text, payment["email"], _iso(end)),
            )
        except sqlite3.OperationalError:
            pass
        return {"already_paid": False, "email": payment["email"],
                "amount_idr": payment["amount_idr"], "plan_name": plan_row["name"],
                "current_period_end": _iso(end)}


def confirm_manual_payment_by_id(database: str | Path, payment_id: int) -> dict:
    """Admin confirmation for one specific manual transfer request."""
    return _settle_payment(database, payment_id, "manual")


def complete_provider_payment(
    database: str | Path,
    provider: str,
    transaction_ref: str,
    amount_idr: int | None = None,
) -> dict:
    """Settle a gateway payment by its durable provider transaction reference."""
    initialize_billing(database)
    with _connect(database) as connection:
        row = connection.execute(
            """SELECT id, amount_idr FROM payments
               WHERE provider = ? AND provider_transaction_id = ?""",
            (provider, str(transaction_ref)),
        ).fetchone()
    if row is None:
        raise ValueError("Transaksi gateway tidak ditemukan.")
    if amount_idr is not None and int(amount_idr) != int(row["amount_idr"]):
        raise ValueError("Nominal pada notifikasi gateway tidak cocok dengan tagihan.")
    return _settle_payment(database, int(row["id"]), provider)

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
        plan_id=plan_id,
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
        def iso(value):
            if not value:
                return None
            if isinstance(value, (int, float)):
                return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
            return value

        set_subscription(
            database, email, plan_id,
            status=data.get("status", "active"),
            period_start=iso(data.get("current_period_start")),
            period_end=iso(data.get("current_period_end")),
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
