"""Local account entitlement store for the single-server thesis prototype.

Identity and passwords are handled by an OIDC provider through Streamlit auth;
this module stores only verified email and trial/subscription dates.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
import math
from pathlib import Path


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _connect(database: str | Path) -> sqlite3.Connection:
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def initialize_accounts(database: str | Path) -> None:
    with _connect(database) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS accounts (
                email TEXT PRIMARY KEY COLLATE NOCASE,
                display_name TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL CHECK (status IN ('trial', 'active', 'expired')),
                trial_started_at TEXT NOT NULL,
                access_until TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"""
        )


def start_or_get_account(
    database: str | Path,
    email: str,
    display_name: str = "",
    trial_days: int = 7,
) -> dict:
    """Create a first-time account with a trial or return its existing record."""
    normalized_email = email.strip().casefold()
    if not normalized_email or "@" not in normalized_email:
        raise ValueError("Penyedia login tidak memberikan alamat email yang valid.")
    if trial_days <= 0:
        raise ValueError("Lama trial harus lebih dari 0 hari.")

    now = _now()
    now_text = now.isoformat()
    trial_end = (now + timedelta(days=trial_days)).isoformat()
    initialize_accounts(database)
    with _connect(database) as connection:
        connection.execute(
            """INSERT OR IGNORE INTO accounts
               (email, display_name, status, trial_started_at, access_until, created_at, updated_at)
               VALUES (?, ?, 'trial', ?, ?, ?, ?)""",
            (normalized_email, display_name.strip(), now_text, trial_end, now_text, now_text),
        )
        connection.execute(
            "UPDATE accounts SET display_name = ?, updated_at = ? WHERE email = ? COLLATE NOCASE",
            (display_name.strip(), now_text, normalized_email),
        )
        row = connection.execute(
            "SELECT * FROM accounts WHERE email = ? COLLATE NOCASE", (normalized_email,)
        ).fetchone()
        record = dict(row)

        expiry = datetime.fromisoformat(record["access_until"])
        if record["status"] in {"trial", "active"} and expiry <= now:
            connection.execute(
                "UPDATE accounts SET status = 'expired', updated_at = ? WHERE email = ? COLLATE NOCASE",
                (now_text, normalized_email),
            )
            record["status"] = "expired"

    seconds_left = (datetime.fromisoformat(record["access_until"]) - now).total_seconds()
    record["days_remaining"] = max(0, math.ceil(seconds_left / 86400))
    record["access_allowed"] = record["status"] in {"trial", "active"} and record["days_remaining"] >= 0
    return record


def activate_subscription(
    database: str | Path,
    email: str,
    days: int = 30,
) -> dict:
    """Grant/extend access after an administrator confirms payment externally."""
    normalized_email = email.strip().casefold()
    if not normalized_email:
        raise ValueError("Email pengguna wajib diisi.")
    if days <= 0:
        raise ValueError("Lama langganan harus lebih dari 0 hari.")

    now = _now()
    now_text = now.isoformat()
    initialize_accounts(database)
    with _connect(database) as connection:
        row = connection.execute(
            "SELECT * FROM accounts WHERE email = ? COLLATE NOCASE", (normalized_email,)
        ).fetchone()
        if row is None:
            raise ValueError(f"Akun {normalized_email} belum pernah login dan belum memiliki trial.")
        current_expiry = datetime.fromisoformat(row["access_until"])
        base = current_expiry if row["status"] == "active" and current_expiry > now else now
        new_expiry = (base + timedelta(days=days)).isoformat()
        connection.execute(
            "UPDATE accounts SET status = 'active', access_until = ?, updated_at = ? WHERE email = ? COLLATE NOCASE",
            (new_expiry, now_text, normalized_email),
        )
        updated = connection.execute(
            "SELECT * FROM accounts WHERE email = ? COLLATE NOCASE", (normalized_email,)
        ).fetchone()
    result = dict(updated)
    seconds_left = (datetime.fromisoformat(result["access_until"]) - now).total_seconds()
    result["days_remaining"] = max(0, math.ceil(seconds_left / 86400))
    result["access_allowed"] = True
    return result


def delete_account(database: str | Path, email: str) -> bool:
    """Hapus akun, langganan, dan catatan pembayaran pengguna secara permanen."""
    normalized_email = email.strip().casefold()
    if not normalized_email:
        raise ValueError("Email pengguna wajib diisi.")
    initialize_accounts(database)
    with _connect(database) as connection:
        try:  # tabel billing mungkin belum ada; tolerir.
            connection.execute(
                "DELETE FROM subscriptions WHERE email = ? COLLATE NOCASE", (normalized_email,)
            )
            connection.execute(
                "DELETE FROM payments WHERE email = ? COLLATE NOCASE", (normalized_email,)
            )
        except sqlite3.OperationalError:
            pass
        connection.execute(
            "DELETE FROM accounts WHERE email = ? COLLATE NOCASE", (normalized_email,)
        )
    return True
