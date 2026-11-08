"""Self-check for the billing module (no test framework required).

Run: python scripts/selfcheck_billing.py
"""

from __future__ import annotations

import hashlib
import hmac
import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pangan_forecast.billing import (  # noqa: E402
    check_account_access,
    get_plan,
    get_subscription,
    handle_stripe_event,
    initialize_billing,
    list_plans,
    parse_stripe_event,
    record_payment,
    set_subscription,
    verify_stripe_signature,
)

DB = Path(tempfile.gettempdir()) / "pangan_billing_selfcheck.sqlite3"
if DB.exists():
    DB.unlink()
initialize_billing(DB)

# 1. Plans seeded.
assert {p["id"] for p in list_plans(DB)} == {"starter", "pro", "enterprise"}
assert get_plan(DB, "pro")["price_idr"] == 300_000

# 2. Subscription extends access beyond trial.
now = datetime.now(timezone.utc)
trial_end = (now + timedelta(days=7)).isoformat()
account = {
    "email": "uji@pangan.local",
    "status": "trial",
    "access_until": trial_end,
    "days_remaining": 7,
    "access_allowed": True,
}
# Without a subscription, trial governs.
after = check_account_access(DB, account)
assert after["access_allowed"] is True

# Add a paid subscription ending in 30 days.
set_subscription(DB, "uji@pangan.local", "pro", period_end=(now + timedelta(days=30)).isoformat())
after = check_account_access(DB, account)
assert after["access_allowed"] is True
assert after["plan_id"] == "pro"
assert after["subscription_status"] == "active"

# 3. A past subscription does not grant access.
set_subscription(DB, "uji@pangan.local", "starter", period_start=(now - timedelta(days=40)).isoformat(),
                 period_end=(now - timedelta(days=10)).isoformat())
after = check_account_access(DB, account)
assert after["access_allowed"] is False

# 4. Payment record.
pid = record_payment(DB, "uji@pangan.local", 300_000, "succeeded", provider="manual")
assert isinstance(pid, int) and pid > 0

# 5. Stripe signature verification.
secret = "whsec_test_secret"
ts = int(now.timestamp())
payload = json.dumps({"type": "invoice.payment_succeeded"}).encode("utf-8")
digest = hmac.new(secret.encode(), f"{ts}.{payload.decode()}".encode(), hashlib.sha256).hexdigest()
good_sig = f"t={ts},v1={digest}"
assert verify_stripe_signature(payload, good_sig, secret) is True
# Wrong signature must fail.
assert verify_stripe_signature(payload, f"t={ts},v1={'0'*64}", secret) is False
try:
    parse_stripe_event(payload, f"t={ts},v1={'0'*64}", secret)
    raise AssertionError("bad signature should have raised")
except ValueError:
    pass

# 6. Stripe event dispatch happy path (with plan map).
os_env_backup = sys.modules["os"].environ.get("STRIPE_PRICE_PLAN_MAP")
sys.modules["os"].environ["STRIPE_PRICE_PLAN_MAP"] = json.dumps({"price_1": "pro"})
event = {
    "type": "customer.subscription.updated",
    "data": {"object": {
        "customer_email": "uji@pangan.local",
        "status": "active",
        "current_period_start": now.timestamp(),
        "current_period_end": (now + timedelta(days=30)).timestamp(),
        "cancel_at_period_end": False,
        "id": "sub_123",
        "items": {"data": [{"price": "price_1"}]},
    }},
}
result = handle_stripe_event(DB, event)
assert result == "subscription_synced", result
sub = get_subscription(DB, "uji@pangan.local")
assert sub["plan_id"] == "pro" and sub["provider"] == "stripe"
if os_env_backup is None:
    del sys.modules["os"].environ["STRIPE_PRICE_PLAN_MAP"]
else:
    sys.modules["os"].environ["STRIPE_PRICE_PLAN_MAP"] = os_env_backup

DB.unlink()
print("selfcheck_billing: SEMUA LULUS")
