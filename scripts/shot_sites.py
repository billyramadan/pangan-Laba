# -*- coding: utf-8 -*-
"""Screenshot homepage tiap kompetitor + landing PanganLaba untuk slide perbandingan."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path("temp/shots"); OUT.mkdir(parents=True, exist_ok=True)

SITES = [
    ("panganlaba",   "file:///c:/pangan/index.html"),
    ("raciklaba",    "https://raciklaba.id"),
    ("pihps_bi",     "https://www.bi.go.id/hargapangan"),
    ("qasir",        "https://qasir.id"),
    ("majoo",        "https://majoo.id"),
    ("tanihub",      "https://www.tanihub.com"),
    ("olsera",       "https://www.olsera.com"),
    ("xtrachef",     "https://www.xtrachef.com"),
    ("reciprofity",  "https://www.costguard.com"),
    ("afresh",       "https://www.afresh.com"),
    ("dtn",          "https://www.dtn.com"),
    ("tridge",       "https://www.tridge.com"),
]

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

ok, fail = [], []
with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 900},
                              user_agent=UA, ignore_https_errors=True, locale="id-ID")
    for name, url in SITES:
        page = ctx.new_page()
        try:
            page.goto(url, timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            page.screenshot(path=str(OUT / f"{name}.png"))
            ok.append(name)
            print("OK ", name)
        except Exception as e:
            fail.append((name, str(e)[:80]))
            print("ERR", name, str(e)[:80])
        finally:
            page.close()
    browser.close()

print("ok:", ok)
print("fail:", fail)
sys.exit(0 if ok else 1)
