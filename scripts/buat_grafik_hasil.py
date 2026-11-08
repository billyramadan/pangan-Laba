"""Generate ringkasan-grafik hasil model untuk slide bimbingan.

Input : reports/tabel_evaluasi_skripsi.csv (detail per komoditas)
Output : reports/grafik/*.png
Cara jalan : .\.venv\Scripts\python.exe scripts\buat_grafik_hasil.py
"""

from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "reports" / "tabel_evaluasi_skripsi.csv"
OUT = ROOT / "reports" / "grafik"
OUT.mkdir(parents=True, exist_ok=True)

C = {
    "ink": "#2D2722", "muted": "#746C64", "primary": "#C64D2C",
    "spice": "#E9A33B", "brown": "#8B6B4A", "green": "#31826E",
}
plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 10,
    "axes.edgecolor": "#EADFD3", "axes.labelcolor": C["ink"],
    "xtick.color": C["muted"], "ytick.color": C["muted"],
    "axes.titlecolor": C["ink"], "figure.facecolor": "white",
    "axes.facecolor": "white", "savefig.facecolor": "white",
})

df = pd.read_csv(IN)


def _label(row):
    return f"{row['model']}\n{row['fitur']}"


# ---- 1. Ringkasan per konfigurasi (mean & median) ----
summary = df.groupby(["model", "fitur"], as_index=False).agg(
    mean_MAE=("MAE_Rp_per_kg", "mean"),
    mean_MAPE=("MAPE_persen", "mean"),
    median_MAE=("MAE_Rp_per_kg", "median"),
    median_MAPE=("MAPE_persen", "median"),
)
summary["label"] = summary.apply(_label, axis=1)

fig, ax = plt.subplots(figsize=(8.5, 4.6))
x = np.arange(len(summary))
w = 0.38
b1 = ax.bar(x - w / 2, summary["median_MAE"], w, color=C["primary"], label="Median MAE (Rp/kg)")
b2 = ax.bar(x + w / 2, summary["mean_MAE"], w, color=C["spice"], label="Rata-rata MAE (Rp/kg)")
for bars in (b1, b2):
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 30,
                f"{bar.get_height():,.0f}", ha="center", va="bottom", fontsize=8, color=C["ink"])
ax.set_xticks(x); ax.set_xticklabels(summary["label"], fontsize=9)
ax.set_ylabel("MAE (Rp/kg)")
ax.set_title("MAE per Konfigurasi Model")
ax.legend(frameon=False)
ax.grid(axis="y", color="#EFE6D8", lw=0.8)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(OUT / "ringkasan_MAE.png", dpi=200); plt.close()

fig, ax = plt.subplots(figsize=(8.5, 4.6))
x = np.arange(len(summary))
b1 = ax.bar(x - w / 2, summary["median_MAPE"], w, color=C["primary"], label="Median MAPE (%)")
b2 = ax.bar(x + w / 2, summary["mean_MAPE"], w, color=C["spice"], label="Rata-rata MAPE (%)")
for bars in (b1, b2):
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.06,
                f"{bar.get_height():.2f}", ha="center", va="bottom", fontsize=8, color=C["ink"])
ax.set_xticks(x); ax.set_xticklabels(summary["label"], fontsize=9)
ax.set_ylabel("MAPE (%)")
ax.set_title("MAPE per Konfigurasi Model")
ax.legend(frameon=False)
ax.grid(axis="y", color="#EFE6D8", lw=0.8)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(OUT / "ringkasan_MAPE.png", dpi=200); plt.close()

# ---- 2. GRU harga saja vs LSTM harga saja per komoditas ----
g = df[(df["model"] == "GRU") & (df["fitur"].str.startswith("harga saja"))]
l = df[(df["model"] == "LSTM") & (df["fitur"].str.startswith("harga saja"))]
g = g.sort_values("MAPE_persen")
m = g.set_index("komoditas")["MAPE_persen"]
mm = l.set_index("komoditas").loc[m.index, "MAPE_persen"]

fig, ax = plt.subplots(figsize=(9, 5.4))
y = np.arange(len(m))
ax.barh(y + 0.18, m.values, 0.36, color=C["primary"], label="GRU (harga saja)")
ax.barh(y - 0.18, mm.values, 0.36, color=C["brown"], label="LSTM (harga saja)")
for yi, val in zip(y, m.values):
    ax.text(val + 0.08, yi + 0.18, f"{val:.2f}", va="center", fontsize=8, color=C["ink"])
ax.set_yticks(y); ax.set_yticklabels(m.index, fontsize=9)
ax.set_xlabel("MAPE (%)")
ax.set_title("MAPE per Komoditas — GRU vs LSTM (harga saja)")
ax.legend(frameon=False, loc="lower right")
ax.grid(axis="x", color="#EFE6D8", lw=0.8)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(OUT / "per_komoditas_MAPE.png", dpi=200); plt.close()

print("Grafik tersimpan di:", OUT)
for p in sorted(OUT.glob("*.png")):
    print(" -", p.name)
