"""Server Python stdlib untuk menampilkan hasil model PanganLaba di browser.

Tanpa Streamlit — cukup Python standar. Data dari reports/*.csv.

Cara jalan:
    .\.venv\Scripts\python.exe server.py
Buka: http://127.0.0.1:8000
"""

from __future__ import annotations

import csv
import html
import io
import json
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"

HOST = "127.0.0.1"
PORT = 8000

SUMMARY_CSV = REPORTS / "model_comparison_summary.csv"
DETAIL_CSV = REPORTS / "tabel_evaluasi_skripsi.csv"
FORECAST_CSV = REPORTS / "forecasts.csv"


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fmt_money(value) -> str:
    try:
        return f"Rp{float(value):,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return str(value or "-")


def render_summary_table(rows: list[dict]) -> str:
    if not rows:
        return "<p>Data ringkasan belum tersedia.</p>"
    head = "<tr><th>Model</th><th>Fitur</th><th>Komoditas</th><th>Median MAE</th><th>Median RMSE</th><th>Median MAPE</th></tr>"
    body = []
    for r in rows:
        body.append(
            f"<tr><td>{html.escape(r.get('model',''))}</td>"
            f"<td>{html.escape(r.get('fitur',''))}</td>"
            f"<td>{r.get('jumlah_komoditas','')}</td>"
            f"<td>{fmt_money(r.get('median_MAE'))}</td>"
            f"<td>{fmt_money(r.get('median_RMSE'))}</td>"
            f"<td>{r.get('median_MAPE','')}%</td></tr>"
        )
    return f"<table class='tbl'>{head}{''.join(body)}</table>"


def render_detail_table(rows: list[dict]) -> str:
    if not rows:
        return "<p>Data detail belum tersedia.</p>"
    head = ("<tr><th>Komoditas</th><th>Model</th><th>Fitur</th><th>MAE</th>"
            "<th>RMSE</th><th>MAPE</th><th>Jendela</th><th>Horizon</th><th>Epoch</th></tr>")
    body = []
    for r in rows:
        body.append(
            f"<tr><td>{html.escape(r.get('komoditas',''))}</td>"
            f"<td>{html.escape(r.get('model',''))}</td>"
            f"<td>{html.escape(r.get('fitur',''))}</td>"
            f"<td>{fmt_money(r.get('MAE_Rp_per_kg'))}</td>"
            f"<td>{fmt_money(r.get('RMSE_Rp_per_kg'))}</td>"
            f"<td>{r.get('MAPE_persen','')}%</td>"
            f"<td>{r.get('jendela_hari','')} hr</td>"
            f"<td>{r.get('horizon_hari','')} hr</td>"
            f"<td>{r.get('epoch_aktual','')}</td></tr>"
        )
    return f"<table class='tbl'>{head}{''.join(body)}</table>"


def render_page() -> bytes:
    summary = read_csv(SUMMARY_CSV)
    detail = read_csv(DETAIL_CSV)
    html_doc = f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PanganLaba — Hasil Model</title>
<style>
:root {{ --ink:#2D2722; --muted:#746C64; --primary:#C64D2C; --line:#EADFD3; --surface:#FFFDFA; --canvas:#FFF9F1; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:sans-serif; background:var(--canvas); color:var(--ink); }}
.wrap {{ max-width:1100px; margin:0 auto; padding:2rem 1.25rem 4rem; }}
h1 {{ font-size:1.7rem; letter-spacing:-.02em; margin:0 0 .25rem; }}
.sub {{ color:var(--muted); margin:0 0 1.5rem; }}
h2 {{ font-size:1.15rem; margin:1.8rem 0 .6rem; color:var(--primary); }}
.tbl {{ width:100%; border-collapse:collapse; background:var(--surface); border:1px solid var(--line); border-radius:10px; overflow:hidden; font-size:.9rem; }}
.tbl th {{ background:#A33D22; color:#fff; text-align:left; padding:.55rem .7rem; font-weight:700; }}
.tbl td {{ padding:.5rem .7rem; border-bottom:1px solid var(--line); }}
.tbl tr:nth-child(even) td {{ background:#F7EFE4; }}
.note {{ color:var(--muted); font-size:.85rem; margin-top:1.5rem; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>PanganLaba — Hasil Model</h1>
  <p class="sub">Ringkasan evaluasi LSTM vs GRU (13 komoditas) · data PIHPS Depok</p>

  <h2>1. Grafik</h2>
  <img src="/chart/mae" alt="MAE per konfigurasi" style="max-width:100%;border:1px solid var(--line);border-radius:10px;">
  <br><br>
  <img src="/chart/mape_commodity" alt="MAPE per komoditas" style="max-width:100%;border:1px solid var(--line);border-radius:10px;">

  <h2>2. Ringkasan per konfigurasi (median)</h2>
  {render_summary_table(summary)}

  <h2>3. Detail per komoditas</h2>
  {render_detail_table(detail)}

  <p class="note">Sumber: reports/model_comparison_summary.csv · reports/tabel_evaluasi_skripsi.csv · dihasilkan server.py</p>
</div>
</body>
</html>"""
    return html_doc.encode("utf-8")


C = {
    "ink": "#2D2722", "muted": "#746C64", "primary": "#C64D2C",
    "spice": "#E9A33B", "brown": "#8B6B4A",
}
plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 10,
    "axes.edgecolor": "#EADFD3", "axes.labelcolor": C["ink"],
    "xtick.color": C["muted"], "ytick.color": C["muted"],
    "axes.titlecolor": C["ink"], "axes.facecolor": "white",
})


def _chart_summary_mae(df: pd.DataFrame) -> bytes:
    s = df.groupby(["model", "fitur"], as_index=False).agg(
        mean=("MAE_Rp_per_kg", "mean"), median=("MAE_Rp_per_kg", "median"))
    s["label"] = s["model"] + "\n" + s["fitur"]
    import numpy as np
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    x = np.arange(len(s)); w = 0.38
    b1 = ax.bar(x - w/2, s["median"], w, color=C["primary"], label="Median MAE (Rp/kg)")
    b2 = ax.bar(x + w/2, s["mean"], w, color=C["spice"], label="Rata-rata MAE (Rp/kg)")
    for bars in (b1, b2):
        for bar in bars:
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+30,
                    f"{bar.get_height():,.0f}", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(s["label"], fontsize=9)
    ax.set_ylabel("MAE (Rp/kg)"); ax.set_title("MAE per Konfigurasi Model")
    ax.legend(frameon=False); ax.grid(axis="y", color="#EFE6D8", lw=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=150); plt.close(fig)
    return buf.getvalue()


def _chart_per_commodity(df: pd.DataFrame) -> bytes:
    g = df[(df["model"] == "GRU") & (df["fitur"].str.startswith("harga saja"))].sort_values("MAPE_persen")
    l = df[(df["model"] == "LSTM") & (df["fitur"].str.startswith("harga saja"))]
    m = g.set_index("komoditas")["MAPE_persen"]
    mm = l.set_index("komoditas").loc[m.index, "MAPE_persen"]
    import numpy as np
    fig, ax = plt.subplots(figsize=(9, 5.4))
    y = np.arange(len(m))
    ax.barh(y + 0.18, m.values, 0.36, color=C["primary"], label="GRU (harga saja)")
    ax.barh(y - 0.18, mm.values, 0.36, color=C["brown"], label="LSTM (harga saja)")
    for yi, val in zip(y, m.values):
        ax.text(val + 0.08, yi + 0.18, f"{val:.2f}", va="center", fontsize=8)
    ax.set_yticks(y); ax.set_yticklabels(m.index, fontsize=9)
    ax.set_xlabel("MAPE (%)"); ax.set_title("MAPE per Komoditas — GRU vs LSTM (harga saja)")
    ax.legend(frameon=False, loc="lower right"); ax.grid(axis="x", color="#EFE6D8", lw=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=150); plt.close(fig)
    return buf.getvalue()


CHART_CACHE = {}


def chart_png(name: str) -> bytes | None:
    if name in CHART_CACHE:
        return CHART_CACHE[name]
    df = pd.read_csv(DETAIL_CSV)
    if name == "mae":
        data = _chart_summary_mae(df)
    elif name == "mape_commodity":
        data = _chart_per_commodity(df)
    else:
        return None
    CHART_CACHE[name] = data
    return data


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        path = urllib.parse.urlparse(self.path).path
        if path.startswith("/chart/"):
            name = path.split("/chart/")[1]
            data = chart_png(name)
            if data is None:
                self.send_error(404, "Chart not found")
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path not in {"/", "/index.html"}:
            self.send_error(404, "Not Found")
            return
        body = render_page()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print("[server]", fmt % args)


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"PanganLaba server berjalan: http://{HOST}:{PORT}")
    print("Tekan Ctrl+C untuk berhenti.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nMenghentikan server...")
        server.shutdown()


if __name__ == "__main__":
    main()
