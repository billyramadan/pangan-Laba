"""Gambar diagram arsitektur pipeline prediksi harga (LSTM/GRU) — versi premium.

Output: reports/figures/ml_pipeline_diagram.png dan .svg
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Ellipse, Rectangle

# ===== Brand palette (selaras UI PanganLaba) =====
INK = "#2A211C"
MUTED = "#6A5B52"
FAINT = "#8A7A70"
PRIMARY = "#E4572E"
PRIMARY_DARK = "#C13E1D"
SPICE = "#E9A33B"
GREEN = "#355F4E"
TEAL = "#2E6E6E"
LINE = "#E6DBCC"
SURFACE = "#FFFDFA"
CANVAS = "#FAF5EE"
SHADOW = "#000000"

FONT = "Segoe UI"
FONT_BOLD = "Segoe UI Semibold"

OUT = Path(__file__).resolve().parents[1] / "reports" / "figures"


def _box(ax, x, y, w, h, *, fill=SURFACE, edge=LINE, lw=1.6,
         rounding=1.4, shadow=True, dashed=False, alpha=1.0, z=2):
    if shadow:
        ax.add_patch(FancyBboxPatch(
            (x + 0.35, y - 0.5), w, h,
            boxstyle=f"round,pad=0.02,rounding_size={rounding}",
            linewidth=0, facecolor=SHADOW, alpha=0.07, zorder=z - 1))
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.02,rounding_size={rounding}",
        linewidth=lw, edgecolor=edge, facecolor=fill, alpha=alpha,
        linestyle="--" if dashed else "-", zorder=z))


def _arrow(ax, x1, y1, x2, y2, *, color=MUTED, lw=2.0, rad=0.12,
           style="-|>", ms=22, z=3):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2),
        connectionstyle=f"arc3,rad={rad}",
        arrowstyle=style, mutation_scale=ms,
        linewidth=lw, color=color, zorder=z))


def _txt(ax, x, y, s, *, size=10.5, color=INK, weight="normal",
         va="center", ha="center", spacing=1.25, z=4):
    ax.text(x, y, s, fontsize=size, color=color,
            fontfamily=FONT, fontweight=weight,
            va=va, ha=ha, linespacing=spacing, zorder=z)


def _chip(ax, x, y, s, *, fill=TEAL, textcolor="#FFFFFF", size=8.8,
          h=4.2, weight="normal", z=4):
    w = 0.55 * len(s) * size / 10 + 2.6
    _box(ax, x - w / 2, y - h / 2, w, h, fill=fill, edge=fill,
         rounding=2.0, shadow=False, z=z - 1)
    _txt(ax, x, y, s, size=size, color=textcolor, weight=weight, z=z)


# ================= Ikon mini (vektor) =================

def _icon_rupiah(ax, cx, cy, r=4.4, color=PRIMARY_DARK):
    ax.add_patch(Circle((cx, cy), r, facecolor="#FFF8F2",
                        edgecolor=color, linewidth=1.6, zorder=4))
    _txt(ax, cx, cy, "Rp", size=4.6, color=color, weight="bold")


def _icon_sun(ax, cx, cy, r=2.9, color=SPICE):
    ax.add_patch(Circle((cx, cy), r, facecolor="#FFF3DC",
                        edgecolor=color, linewidth=1.6, zorder=4))
    for a in range(0, 360, 45):
        import math
        ra = math.radians(a)
        x1 = cx + (r + 1.1) * math.cos(ra)
        y1 = cy + (r + 1.1) * math.sin(ra)
        x2 = cx + (r + 2.8) * math.cos(ra)
        y2 = cy + (r + 2.8) * math.sin(ra)
        ax.plot([x1, x2], [y1, y2], color=color, linewidth=1.4, zorder=4)


def _icon_calendar(ax, cx, cy, w=8.6, h=7.4, color=GREEN):
    x0, y0 = cx - w / 2, cy - h / 2
    _box(ax, x0, y0, w, h, fill="#F1F7F2", edge=color, lw=1.4,
         rounding=1.2, shadow=False, z=3)
    ax.add_patch(Rectangle((x0, y0 + h - 2.1), w, 2.1,
                           facecolor=color, zorder=4))
    # cincin gantungan
    for dx in (-2.0, 2.0):
        ax.add_patch(Rectangle((x0 + w / 2 + dx - 0.35, y0 + h - 3.2),
                               0.7, 1.4, facecolor=color, zorder=5))
    # garis grid
    for i in range(1, 4):
        yy = y0 + h - 2.1 - i * 1.35
        ax.plot([x0 + 0.7, x0 + w - 0.7], [yy, yy],
                color=color, lw=0.8, zorder=4, alpha=0.75)
    for i in range(1, 3):
        xx = x0 + i * w / 3
        ax.plot([xx, xx], [y0 + 0.7, y0 + h - 2.1],
                color=color, lw=0.8, zorder=4, alpha=0.75)


def _icon_arrow_bars(ax, cx, cy, w=12, h=4.6, color=PRIMARY_DARK):
    x0 = cx - w / 2
    ys = [cy + h / 2 - 1.15, cy, cy - h / 2 + 1.05]
    hs = [1.0, 1.9, 2.9]
    for i, (yy, hh) in enumerate(zip(ys, hs)):
        ax.add_patch(Rectangle((x0 + i * (w / 3 + 0.7), yy - hh / 2),
                                w / 3 - 0.6, hh, facecolor=color,
                                alpha=0.35 + 0.3 * i, zorder=4))
    ax.annotate("", xy=(x0 + w + 0.5, cy - h / 2),
                xytext=(x0 + w + 0.5, cy + h / 2),
                arrowprops=dict(arrowstyle="-|>", lw=1.8, color=INK),
                zorder=4)


def draw():
    fig, ax = plt.subplots(figsize=(13.4, 11.0), dpi=200)
    fig.patch.set_facecolor(CANVAS)
    ax.set_facecolor(CANVAS)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 106)
    ax.axis("off")

    # ===== Judul =====
    _txt(ax, 50, 103.6, "Arsitektur Pipeline Prediksi Harga Pangan",
         size=19, weight="bold", color=INK)
    _txt(ax, 50, 100.4,
         "LSTM & GRU · Fitur eksternal · Dukungan perencanaan belanja bahan baku UMKM kuliner — Kota Depok",
         size=10.4, color=MUTED)

    # ===== Baris 1: Sumber data =====
    src_top, src_h = 89.5, 8.6
    srcs = [
        ("Harga PIHPS", "Kota Depok · Rp/kg", _icon_rupiah,
         ("harga harian per komoditas + pasar",)),
        ("Cuaca ERA5", "Open-Meteo · historis", _icon_sun,
         ("curah hujan · suhu · angin · radiasi",)),
        ("Kalender Indonesia", "libur & cuti", _icon_calendar,
         ("weekend · libur nasional · Idulfitri",)),
    ]
    xs = [2.5, 36.5, 70.5]
    w = 27
    for (title, sub, icon, lines), x0 in zip(srcs, xs):
        _box(ax, x0, src_top - src_h, w, src_h + 6.4, fill=SURFACE,
             edge=LINE, lw=1.6, rounding=1.6)
        icon(ax, x0 + 4.6, src_top - src_h + 4.0)
        _txt(ax, x0 + 10.4, src_top - src_h + 5.6, title,
             size=12.2, weight="bold", color=INK, ha="left")
        _txt(ax, x0 + 10.4, src_top - src_h + 2.9, sub,
             size=8.8, color=FAINT, ha="left")
        for i, ln in enumerate(lines):
            _txt(ax, x0 + w / 2, src_top - src_h - 2.1 - i * 2.4, ln,
                 size=9.0, color=MUTED)

    # ===== Baris 2: Preprocessing & fitur =====
    pp_y, pp_h = 69.5, 9.6
    _box(ax, 6, pp_y, 88, pp_h, fill=PRIMARY, edge=PRIMARY_DARK,
         lw=2.0, rounding=1.8)
    _txt(ax, 50, pp_y + pp_h - 2.5, "Penggabungan & Fitur Eksternal",
         size=13.5, weight="bold", color="#FFFFFF")
    chips = [
        ("validasi & pembersihan data", "#FFFFFF", PRIMARY_DARK, 8.4),
        ("fitur harga: lag 1/7 · mean 7/30", "#FFFFFF", PRIMARY_DARK, 8.4),
        ("eksternal: cuaca · kalender · siklus hari/bulan", "#FFFFFF", PRIMARY_DARK, 8.4),
    ]
    cw_sum = 0
    for s, tc, bg, sz in chips:
        cw_sum += 0.55 * len(s) * sz / 10 + 2.6
    gap = 2.2
    total_w = cw_sum + gap * (len(chips) - 1)
    cx0 = 50 - total_w / 2
    for s, tc, bg, sz in chips:
        _chip(ax, cx0 + (0.55 * len(s) * sz / 10 + 2.6) / 2,
              pp_y + 2.6, s, fill=bg, textcolor=tc, size=sz)
        cx0 += 0.55 * len(s) * sz / 10 + 2.6 + gap

    # ===== Baris 3: Windowing =====
    wn_y, wn_h = 57.5, 7.6
    _box(ax, 26, wn_y - wn_h, 48, wn_h, fill=SURFACE, edge=SPICE,
         lw=2.0, rounding=1.8)
    _txt(ax, 50, wn_y - wn_h / 2 + 0.9, "Jendela bergulir 30 hari  →  horizon 7 hari",
         size=11.6, weight="bold", color=INK)
    _icon_arrow_bars(ax, 50, wn_y - wn_h / 2 - 2.6, w=16, h=2.2, color=SPICE)

    # ===== Baris 4: Zone model =====
    zone_y, zone_h = 32.5, 18.6
    _box(ax, 3, zone_y, 94, zone_h, fill="#F3ECE1", edge="#DCC8B2",
         lw=1.3, rounding=1.8, dashed=True, alpha=0.55, shadow=False)
    _txt(ax, 50, zone_y + zone_h - 1.6, "MODEL (LSTM / GRU)",
         size=10.2, weight="bold", color=PRIMARY_DARK, spacing=1.0)

    m_top = zone_y + zone_h - 6.2
    m_h = 11.0
    m_w = 34
    m_left = 18
    m_right = 48
    # satu kotak model utama (alternatif LSTM/GRU)
    _box(ax, m_left, m_top - m_h, m_w, m_h, fill=SURFACE, edge=GREEN,
         lw=2.2, rounding=1.8)
    _txt(ax, m_left + m_w / 2, m_top - 1.4, "Model (LSTM / GRU)",
         size=13.5, weight="bold", color=GREEN)
    # label alternatif LSTM & GRU di atas kotak
    _txt(ax, m_left + m_w / 2 - 12, m_top - m_h - 2.6, "LSTM",
         size=11.5, weight="bold", color=TEAL)
    _txt(ax, m_left + m_w / 2 + 12, m_top - m_h - 2.6, "GRU",
         size=11.5, weight="bold", color=TEAL)
    _txt(ax, m_left + m_w / 2, m_top - m_h - 2.6, " ↔ ",
         size=12, weight="bold", color=INK)
    # input yang sama untuk kedua model
    _chip(ax, m_left + m_w / 2, m_top - 5.4, "harga + eksternal",
          fill=PRIMARY, size=9.2)
    _box(ax, m_left + m_w / 2 - 36, m_top - m_h - 6.0, 72, 4.2,
         fill="#EEE6DA", edge=LINE, lw=1.0, rounding=2.0, shadow=False)
    _txt(ax, m_left + m_w / 2, m_top - m_h - 4.0,
         "Input sama untuk kedua model (harga + eksternal)",
         size=9.2, color=MUTED, weight="normal")

    # ===== Baris 5: Output =====
    o_y, o_h = 17.5, 9.6
    _box(ax, 11, o_y, 78, o_h, fill="#F4E2CF", edge=PRIMARY,
         lw=2.0, rounding=1.8)
    _txt(ax, 50, o_y + o_h - 2.4, "Keluaran untuk Perencanaan Belanja",
         size=13.2, weight="bold", color=PRIMARY_DARK)
    out_chips = [
        ("prediksi harga 7 hari", "#FFFFFF", PRIMARY),
        ("rekomendasi beli/tunda ±5%", "#FFFFFF", GREEN),
        ("simulasi belanja rutin vs strategi", "#FFFFFF", TEAL),
    ]
    ocw = 0
    for s, tc, bg in out_chips:
        ocw += 0.52 * len(s) * 9.0 / 10 + 2.6
    ogap = 2.4
    ocx = 50 - (ocw + ogap * 2) / 2
    for s, tc, bg in out_chips:
        _chip(ax, ocx + (0.52 * len(s) * 9.0 / 10 + 2.6) / 2,
              o_y + 2.7, s, fill=bg, textcolor=tc, size=9.0)
        ocx += 0.52 * len(s) * 9.0 / 10 + 2.6 + ogap

    # ===== Baris footer: Evaluasi =====
    ft_y, ft_h = 7.5, 5.2
    _box(ax, 6, ft_y, 88, ft_h, fill="#EEE6DA", edge=LINE,
         lw=1.4, rounding=1.8, shadow=False)
    _txt(ax, 50, ft_y + ft_h / 2,
         "Evaluasi: split kronologis 80% latih / 20% uji · MAE · RMSE · MAPE · model final dilatih ulang pada seluruh riwayat (refit full-history)",
         size=9.2, color=MUTED)

    # ===== Panah utama =====
    # sumber -> preprocessing
    for x0 in (16, 50, 84):
        _arrow(ax, x0, src_top - src_h - 1.4, x0, pp_y + pp_h + 1.2,
               color=PRIMARY_DARK, rad=0.0)
    # preprocessing -> windowing
    _arrow(ax, 50, pp_y, 50, wn_y - wn_h - 0.6, color=PRIMARY_DARK, rad=0.0)
    # windowing -> model (split)
    _arrow(ax, 43, wn_y - wn_h - 0.6, 37, m_top, color=GREEN, rad=-0.18)
    _arrow(ax, 57, wn_y - wn_h - 0.6, 63, m_top, color=GREEN, rad=0.18)
    # model -> output
    _arrow(ax, 37, m_top - m_h - 0.6, 42, o_y + o_h + 1.0, color=PRIMARY, rad=0.14)
    _arrow(ax, 63, m_top - m_h - 0.6, 58, o_y + o_h + 1.0, color=PRIMARY, rad=-0.14)

    # ===== Legenda =====
    lx, ly = 5.5, 3.4
    items = [("Data / Input", TEAL), ("Transformasi", PRIMARY),
             ("Model", GREEN), ("Keluaran", SPICE)]
    x = lx
    for label, c in items:
        ax.add_patch(Circle((x + 1.0, ly), 0.85, facecolor=c, zorder=4))
        _txt(ax, x + 2.6, ly, label, size=9.2, color=MUTED, ha="left")
        x += 0.55 * len(label) * 9.2 / 10 + 6.2
    _txt(ax, 86, ly, "PanganLaba · skripsi", size=8.6, color=FAINT)

    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "ml_pipeline_diagram.png", dpi=200,
                bbox_inches="tight", facecolor=CANVAS)
    fig.savefig(OUT / "ml_pipeline_diagram.svg", bbox_inches="tight",
                facecolor=CANVAS)
    plt.close(fig)
    print(OUT / "ml_pipeline_diagram.png")


if __name__ == "__main__":
    draw()
