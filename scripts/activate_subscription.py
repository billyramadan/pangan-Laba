"""Admin-side manual activation after payment has been confirmed separately."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pangan_forecast.accounts import activate_subscription  # noqa: E402
from pangan_forecast.billing import get_subscription, set_subscription  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Aktifkan/lanjutkan akses langganan pengguna.")
    parser.add_argument("email", help="Email terverifikasi pengguna")
    parser.add_argument("--days", type=int, default=30, help="Durasi akses tambahan (default: 30 hari)")
    args = parser.parse_args()
    db = ROOT / "data" / "app_users.sqlite3"
    account = activate_subscription(db, args.email, args.days)
    # Sinkronkan baris subscriptions (yang tadi tercatat 'incomplete') jadi 'active',
    # supaya check_account_access menganggap langganan aktif dan membuka akses.
    try:
        sub = get_subscription(db, args.email)
        if sub is not None:
            set_subscription(db, args.email, sub["plan_id"], status="active")
    except Exception as exc:
        print(f"Peringatan: gagal sinkronkan status langganan: {exc}")
    print(f"Langganan aktif untuk {account['email']} sampai {account['access_until']} (UTC).")


if __name__ == "__main__":
    main()
