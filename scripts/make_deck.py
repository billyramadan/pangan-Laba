# -*- coding: utf-8 -*-
"""Generate PanganLaba pitch deck (.pptx). 7 slide, 16:9, brand palette from frontend."""
from pptx import Presentation
from pptx.util import Inches as In, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

INK    = RGBColor(0x2A, 0x21, 0x1C)
MUTED  = RGBColor(0x5E, 0x51, 0x49)
PRIM   = RGBColor(0xE4, 0x57, 0x2E)
PDARK  = RGBColor(0xC1, 0x3E, 0x1D)
SPICE  = RGBColor(0xE9, 0xA3, 0x3B)
SURF   = RGBColor(0xFF, 0xFD, 0xFA)
CANVAS = RGBColor(0xFA, 0xF5, 0xEE)
GREEN  = RGBColor(0x35, 0x5F, 0x4E)
LINEC  = RGBColor(0xE6, 0xDB, 0xCC)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)

F = "Calibri"

prs = Presentation()
prs.slide_width  = In(13.333)
prs.slide_height = In(7.5)
BLANK = prs.slide_layouts[6]
W, H = 13.333, 7.5
PAD = 0.65
CONTENT_W = W - 2*PAD

def slide():
    s = prs.slides.add_slide(BLANK)
    rect(s, 0, 0, W, H, fill=SURF)
    return s

def rect(s, x, y, w, h, fill=None, line=None, lw=1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=None):
    sp = s.shapes.add_shape(shape, In(x), In(y), In(w), In(h))
    if fill is None: sp.fill.background()
    else: sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None: sp.line.fill.background()
    else: sp.line.color.rgb = line; sp.line.width = Pt(lw)
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try: sp.adjustments[0] = radius
        except Exception: pass
    sp.shadow.inherit = False
    return sp

def txt(s, x, y, w, h, items, anchor=MSO_ANCHOR.TOP, wrap=True):
    tb = s.shapes.add_textbox(In(x), In(y), In(w), In(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = it.get("align", PP_ALIGN.LEFT)
        if it.get("space_before") is not None: p.space_before = Pt(it["space_before"])
        if it.get("space_after") is not None: p.space_after = Pt(it["space_after"])
        if it.get("line") is not None: p.line_spacing = it["line"]
        r = p.add_run(); r.text = it.get("text", "")
        r.font.name = it.get("font", F)
        r.font.size = Pt(it.get("size", 14))
        r.font.bold = it.get("bold", False)
        r.font.italic = it.get("italic", False)
        r.font.color.rgb = it.get("color", INK)
    return tb

def header(s, kicker, title, color=PRIM):
    y = 0.42
    rect(s, PAD, y, 0.14, 0.72, fill=color)
    txt(s, PAD+0.32, y-0.03, CONTENT_W, 0.3,
        [dict(text=kicker.upper(), size=12, bold=True, color=PDARK)])
    txt(s, PAD+0.32, y+0.24, CONTENT_W, 0.7,
        [dict(text=title, size=30, bold=True, color=INK)])

def footer(s, n):
    txt(s, 0.55, H-0.42, W-1.1, 0.3,
        [dict(text="PanganLaba — Tugas Akhir", size=10, color=MUTED)])
    txt(s, W-1.15, H-0.5, 0.8, 0.3,
        [dict(text=str(n), size=11, bold=True, color=MUTED, align=PP_ALIGN.RIGHT)])

def bullets(s, x, y, w, h, items, size=13.5, color=MUTED, gap=8, bold=False, line=1.15, marker="▸  "):
    paras = [dict(text=marker+b, size=size, bold=bold, color=color, line=line, space_after=gap) for b in items]
    txt(s, x, y, w, h, paras)

def card(s, x, y, w, h, title, body, tcolor=INK, fill=SURF, line=LINEC, tsize=15, bsize=12.5):
    rect(s, x, y, w, h, fill=fill, line=line, lw=1.1, radius=0.06)
    txt(s, x+0.22, y+0.1, w-0.44, h-0.2,
        [dict(text=title, size=tsize, bold=True, color=tcolor, space_after=4),
         dict(text=body, size=bsize, color=MUTED, line=1.12)],
        anchor=MSO_ANCHOR.MIDDLE)

# ============ 1. PERMASALAHAN ============
s = slide()
header(s, "Slide 1 — Masalah", "Permasalahan yang Terjadi")
# quote
rect(s, PAD, 1.6, CONTENT_W, 1.45, fill=CANVAS, line=LINEC, lw=1.2, radius=0.08)
txt(s, PAD+0.4, 1.6, CONTENT_W-0.8, 1.45, [
    dict(text="“Kemarin belanja ayam Rp48.000/kg, hari ini Rp50.000/kg. Naik Rp2.000 — cuma 4% — dalam satu malam.”",
         size=16, bold=True, color=INK, line=1.15),
    dict(text="Modal pas-pasan jadi tidak cukup: beli lebih sedikit, atau pakai cadangan untuk kebutuhan lain.",
         size=12.5, color=MUTED, space_before=6, line=1.12)],
    anchor=MSO_ANCHOR.MIDDLE)
# four mini cards
stats = [
    ("Kecil × Volume", "Ayam +Rp2.000/kg; beli 10 kg/hari → +Rp600.000/bulan di luar rencana.", PRIM),
    ("Margin tipis", "Margin UMKM 5–15%; kenaikan bahan 5–8% hapus seluruh laba seminggu.", SPICE),
    ("Lonjakan terpusat", "Idulfitri / cuaca ekstrem: harga bisa melonjak 12–30% dalam hitungan hari.", GREEN),
    ("Akumulasi", "Kecil yang berulang tiap minggu jadi pergeseran besar dalam sebulan.", PDARK),
]
x = PAD
for t, b, c in stats:
    card(s, x, 3.3, 2.93, 2.35, t, b, tcolor=c)
    x += 3.05
rect(s, PAD, 5.95, CONTENT_W, 0.85, fill=PRIM, radius=0.1)
txt(s, PAD+0.4, 5.95, CONTENT_W-0.8, 0.85,
    [dict(text="Masalah besarnya: volatilitas biaya bahan baku menggerus margin tipis ribuan UMKM kuliner Depok — bukan sekadar “harga naik berapa”.",
         size=15, bold=True, color=WHITE, line=1.15)],
    anchor=MSO_ANCHOR.MIDDLE)
footer(s, 1)

# ============ 2. SOLUSI ============
s = slide()
header(s, "Slide 2 — Solusi", "Solusi yang Ditawarkan: PanganLaba")
pill = [
    ("1", "Prediksi Harga 7 Hari", "Model LSTM & GRU memperkirakan 13 komoditas pangan strategis — tahu kapan aman beli atau tunda.", PRIM),
    ("2", "Kalkulator Modal & Laba", "Modal per porsi, harga jual aman, margin, titik impas — dihitung otomatis setiap hari.", SPICE),
    ("3", "Langganan Trial→Bayar", "7 hari gratis, lalu paket berbayar — sekaligus uji kelayakan komersial produk.", GREEN),
]
x = PAD
for num, t, b, c in pill:
    rect(s, x, 1.6, 3.85, 2.55, fill=SURF, line=LINEC, lw=1.2, radius=0.08)
    rect(s, x+0.3, 1.9, 0.85, 0.85, fill=c, radius=0.5)
    txt(s, x+0.3, 1.9, 0.85, 0.85, [dict(text=num, size=22, bold=True, color=WHITE, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
    txt(s, x+0.3, 2.95, 3.25, 0.4, [dict(text=t, size=16, bold=True, color=INK)])
    txt(s, x+0.3, 3.4, 3.25, 0.7, [dict(text=b, size=12.5, color=MUTED, line=1.12)])
    x += 4.05
# technical strip
rect(s, PAD, 4.45, 6.0, 2.2, fill=CANVAS, line=LINEC, lw=1.2, radius=0.08)
txt(s, PAD+0.35, 4.65, 5.3, 0.4, [dict(text="DATA & ARSITEKTUR", size=12.5, bold=True, color=GREEN)])
bullets(s, PAD+0.35, 5.05, 5.35, 1.5, [
    "PIHPS 13 komoditas Depok 2020–2026 + cuaca ERA5 + kalender Indonesia",
    "Jendela 30 hari → prediksi 7 hari; LSTM/GRU 48 unit, seed 42",
    "Saran beli/tunda otomatis pada ambang perubahan ±5%",
], size=12.5, gap=7)
rect(s, 6.95, 4.45, 5.75, 2.2, fill=CANVAS, line=LINEC, lw=1.2, radius=0.08)
txt(s, 7.3, 4.65, 5.1, 0.4, [dict(text="EVALUASI JUJUR", size=12.5, bold=True, color=PRIM)])
bullets(s, 7.3, 5.05, 5.15, 1.5, [
    "Metrik MAE, RMSE, MAPE pada data uji 20% akhir",
    "GRU harga-saja terbaik: MAPE ≈ 3,5%",
    "Fitur eksternal belum terbukti menolong pada data ini — diakui, bukan disembunyikan",
], size=12.5, gap=7)
footer(s, 2)

# ============ 3. FITUR UTAMA ============
s = slide()
header(s, "Slide 3 — Produk", "Fitur Utama PanganLaba")
mods = [
    ("Ringkasan Usaha", "Harga PIHPS terakhir, rerata prediksi 7 hari, saran beli/tunda.", PRIM),
    ("Kalkulator Laba Menu", "Modal per porsi, omzet, laba bersih, margin, titik impas.", PRIM),
    ("Simulasi Belanja", "Bandingkan belanja rutin vs strategis (tunda) per siklus.", PRIM),
    ("Tanya PanganLaba", "Jawaban bahasa sehari-hari dari data aplikasi.", SPICE),
    ("Riwayat & Unduh", "Rekap laba-rugi dan ekspor CSV.", SPICE),
    ("Otentikasi & Paket", "Login Google, status trial/aktif/berakhir, batas komoditas per paket.", SPICE),
]
pos = [(0.65,1.75),(4.74,1.75),(8.83,1.75),(0.65,4.15),(4.74,4.15),(8.83,4.15)]
for (x,y),(t,b,c) in zip(pos, mods):
    card(s, x, y, 3.85, 2.1, t, b, tcolor=c)
rect(s, PAD, 6.45, CONTENT_W, 0.6, fill=LINEC, radius=0.12)
txt(s, PAD+0.35, 6.45, CONTENT_W-0.7, 0.6,
    [dict(text="Akses via browser HP — tanpa instalasi, cocok perangkat entry-level UMKM.", size=13.5, bold=True, color=INK)],
    anchor=MSO_ANCHOR.MIDDLE)
footer(s, 3)

# ============ 4. TARGET & PASAR ============
s = slide()
header(s, "Slide 4 — Pasar", "Target Pengguna & Ukuran Pasar")
rect(s, PAD, 1.6, 6.0, 2.45, fill=CANVAS, line=LINEC, lw=1.2, radius=0.08)
txt(s, PAD+0.35, 1.8, 5.3, 0.4, [dict(text="SASARAN (MASUK SEGMEN)", size=12.5, bold=True, color=GREEN)])
bullets(s, PAD+0.35, 2.2, 5.35, 1.7, [
    "UMKM kuliner yang belanja bahan baku setiap hari",
    "Harga bahan = bagian besar dari biaya produksi",
    "Bahan volatile: cabai, bawang, telur, ayam, minyak",
], size=13, gap=7)
rect(s, 6.95, 1.6, 5.75, 2.45, fill=SURF, line=LINEC, lw=1.2, radius=0.08)
txt(s, 7.3, 1.8, 5.1, 0.4, [dict(text="DI LUAR SEGMEN", size=12.5, bold=True, color=MUTED)])
bullets(s, 7.3, 2.2, 5.15, 1.7, [
    "UMKM non-kuliner (baju, jasa): bahan tidak naik-turun harian",
    "Kebutuhan prediksi & kalkulator margin jauh lebih rendah",
    "Dipisah sengaja agar fokus jelas",
], size=13, gap=7)
# TAM SAM SOM
tam = [("TAM", "Seluruh UMKM kuliner Indonesia yang belanja bahan harian", PRIM),
       ("SAM", "UMKM kuliner Jabodetabek yang bergantung komoditas volatile", SPICE),
       ("SOM", "Target awal: Kota Depok — penetrasi sebagian UMKM kuliner", GREEN)]
x = PAD
for t, b, c in tam:
    rect(s, x, 4.35, 3.85, 1.85, fill=SURF, line=LINEC, lw=1.2, radius=0.08)
    rect(s, x, 4.35, 3.85, 0.55, fill=c, radius=0.06)
    txt(s, x+0.25, 4.35, 3.35, 0.55, [dict(text=t, size=15, bold=True, color=WHITE)], anchor=MSO_ANCHOR.MIDDLE)
    txt(s, x+0.25, 5.05, 3.35, 1.05, [dict(text=b, size=12.5, color=MUTED, line=1.15)])
    x += 4.05
txt(s, PAD, 6.4, CONTENT_W, 0.4,
    [dict(text="Alasan peluang nyata: harga volatile, margin tipis 5–15%, mayoritas UMKM belum menghitung margin. Proyeksi berbasis asumsi; perlu validasi survei kesediaan bayar.",
         size=12.5, italic=True, color=PDARK, line=1.15)])
footer(s, 4)

# ============ 5. KOMPETITOR ============
s = slide()
header(s, "Slide 5 — Persaingan", "Analisis Kompetitor")
rect(s, PAD, 1.6, 6.0, 4.6, fill=CANVAS, line=LINEC, lw=1.2, radius=0.08)
txt(s, PAD+0.35, 1.85, 5.3, 0.4, [dict(text="YANG ADA SEKARANG (parsial)", size=13, bold=True, color=MUTED)])
alt = [
    ("Excel / catatan manual", "Tidak menarik data otomatis; tidak menghitung margin."),
    ("Intel harga pemerintah (PIHPS, Bapanas)", "Data tersedia, tanpa alat keputusan."),
    ("Riset akademik", "Berhenti di angka akurasi, bukan produk."),
]
cy = 2.4
for t, b in alt:
    txt(s, PAD+0.35, cy, 5.4, 0.35, [dict(text="▸  "+t, size=14, bold=True, color=INK)])
    txt(s, PAD+0.35, cy+0.34, 5.4, 0.7, [dict(text=b, size=12, color=MUTED, line=1.12)])
    cy += 1.25
rect(s, 6.95, 1.6, 5.75, 4.6, fill=PRIM, radius=0.08)
txt(s, 7.3, 1.85, 5.1, 0.4, [dict(text="PEMBEDA PANGANLABA", size=13, bold=True, color=WHITE)])
bullets(s, 7.3, 2.4, 5.1, 3.4, [
    "Prediksi harga + kalkulator margin dalam satu tempat",
    "Pipeline data otomatis, diperbarui harian",
    "Akses browser HP — tanpa instalasi, perangkat entry-level",
    "Saran beli/tunda, bukan sekadar angka",
    "Kontekstual Depok — data PIHPS lokal",
], size=13, color=WHITE, bold=True, gap=10)
rect(s, PAD, 6.45, CONTENT_W, 0.6, fill=LINEC, radius=0.12)
txt(s, PAD+0.35, 6.45, CONTENT_W-0.7, 0.6,
    [dict(text="Posisi: satu-satunya yang mengubah prediksi harga jadi keputusan belanja & harga jual yang aman.",
         size=13.5, bold=True, color=INK)],
    anchor=MSO_ANCHOR.MIDDLE)
footer(s, 5)

# ============ 6. KEUNGGULAN ============
s = slide()
header(s, "Slide 6 — Keunggulan", "Keunggulan & Pembeda PanganLaba")
adv = [
    ("Satu tempat", "Prediksi + kalkulator + riwayat dalam satu aplikasi.", PRIM),
    ("Otomatis", "Data PIHPS, cuaca & kalender diperbarui harian.", SPICE),
    ("Mudah diakses", "Browser HP, tanpa instalasi, perangkat entry-level.", GREEN),
    ("Rendah hambatan", "Margin dihitung otomatis — mayoritas UMKM belum melakukannya.", PDARK),
    ("Berbasis riset", "Model teruji pada data lokal Depok, bukan klaim kosong.", GREEN),
    ("Jujur", "Tidak mengklaim akurasi palsu; nilai dari rutinitas menghitung.", PRIM),
]
pos = [(0.65,1.75),(4.74,1.75),(8.83,1.75),(0.65,4.1),(4.74,4.1),(8.83,4.1)]
for (x,y),(t,b,c) in zip(pos, adv):
    card(s, x, y, 3.85, 2.1, t, b, tcolor=c)
rect(s, PAD, 6.45, CONTENT_W, 0.6, fill=SPICE, radius=0.12)
txt(s, PAD+0.35, 6.45, CONTENT_W-0.7, 0.6,
    [dict(text="Pembeda utama: bukan sekadar angka prediksi, tapi instrumen perlindungan margin yang dipakai setiap hari.",
         size=14, bold=True, color=INK)],
    anchor=MSO_ANCHOR.MIDDLE)
footer(s, 6)

# ============ 7. MODEL BISNIS ============
s = slide()
header(s, "Slide 7 — Bisnis", "Model Bisnis & Sumber Pendapatan")
cols = [
    ("ALUR MONETISASI", GREEN, [
        "Trial 7 hari gratis sejak login pertama",
        "Paket berbayar: Starter / Pro / Enterprise",
        "Beda paket = jumlah komoditas dianalisis",
        "Paywall muncul setelah trial berakhir",
    ]),
    ("PAKET (KONSEP)", PRIM, [
        "Starter — 3 komoditas, prediksi 7 hari, kalkulator dasar",
        "Pro — 13 komoditas + simulasi belanja + riwayat",
        "Enterprise — multi-outlet, ekspor CSV, dukungan prioritas",
        "Harga ditetapkan setelah uji kesediaan bayar",
    ]),
    ("UJI KELAYAKAN & KPI", PDARK, [
        "Pembayaran manual (transfer BCA) + verifikasi panel admin",
        "Konversi trial → berbayar",
        "Churn bulanan & skor manfaat uji coba UMKM",
        "Waktu penyelesaian tugas kalkulator & dashboard",
    ]),
]
x = PAD
for t, c, items in cols:
    rect(s, x, 1.6, 3.85, 4.35, fill=CANVAS, line=LINEC, lw=1.2, radius=0.08)
    rect(s, x, 1.6, 3.85, 0.55, fill=c, radius=0.06)
    txt(s, x+0.25, 1.6, 3.35, 0.55, [dict(text=t, size=13, bold=True, color=WHITE)], anchor=MSO_ANCHOR.MIDDLE)
    bullets(s, x+0.25, 2.35, 3.35, 3.4, items, size=12.5, gap=10)
    x += 4.05
rect(s, PAD, 6.2, CONTENT_W, 0.75, fill=SPICE, radius=0.1)
txt(s, PAD+0.4, 6.2, CONTENT_W-0.8, 0.75,
    [dict(text="Sumber pendapatan: langganan bulanan paket berbayar. Uji coba UMKM mengukur kesediaan bayar sebelum skala.",
         size=14, bold=True, color=INK)],
    anchor=MSO_ANCHOR.MIDDLE)
footer(s, 7)

prs.save(r"c:\pangan\reports\PanganLaba_Presentasi.pptx")
print("OK saved. slides =", len(prs.slides._sldIdLst))
