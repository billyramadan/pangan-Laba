"""Focused: navigate to calculator tab, run profit flow, download history CSV."""
import base64, hashlib, hmac, json, time, tomllib
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
C = tomllib.loads(open(".streamlit/secrets.toml", encoding="utf-8").read())
SECRET = str(C["auth"]["cookie_secret"])
EMAIL, NAME = "ramadanbilly12@gmail.com", "ramadan billy"

def cookie(e, n, x):
    b = base64.urlsafe_b64encode(json.dumps({"email": e, "name": n, "exp": x}, separators=(",", ":")).encode()).decode().rstrip("=")
    return b + "." + hmac.new(SECRET.encode(), b.encode(), hashlib.sha256).hexdigest()

out = {}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width":1440,"height":900})
    ctx.add_cookies([{"name":"pangan_session","value":cookie(EMAIL,NAME,int(time.time())+2592000),"domain":"127.0.0.1","path":"/"}])
    page = ctx.new_page()
    page.on("pageerror", lambda e: out.setdefault("page_errors",[]).append(str(e)))
    page.on("console", lambda m: out.setdefault("console_errors",[]).append(m.text) if m.type=="error" else None)
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_timeout(1200)

    # open calculator tab via nav button
    try:
        page.click("button[data-action='goFeature'][data-args*='profitCard']")
        page.wait_for_timeout(800)
    except Exception as ex:
        out["nav"] = f"click failed: {ex}"

    # now profit inputs should be visible
    try:
        page.wait_for_selector("#otherCost:visible", timeout=5000)
        page.locator(".recipe-row").first.locator("input[placeholder*='Pilih / ketik']").fill("Beras")
        page.locator(".recipe-row").first.locator("input[placeholder*='Takaran']").fill("500")
        page.locator(".recipe-row").first.locator("input[placeholder*='Harga beli']").fill("13000")
        page.locator("#menuName").fill("Nasi Putih")
        page.locator("#sellingPrice").fill("12000")
        page.locator("#portions").fill("20")
        page.locator("#otherCost").fill("0")
        page.locator("#fixedCost").fill("0")
        if page.locator("#saveHistory").count(): page.locator("#saveHistory").uncheck()
        page.evaluate("calculateProfit()")
        page.wait_for_timeout(2500)
        out["profit_status"] = page.locator("#profitStatus").inner_text()
        out["profit_result"] = page.locator("#profitResult").inner_text()[:500]
    except Exception as ex:
        out["profit_error"] = str(ex)[:400]

    # CSV download
    try:
        with page.expect_download(timeout=8000) as dl_info:
            page.evaluate("downloadHistory()")
        dl = dl_info.value
        out["history_csv"] = {"suggested": dl.suggested_filename}
    except Exception as ex:
        out["history_csv_error"] = str(ex)[:300]

    page.screenshot(path="/tmp/profit_tab.png")
    b.close()

print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
