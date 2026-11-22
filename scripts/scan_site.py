"""Scanner framework: crawl PanganLaba UI, collect console/page/image/network errors + exercise core flows."""
import json, sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
findings = {"console_errors": [], "page_errors": [], "failed_requests": [],
            "broken_images": [], "http_status": {}, "access_flow": [], "notes": []}

def rec(lst, x): lst.append(x)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    page.on("console", lambda m: rec(findings["console_errors"], m.text)
            if m.type == "error" and "favicon" not in m.text.lower() else None)
    page.on("pageerror", lambda e: rec(findings["page_errors"], str(e)))
    page.on("requestfailed", lambda r: rec(findings["failed_requests"],
            f"{r.method} {r.url} :: {r.failure}") if r.resource_type not in ("fetch",) or "api" in r.url else None)

    page.goto(BASE, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(1500)

    # broken images
    for img in page.locator("img[src]").all():
        src = img.get_attribute("src") or ""
        if not src or src.startswith("data:"):
            continue
        resp = page.request.get(BASE + ("/" if not src.startswith("/") else "") + src.lstrip("/"))
        if not resp.ok:
            rec(findings["broken_images"], f"{src} -> HTTP {resp.status}")

    # fetch endpoints probed by JS on load
    page.screenshot(path="/tmp/landing.png", full_page=True)
    body = page.content()
    findings["notes"].append(f"landing title={page.title()!r}")
    findings["notes"].append(f"local_preview_flow: {page.locator('#accountNotice').count()} accountNotice els")

    # anchor link audit
    anchors = []
    for a in page.locator("a[href^='#']").all():
        href = a.get_attribute("href")
        if href and href != "#" and not page.locator(href).count():
            anchors.append(href)
    if anchors:
        findings["notes"].append("dead_anchors=" + json.dumps(sorted(set(anchors)), ensure_ascii=False))

    # JSON api checks
    for path in ["/api/bootstrap", "/api/forecasts/current?commodity=beras&model=GRU&features=harga+saja&restock_days=7"]:
        r = page.request.get(BASE + path)
        ct = r.headers.get("content-type", "")
        findings["http_status"][path] = r.status
        if "json" not in ct:
            findings["notes"].append(f"{path} returned non-JSON content-type {ct!r} status {r.status}")
        else:
            try:
                j = r.json()
            except Exception as e:
                findings["notes"].append(f"{path} JSON parse failed: {e}")
            else:
                if "error" in j:
                    findings["notes"].append(f"{path} returned error: {j['error']}")

    # local preview flow (no login) — check enterDemo path & core widgets
    try:
        page.evaluate("startSignup()")
        page.wait_for_timeout(600)
        findings["access_flow"].append(f"startSignup(anon) -> url={page.url}, toast={page.locator('#toast').inner_text()!r}")
    except Exception as e:
        findings["access_flow"].append(f"startSignup threw: {e}")

    browser.close()

print("=== SCAN RESULTS ===")
print(json.dumps(findings, indent=2, ensure_ascii=False, default=str))
