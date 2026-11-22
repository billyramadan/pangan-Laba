import base64, hashlib, hmac, json, time, tomllib
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8000"
C = tomllib.loads(open(".streamlit/secrets.toml", encoding="utf-8").read())
S = str(C["auth"]["cookie_secret"]); E, N = "ramadanbilly12@gmail.com", "ramadan billy"
def ck(e, n, x):
    b = base64.urlsafe_b64encode(json.dumps({"email": e, "name": n, "exp": x}, separators=(",", ":")).encode()).decode().rstrip("=")
    return b + "." + hmac.new(S.encode(), b.encode(), hashlib.sha256).hexdigest()
out = {}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    ctx.add_cookies([{"name": "pangan_session", "value": ck(E, N, int(time.time()) + 2592000), "domain": "127.0.0.1", "path": "/"}])
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: out.setdefault("perr", []).append(str(e)))
    pg.on("console", lambda m: out.setdefault("cerr", []).append(m.text) if m.type == "error" else None)
    pg.goto(BASE, wait_until="networkidle"); pg.wait_for_timeout(1200)
    try:
        pg.click("button[data-nav='profitCard']"); pg.wait_for_timeout(700)
        out["nav"] = "ok"
    except Exception as ex:
        out["nav"] = f"fail: {ex}"
    try:
        pg.wait_for_selector("#otherCost:visible", timeout=5000)
        pg.locator(".recipe-row").first.locator("input[placeholder*='Pilih / ketik']").fill("Beras")
        pg.locator(".recipe-row").first.locator("input[placeholder*='Takaran']").fill("500")
        pg.locator(".recipe-row").first.locator("input[placeholder*='Harga beli']").fill("13000")
        pg.locator("#menuName").fill("Nasi Putih")
        pg.locator("#sellingPrice").fill("12000")
        pg.locator("#portions").fill("20")
        pg.locator("#otherCost").fill("0"); pg.locator("#fixedCost").fill("0")
        if pg.locator("#saveHistory").count(): pg.locator("#saveHistory").uncheck()
        pg.evaluate("calculateProfit()"); pg.wait_for_timeout(2500)
        out["profit_status"] = pg.locator("#profitStatus").inner_text()
        out["profit_result"] = pg.locator("#profitResult").inner_text()[:500]
    except Exception as ex:
        out["profit_error"] = str(ex)[:400]
    b.close()
print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
