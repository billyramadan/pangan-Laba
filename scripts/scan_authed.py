"""Authenticated scanner: inject signed session cookie for admin, exercise all dashboard flows read-only."""
import base64, hashlib, hmac, json, time, tomllib
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
SECRET = tomllib.loads(open(".streamlit/secrets.toml", encoding="utf-8").read())
COOKIE_SECRET = str(SECRET["auth"]["cookie_secret"])
EMAIL = "ramadanbilly12@gmail.com"
NAME = "ramadan billy"

def session_cookie(email, name, exp):
    payload = {"email": email, "name": name, "exp": exp}
    blob = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    sig = hmac.new(COOKIE_SECRET.encode(), blob.encode(), hashlib.sha256).hexdigest()
    return blob + "." + sig

F = {"console_errors": [], "page_errors": [], "failed_requests": [],
     "flows": {}, "http": {}, "notes": []}

def rec(l, x): l.append(x)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    ctx.add_cookies([{"name": "pangan_session", "value": session_cookie(EMAIL, NAME, int(time.time()) + 2592000),
                      "domain": "127.0.0.1", "path": "/"}])
    page = ctx.new_page()
    page.on("console", lambda m: rec(F["console_errors"], m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: rec(F["page_errors"], str(e)))
    page.on("requestfailed", lambda r: rec(F["failed_requests"], f"{r.url} :: {r.failure}") if "api" in r.url else None)

    page.goto(BASE, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2500)
    F["flows"]["landing"] = {"in_app": not page.locator("#app").evaluate("el=>el.classList.contains('hidden')"),
                              "account_badge": page.locator("#accountBadge").inner_text() if page.locator("#accountBadge").count() else None}
    page.screenshot(path="/tmp/authed_dash.png", full_page=True)

    # summary box
    try:
        page.wait_for_selector("#summaryMetrics .metric", timeout=8000)
        F["flows"]["summary"] = page.locator("#summaryMetrics").inner_text()[:200]
    except Exception as e:
        F["flows"]["summary"] = f"not rendered: {e}"

    # recipe: add a raw, fill, calculate profit (save_history=false)
    try:
        row = page.locator(".recipe-row").first
        row.locator("input[placeholder*='Pilih / ketik']").fill("Beras")
        row.locator("input[placeholder*='Takaran']").fill("500")
        row.locator("input[placeholder*='Harga beli']").fill("13000")
        page.locator("#menuName").fill("Nasi Putih")
        page.locator("#sellingPrice").fill("10000")
        page.locator("#portions").fill("10")
        page.locator("#otherCost").fill("0")
        page.locator("#fixedCost").fill("0")
        # force no save
        page.locator("#saveHistory").uncheck() if page.locator("#saveHistory").count() else None
        page.locator("#profitStatus").evaluate("el=>el.textContent=''")
        page.evaluate("calculateProfit()")
        page.wait_for_timeout(2500)
        F["flows"]["profit_status"] = page.locator("#profitStatus").inner_text()
        F["flows"]["profit_result"] = page.locator("#profitResult").inner_text()[:400] if page.locator("#profitResult").count() else "(no result)"
    except Exception as e:
        F["flows"]["profit"] = f"ERROR: {e}"

    # simulation
    try:
        page.evaluate("runSimulation()")
        page.wait_for_timeout(2000)
        F["flows"]["sim"] = page.locator("#simStatus").inner_text() + " :: " + (page.locator("#simResult").inner_text()[:200] if page.locator("#simResult").count() else "")
    except Exception as e:
        F["flows"]["sim"] = f"ERROR: {e}"

    # tanya
    try:
        page.locator("#tanyaInput").fill("prediksi harga Beras?")
        page.evaluate("askPanganLaba()")
        page.wait_for_timeout(400)
        F["flows"]["tanya"] = page.locator("#tanyaResult").inner_text()[:300] if page.locator("#tanyaResult").count() else "(no result)"
    except Exception as e:
        F["flows"]["tanya"] = f"ERROR: {e}"

    # history
    try:
        page.evaluate("loadHistory()")
        page.wait_for_timeout(1200)
        F["flows"]["history"] = page.locator("#historyTable").inner_text()[:200] if page.locator("#historyTable").count() else "(empty)"
    except Exception as e:
        F["flows"]["history"] = f"ERROR: {e}"

    # research/eval (admin)
    try:
        page.evaluate("showTab('research')")
        page.wait_for_timeout(1200)
        F["flows"]["eval_metrics"] = page.locator("#evalMetrics").inner_text()[:200] if page.locator("#evalMetrics").count() else "(none)"
        F["flows"]["eval_info"] = page.locator("#evalInfo").inner_text()[:200] if page.locator("#evalInfo").count() else "(none)"
    except Exception as e:
        F["flows"]["research"] = f"ERROR: {e}"

    # direct API reads
    for path in ["/api/evaluation", "/api/evaluation?commodity=Beras", "/api/history",
                 "/api/admin/payments", "/api/admin/pending"]:
        r = page.request.get(BASE + path)
        F["http"][path] = r.status
        if r.status != 200:
            F["notes"].append(f"{path} -> HTTP {r.status}: {r.text()[:120]}")

    # train status with bogus id (admin) to confirm 404 path
    r = page.request.get(BASE + "/api/train/status/nonexistent")
    F["http"]["/api/train/status/nonexistent"] = r.status

    browser.close()

print("=== AUTHED SCAN ===")
print(json.dumps(F, indent=2, ensure_ascii=False, default=str))
