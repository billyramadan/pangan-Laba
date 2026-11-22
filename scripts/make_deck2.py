# -*- coding: utf-8 -*-
"""PanganLaba — deck 10 slide, 16:9, premium. Palet: hijau, teal, oranye, putih."""
from pptx import Presentation
from pptx.util import Inches as In, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ---------- palette (identik dengan css/app.css website) ----------
INK     = RGBColor(0x2A, 0x21, 0x1C)   # --ink
MUTED   = RGBColor(0x5E, 0x51, 0x49)   # --muted
FAINT   = RGBColor(0x9A, 0x8E, 0x84)
GREEN   = RGBColor(0x35, 0x5F, 0x4E)   # --green
GREEN_D = RGBColor(0x27, 0x4A, 0x3C)
TEAL    = RGBColor(0x2E, 0x6E, 0x6A)   # aksen teal turunan palet
TEAL_D  = RGBColor(0x22, 0x55, 0x52)
ORANGE  = RGBColor(0xE4, 0x57, 0x2E)   # --primary
ORANGE_D= RGBColor(0xC1, 0x3E, 0x1D)   # --primary-dark
SPICE   = RGBColor(0xE9, 0xA3, 0x3B)   # --spice
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
CREAM   = RGBColor(0xFF, 0xFD, 0xFA)   # --surface
CANVAS  = RGBColor(0xFA, 0xF5, 0xEE)   # --canvas
LINE    = RGBColor(0xE6, 0xDB, 0xCC)   # --line
NAV     = RGBColor(0xF5, 0xED, 0xE2)   # --nav
GREEN_SOFT = RGBColor(0xEA, 0xF3, 0xED)
TEAL_SOFT  = RGBColor(0xE6, 0xF1, 0xF1)
ORANGE_SOFT= RGBColor(0xF8, 0xF0, 0xE5)  # --notice bg di website

F = "Segoe UI"   # fallback Inter di website
DARK_F = "Segoe UI Semibold"

prs = Presentation()
prs.slide_width  = In(13.333)
prs.slide_height = In(7.5)
BLANK = prs.slide_layouts[6]
W, H = 13.333, 7.5
PAD = 0.62
CW = W - 2*PAD

def slide():
    s = prs.slides.add_slide(BLANK)
    rect(s, 0, 0, W, H, fill=CREAM)
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
        if it.get("sb") is not None: p.space_before = Pt(it["sb"])
        if it.get("sa") is not None: p.space_after = Pt(it["sa"])
        if it.get("line") is not None: p.line_spacing = it["line"]
        r = p.add_run(); r.text = it.get("text", "")
        r.font.name = it.get("font", F)
        r.font.size = Pt(it.get("size", 14))
        r.font.bold = it.get("bold", False)
        r.font.italic = it.get("italic", False)
        r.font.color.rgb = it.get("color", INK)
    return tb

def bullets(s, x, y, w, h, items, size=13, color=MUTED, gap=9, bold=False, line=1.15, marker=None):
    paras = []
    for b in items:
        t = b if marker is None else marker + b
        paras.append(dict(text=t, size=size, bold=bold, color=color, line=line, sa=gap))
    txt(s, x, y, w, h, paras)

def header(s, kicker, title, sub=None, color=TEAL):
    y = 0.42
    rect(s, PAD, y, 0.12, 0.86, fill=color)
    txt(s, PAD+0.32, y-0.05, CW, 0.3,
        [dict(text=kicker.upper(), size=11.5, bold=True, color=ORANGE_D)])
    txt(s, PAD+0.32, y+0.22, CW, 0.62,
        [dict(text=title, size=27, bold=True, color=INK)])
    if sub:
        txt(s, PAD+0.32, y+0.92, CW, 0.36,
            [dict(text=sub, size=12.5, color=MUTED)])

def footer(s, n, source=None):
    txt(s, PAD, H-0.40, 8.6, 0.28,
        [dict(text="PanganLaba — Tugas Akhir Teknik Informatika", size=9, color=FAINT)])
    if source:
        txt(s, 6.6, H-0.40, 6.1, 0.28,
            [dict(text=source, size=8, color=FAINT, align=PP_ALIGN.RIGHT)])
    txt(s, W-0.62, H-0.48, 0.5, 0.3,
        [dict(text=str(n), size=11, bold=True, color=ORANGE, align=PP_ALIGN.RIGHT)])

def notes(s, text):
    nf = s.notes_slide.notes_text_frame
    nf.text = text

def chip(s, x, y, w, h, label, fill, color=WHITE, size=11):
    rect(s, x, y, w, h, fill=fill, radius=0.5)
    txt(s, x, y, w, h, [dict(text=label, size=size, bold=True, color=color, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)

# ============================================================
# MARKET DATA — diisi dari riset (lihat bawah)
# ============================================================
MARKET = {
    # AKTUAL — terverifikasi terbuka
    "umkm_id": "52 juta",       "umkm_id_src": "UKM s.d. 2011 · Detik/Wikipedia",
    "kuliner_id": "≈20,8 juta", "kuliner_id_src": "52 jt × 40% asumsi",
    # ESTIMASI — basis resmi belum didapat
    "umkm_depok": "≈45.000",    "depok_src": "Estimasi kerja (belum terverifikasi)",
    "populasi_depok": 2168000,  "populasi_src": "BPS Kota Depok 2025",
    # TAM / SAM / SOM
    "tam":  "≈20,8 juta",
    "sam":  "≈12,5 juta",
    "som":  "±500 pelanggan",
}

LOGO = r"frontend/assets/panganlaba_logo.png"
IMG_UMKM = r"assets/umkm_header.jpg"
SHOT_WEB = r"temp/shots/panganlaba.png"
SHOT_RACIK = r"temp/shots/raciklaba.png"

def fmt(n):
    """Format angka ribuan gaya Indonesia (1.234.567)."""
    if isinstance(n, (int, float)):
        return f"{int(n):,.0f}".replace(",", ".")
    return str(n)

# ============================================================
# SLIDE 1 — COVER
# ============================================================
s = slide()
# photo panel kanan
# panel kanan: mockup browser berisi landing page PanganLaba asli
rect(s, 6.62, 0.62, 6.6, 6.2, fill=WHITE, line=LINE, lw=1.0, radius=0.03)
rect(s, 6.62, 0.62, 6.6, 0.42, fill=NAV, shape=MSO_SHAPE.RECTANGLE)
for i, c in enumerate((RGBColor(0xE0,0x6C,0x5F), RGBColor(0xE9,0xA3,0x3B), RGBColor(0x8F,0xBF,0x8F))):
    dot = s.shapes.add_shape(MSO_SHAPE.OVAL, In(6.82+i*0.26), In(0.75), In(0.15), In(0.15))
    dot.fill.solid(); dot.fill.fore_color.rgb = c; dot.line.fill.background(); dot.shadow.inherit = False
txt(s, 7.68, 0.62, 5.0, 0.42,
    [dict(text="panganlaba — beranda (localhost)", size=9.5, color=MUTED)], anchor=MSO_ANCHOR.MIDDLE)
try:
    s.shapes.add_picture(SHOT_WEB, In(6.7), In(1.12), In(6.44), In(4.02))
except Exception:
    pass
txt(s, 6.7, 5.28, 6.44, 0.28,
    [dict(text="Tampilan asli website PanganLaba (landing page).", size=9, italic=True, color=FAINT, align=PP_ALIGN.CENTER)])
rect(s, 6.62, 5.68, 6.6, 1.1, fill=ORANGE_SOFT, line=LINE, lw=1.0, radius=0.06)
txt(s, 6.92, 5.78, 6.0, 0.9,
    [dict(text="UNTUK UMKM KULINER", size=10, bold=True, color=ORANGE_D, sa=2),
     dict(text="Belanja bahan baku lebih cerdas, margin lebih aman.", size=15, bold=True, color=INK, line=1.12)],
    anchor=MSO_ANCHOR.MIDDLE)
# logo + identitas kiri
try:
    s.shapes.add_picture(LOGO, In(0.62), In(0.55), In(1.5), In(1.0))
except Exception:
    pass
txt(s, 0.62, 1.95, 5.6, 0.8, [dict(text="PanganLaba", size=42, bold=True, color=INK)])
txt(s, 0.66, 2.7, 5.6, 0.4, [dict(text="Prediksi Harga Pangan · Perencanaan Belanja · Analisis Margin", size=13, bold=True, color=TEAL)])
# kartu judul
rect(s, 0.62, 3.35, 5.6, 2.35, fill=WHITE, line=LINE, lw=1.2, radius=0.06)
txt(s, 0.95, 3.6, 5.0, 0.32, [dict(text="JUDUL PENELITIAN", size=10.5, bold=True, color=ORANGE_D)])
txt(s, 0.95, 3.92, 5.0, 1.3,
    [dict(text="Prediksi Harga Komoditas Pangan Strategis Menggunakan LSTM dan GRU untuk Mendukung Keputusan Belanja dan Analisis Laba Menu UMKM Kuliner",
         size=14.5, bold=True, color=INK, line=1.18)])
# institusi
txt(s, 0.66, 5.95, 5.6, 0.7,
    [dict(text="Institut Sains dan Teknologi Nasional (ISTN)", size=12.5, bold=True, color=INK),
     dict(text="Teknik Informatika · Tugas Akhir · Jakarta, 2026", size=11.5, color=MUTED)])
rect(s, 0, H-0.55, W, 0.55, fill=GREEN, shape=MSO_SHAPE.RECTANGLE)
txt(s, PAD, H-0.5, 8, 0.4, [dict(text="PanganLaba", size=11, bold=True, color=WHITE)], anchor=MSO_ANCHOR.MIDDLE)
txt(s, W-6.4, H-0.5, 5.8, 0.4,
    [dict(text="LSTM · GRU · Fitur Eksternal · HPP · Analisis Menu", size=10, color=RGBColor(0xD9,0xE8,0xE0), align=PP_ALIGN.RIGHT)],
    anchor=MSO_ANCHOR.MIDDLE)
notes(s, "Salam pembuka. PanganLaba adalah platform prediksi harga pangan untuk UMKM kuliner. Judul Tugas Akhir sesuai rancangan di website: Prediksi Harga Komoditas Pangan Strategis Menggunakan LSTM dan GRU untuk Mendukung Keputusan Belanja dan Analisis Laba Menu UMKM Kuliner. Tujuan: membantu UMKM kuliner membeli bahan baku di waktu yang tepat dan menjaga margin keuntungan.")

# ============================================================
# SLIDE 2 — PROBLEM
# ============================================================
s = slide()
header(s, "Latar Belakang", "Permasalahan UMKM Kuliner", "Harga bahan baku berubah tak terduga — UMKM baru tahu saat sudah di pasar.")
# kiri: dua contoh kasus
rect(s, PAD, 1.75, 6.55, 3.15, fill=WHITE, line=LINE, lw=1.2, radius=0.06)
txt(s, PAD+0.35, 1.92, 5.9, 0.32, [dict(text="CONTOH KASUS — BAHAN HARIAN", size=11, bold=True, color=ORANGE_D)])
txt(s, PAD+0.35, 2.26, 5.9, 1.25,
    [dict(text="Ayam: Rp48.000 → Rp50.000/kg (+4%) dalam semalam.", size=14.5, bold=True, color=INK, sa=3),
     dict(text="Beli 10 kg/hari → +Rp20.000/hari → +Rp600.000/bulan di luar rencana.", size=12.5, color=MUTED, line=1.15)])
rect(s, PAD+0.35, 3.5, 5.85, 0.012, fill=LINE, shape=MSO_SHAPE.RECTANGLE)
txt(s, PAD+0.35, 3.6, 5.9, 1.2,
    [dict(text="Cabai: Rp40.000 → Rp44.800/kg (+12%).", size=14.5, bold=True, color=INK, sa=3),
     dict(text="Pakai 2 kg/hari → +Rp9.600/hari → +Rp288.000/bulan. Dua bahan ini hampir setiap hari dibutuhkan.", size=12.5, color=MUTED, line=1.15)])
rect(s, PAD, 5.1, 6.55, 1.35, fill=ORANGE_SOFT, line=LINE, lw=1.0, radius=0.08)
txt(s, PAD+0.35, 5.2, 5.9, 1.15,
    [dict(text="Inti masalah:", size=12.5, bold=True, color=ORANGE_D, sa=3),
     dict(text="kenaikan tidak bisa diperkirakan sebelumnya. Biaya produksi naik, tapi harga jual sulit dinaikkan karena takut kehilangan pelanggan — akhirnya keuntungan menyusut.", size=13, bold=True, color=INK, line=1.18)],
    anchor=MSO_ANCHOR.MIDDLE)
# kanan: 4 titik nyeri
pains = [
    ("Sulit diprediksi", "UMKM baru tahu harga terbaru saat datang ke pasar — tidak ada perkiraan awal pekan.", ORANGE),
    ("Biaya produksi naik", "Bahan baku = komponen utama biaya; kenaikan harian langsung makan margin.", GREEN),
    ("Harga jual tak mudah naik", "Naikkan harga sepi pelanggan; tahan harga, laba hilang. UMKM terjepit.", TEAL),
    ("Margin tak terhitung", "HPP manual & laba per menu tidak terpantau — keputusan jadi tebak-tebakan.", ORANGE_D),
]
y = 1.75
for t, b, c in pains:
    rect(s, 7.4, y, 5.31, 1.13, fill=WHITE, line=LINE, lw=1.0, radius=0.1)
    rect(s, 7.4, y, 0.09, 1.13, fill=c, shape=MSO_SHAPE.RECTANGLE)
    txt(s, 7.67, y+0.12, 4.9, 0.9,
        [dict(text=t, size=12.5, bold=True, color=INK, sa=1),
         dict(text=b, size=10.5, color=MUTED, line=1.1)])
    y += 1.24
footer(s, 2)
notes(s, "Masalah dekat dengan kehidupan sehari-hari UMKM kuliner: harga bahan baku sering berubah dan sulit diprediksi. Contoh ayam: Rp48.000 naik Rp50.000 per kg — kelihatan hanya Rp2.000, tapi untuk warung yang pakai 10 kg per hari menjadi Rp20.000 per hari, Rp600.000 per bulan. Contoh cabai: Rp40.000 naik Rp44.800 per kg, pemakaian 2 kg per hari menambah Rp9.600 per hari, Rp288.000 per bulan. Masalah utamanya: kenaikan seperti ini sering tidak bisa diperkirakan — UMKM baru tahu saat sudah di pasar. Dampaknya: biaya produksi naik otomatis, sementara harga jual tidak bisa sembarangan dinaikkan karena harus mempertimbangkan pelanggan dan daya beli masyarakat. Akhirnya keuntungan menyusut.")

# ============================================================
# SLIDE 3 — SOLUTION
# ============================================================
s = slide()
header(s, "Solusi", "Bagaimana PanganLaba Menjawabnya", "Tiga solusi yang menyatu menjadi satu alur keputusan harian.")
sol = [
    ("01", "Prediksi Harga 7 Hari", "Model LSTM & GRU + fitur eksternal (cuaca, kalender) memperkirakan 13 komoditas pangan strategis. Tahu kapan aman beli atau tunda.", ORANGE, GREEN_SOFT),
    ("02", "Perencanaan Pembelian", "Saran kapan & berapa banyak belanja berdasarkan prediksi dan ambang perubahan harga — menggantikan tebak-tebakan.", TEAL, TEAL_SOFT),
    ("03", "Hitung HPP & Analisis Menu", "Biaya per porsi, harga jual aman, margin, dan keuntungan tiap menu dihitung otomatis dari data harga bahan.", GREEN, GREEN_SOFT),
]
x = PAD
for num, t, b, c, bg in sol:
    rect(s, x, 1.75, 3.93, 3.55, fill=bg, line=LINE, lw=1.0, radius=0.07)
    rect(s, x+0.3, 2.0, 0.8, 0.8, fill=c, radius=0.5)
    txt(s, x+0.3, 2.0, 0.8, 0.8, [dict(text=num, size=20, bold=True, color=WHITE, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
    txt(s, x+0.3, 3.0, 3.3, 0.6, [dict(text=t, size=16, bold=True, color=INK, line=1.05)])
    txt(s, x+0.3, 3.6, 3.35, 1.55, [dict(text=b, size=12, color=MUTED, line=1.18)])
    x += 4.13
# strip manfaat langsung
rect(s, PAD, 5.6, CW, 1.05, fill=GREEN, radius=0.08)
txt(s, PAD+0.4, 5.6, CW-0.8, 1.05,
    [dict(text="Manfaat langsung:  ", size=13, bold=True, color=WHITE),
     dict(text="beli di harga lebih murah, stok tidak menumpuk, harga jual aman, dan margin terlindungi — semuanya dari satu aplikasi.", size=13, color=RGBColor(0xDF,0xEC,0xE5))],
    anchor=MSO_ANCHOR.MIDDLE)
footer(s, 3)
notes(s, "Solusi dalam tiga lapis: (1) Prediksi harga 7 hari dengan LSTM dan GRU + fitur eksternal; (2) Perencanaan pembelian — kapan dan berapa banyak; (3) Perhitungan HPP dan analisis keuntungan per menu. Ketiganya menyatu. Manfaat langsung: hemat biaya belanja, stok terkendali, harga jual aman, margin terlindungi.")

# ============================================================
# SLIDE 4 — FITUR & CARA KERJA
# ============================================================
s = slide()
header(s, "Fitur Utama", "Tiga Fitur Inti & Alur Kerja", "Dari data mentah menjadi keputusan belanja yang terukur.")
feat = [
    ("Food Price Forecasting", "LSTM & GRU + fitur eksternal (cuaca ERA5, kalender) → prediksi harga 7 hari.", ORANGE),
    ("Smart Purchasing Planning", "Saran kapan beli/tunda & estimasi volume belanja berdasarkan prediksi harga.", TEAL),
    ("Menu Profitability Analysis", "HPP, biaya per porsi, harga jual aman, margin & keuntungan per menu.", GREEN),
]
x = PAD
for t, b, c in feat:
    rect(s, x, 1.7, 3.93, 1.85, fill=WHITE, line=LINE, lw=1.2, radius=0.07)
    rect(s, x, 1.7, 3.93, 0.09, fill=c, shape=MSO_SHAPE.RECTANGLE)
    txt(s, x+0.28, 1.92, 3.4, 1.5,
        [dict(text=t, size=14.5, bold=True, color=INK, sa=3),
         dict(text=b, size=11.5, color=MUTED, line=1.15)])
    x += 4.13
# flow diagram — vertikal, confin di kiri agar tidak tabrakan panel dashboard
flow = [
    ("INPUT", "Data PIHPS Depok · Cuaca ERA5 · Kalender Indonesia", GREEN),
    ("MODEL", "LSTM / GRU · Jendela 30 hari · Prediksi 7 hari", TEAL),
    ("PREDIKSI", "Harga 13 komoditas · Ambang ±5% · Beli vs tunda", ORANGE),
    ("KEPUTUSAN", "Perencanaan belanja · HPP & margin · Harga jual aman", GREEN_D),
]
fy = 3.8
for t, b, c in flow:
    rect(s, PAD, fy, 6.28, 0.5, fill=WHITE, line=LINE, lw=1.2, radius=0.12)
    rect(s, PAD, fy, 1.3, 0.5, fill=c, radius=0.12)
    txt(s, PAD, fy, 1.3, 0.5, [dict(text=t, size=10.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
    txt(s, PAD+1.5, fy, 4.6, 0.5, [dict(text=b, size=11, color=MUTED)], anchor=MSO_ANCHOR.MIDDLE)
    fy += 0.6
rect(s, 7.35, 3.6, 5.36, 2.25, fill=WHITE, line=LINE, lw=1.2, radius=0.06)
rect(s, 7.35, 3.6, 5.36, 0.34, fill=NAV, shape=MSO_SHAPE.RECTANGLE)
txt(s, 7.35, 3.6, 5.36, 0.34, [dict(text="DASHBOARD PANGANLABA (asli)", size=9, bold=True, color=MUTED, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
try:
    s.shapes.add_picture(SHOT_WEB, In(7.5), In(4.02), In(5.06), In(1.7))
except Exception:
    pass
rect(s, PAD, 6.3, CW, 0.72, fill=ORANGE, radius=0.1)
txt(s, PAD+0.4, 6.3, CW-0.8, 0.72,
    [dict(text="Output: rekomendasi belanja + informasi margin untuk pengambilan keputusan — diperbarui harian.", size=13.5, bold=True, color=WHITE)],
    anchor=MSO_ANCHOR.MIDDLE)
footer(s, 4)
notes(s, "Fitur utama: (1) Food Price Forecasting berbasis LSTM dan GRU dengan fitur eksternal; (2) Smart Purchasing Planning; (3) Menu Profitability Analysis. Alur kerja: data PIHPS Kota Depok, cuaca ERA5, dan kalender Indonesia menjadi input; model LSTM/GRU dengan jendela 30 hari memprediksi 7 hari ke depan; hasilnya diekspresikan sebagai saran beli/tunda; lalu diintegrasikan ke kalkulator HPP dan analisis margin menu.")

# ============================================================
# SLIDE 5 — MARKET (diisi dari riset)
# ============================================================
s = slide()
header(s, "Pasar", "Target Pengguna & Ukuran Pasar", "TAM → SAM → SOM, berbasis data resmi + asumsi eksplisit.")
# baris angka kunci
kpi = [
    ("Total UMKM Indonesia", MARKET["umkm_id"], MARKET["umkm_id_src"], ORANGE),
    ("UMKM Kuliner Indonesia", MARKET["kuliner_id"], MARKET["kuliner_id_src"], TEAL),
    ("UMKM Kota Depok", MARKET["umkm_depok"], MARKET["depok_src"], GREEN),
    ("Populasi Kota Depok", MARKET["populasi_depok"], MARKET["populasi_src"], GREEN_D),
]
x = PAD
for lab, val, src, c in kpi:
    rect(s, x, 1.7, 2.75, 1.6, fill=WHITE, line=LINE, lw=1.1, radius=0.08)
    rect(s, x, 1.7, 2.75, 0.08, fill=c, shape=MSO_SHAPE.RECTANGLE)
    txt(s, x+0.18, 1.88, 2.4, 0.55, [dict(text=lab, size=10.5, bold=True, color=MUTED, line=1.05)])
    txt(s, x+0.18, 2.35, 2.4, 0.5, [dict(text=fmt(val), size=19, bold=True, color=INK)])
    txt(s, x+0.18, 2.85, 2.4, 0.35, [dict(text=src, size=8.5, color=FAINT)])
    x += 2.95
# TAM/SAM/SOM bars
tiers = [
    ("TAM — Semua UMKM Kuliner", MARKET["tam"], "52 juta × 40% asumsi kuliner = ±20,8 juta.", ORANGE),
    ("SAM — Dapat Dilayani", MARKET["sam"], "±60% dari TAM punya akses digital & bahan volatile.", TEAL),
    ("SOM — Target Awal", MARKET["som"], "±3–5% dari SAM dalam 2–3 tahun (asumsi).", GREEN),
]
y = 3.55
for lab, val, note, c in tiers:
    rect(s, PAD, y, 6.2, 0.95, fill=WHITE, line=LINE, lw=1.0, radius=0.1)
    txt(s, PAD+0.25, y+0.12, 5.7, 0.7,
        [dict(text=lab, size=12.5, bold=True, color=INK, sa=1),
         dict(text=note, size=10, color=MUTED, line=1.1)])
    rect(s, 7.0, y+0.18, 4.6, 0.58, fill=RGBColor(0xED,0xE7,0xDB), radius=0.12)
    txt(s, 7.0, y+0.18, 4.6, 0.58, [dict(text=fmt(val), size=15, bold=True, color=INK, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
    y += 1.12
txt(s, PAD, 6.84, CW, 0.24,
    [dict(text="Metode: TAM = total UMKM kuliner; SAM = subset akses digital & bahan volatile; SOM = penetrasi awal Depok. Data aktual + asumsi eksplisit.",
         size=10, italic=True, color=MUTED)])
footer(s, 5)
notes(s, "Market sizing memakai kerangka TAM/SAM/SOM. TAM: seluruh UMKM kuliner Indonesia. SAM: subset yang realistis dijangkau — punya akses digital dan bergantung komoditas volatile. SOM: target awal Kota Depok dengan asumsi penetrasi beberapa persen dalam 2–3 tahun. Semua angka berbasis sumber resmi (KemenkopUKM, BPS, Pemkot Depok) dan asumsi penetrasi eksplisit — bukan menebak seluruh UMKM sebagai calon pelanggan.")

# ============================================================
# SLIDE 6 — VALIDASI
# ============================================================
s = slide()
header(s, "Validasi", "Rencana Validasi Masalah & Kebutuhan Pengguna", "Data pengguna belum ada — rencana wawancara & kuesioner.")
# dimensi
dims = [
    ("Frekuensi kenaikan harga", "Seberapa sering harga bahan baku naik dalam sebulan terakhir."),
    ("Dampak ke keuntungan", "Bagaimana kenaikan tersebut memengaruhi margin / laba usaha."),
    ("Kebiasaan waktu belanja", "Kapan dan apa yang menjadi dasar memutuskan waktu belanja."),
    ("Cara menghitung HPP & laba", "Metode saat ini: manual, spreadsheet, atau belum dihitung."),
    ("Kebutuhan prediksi 7 hari", "Seberapa berguna prediksi harga seminggu ke depan bagi belanja."),
    ("Ketertarikan pakai aplikasi", "Minat & kesediaan mencoba PanganLaba (skala Likert)."),
]
pos = [(0.65,1.75),(4.74,1.75),(8.83,1.75),(0.65,3.75),(4.74,3.75),(8.83,3.75)]
for (x,y),(t,b) in zip(pos, dims):
    rect(s, x, y, 3.85, 1.8, fill=WHITE, line=LINE, lw=1.0, radius=0.08)
    txt(s, x+0.25, y+0.16, 3.35, 1.5,
        [dict(text=t, size=12.5, bold=True, color=GREEN_D, sa=3),
         dict(text=b, size=10.5, color=MUTED, line=1.15)])
rect(s, PAD, 5.85, CW, 1.0, fill=ORANGE_SOFT, line=LINE, lw=1.0, radius=0.08)
txt(s, PAD+0.4, 5.85, CW-0.8, 1.0,
    [dict(text="Status:  ", size=12.5, bold=True, color=ORANGE_D),
     dict(text="belum ada data hasil wawancara/survei. Diperlihatkan sebagai rencana validasi — responden target: pelaku UMKM kuliner Kota Depok, anonim, skala Likert 1–5.", size=12.5, color=INK, line=1.2)],
    anchor=MSO_ANCHOR.MIDDLE)
footer(s, 6)
notes(s, "Validasi kebutuhan dilakukan lewat wawancara dan kuesioner kepada pelaku UMKM kuliner Depok. Dimensi: frekuensi kenaikan harga bahan baku, dampaknya ke keuntungan, kebiasaan menentukan waktu belanja, cara menghitung HPP dan laba saat ini, kebutuhan prediksi harga 7 hari, serta ketertarikan menggunakan aplikasi. Penting: belum ada data hasil survei fiktif — ini rencana validasi, bukan hasil. Responden target: UMKM kuliner Depok, anonim, skala Likert.")

# ============================================================
# SLIDE 7 — KOMPETITOR (tabel) — PanganLaba vs website yang sudah ada
# ============================================================
s = slide()
header(s, "Kompetitor", "PanganLaba vs Website yang Sudah Ada", "Perbandingan fitur diverifikasi dari situs resmi (17 Nov 2026).")

def mark(v):
    if v is True: return ("✓", GREEN, True)
    if v is False: return ("—", FAINT, False)
    return (str(v), ORANGE_D, True)

rows = [
    ("PanganLaba (produk ini)", "Indonesia", True, True, True, True, False, True, True),
    ("RacikLaba.id", "Indonesia", False, False, False, False, False, True, True),
    ("PIHPS — Bank Indonesia", "Indonesia", True, False, False, False, False, False, False),
    ("Qasir (POS restoran)", "Indonesia", False, False, False, False, True, "Parsial", False),
    ("Majoo (POS + inventori)", "Indonesia", False, False, False, "Parsial", True, "Parsial", False),
    ("DTN (intelijen agri)", "AS", True, "Belum jelas", False, "Parsial", True, False, False),
    ("Tridge (intelijen dagang)", "Korea", True, False, False, False, False, False, False),
]
cols = [("Produk", 2.75), ("Negara", 1.05), ("Info harga", 1.05), ("Prediksi", 1.2),
        ("ML", 0.7), ("Pl. Belanja", 1.45), ("Inventory", 1.05), ("HPP", 0.95), ("Analisis Menu", 1.89)]
hy = 1.62
hh = 0.46
rect(s, PAD, hy, CW, hh, fill=GREEN, radius=0.04)
hcx = PAD
for name, w in cols:
    txt(s, hcx+0.04, hy, w-0.08, hh, [dict(text=name, size=10, bold=True, color=WHITE, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
    hcx += w
ry = hy + hh
rh = 0.44
for i, row in enumerate(rows):
    is_us = (i == 0)
    fill = GREEN_SOFT if is_us else (WHITE if i % 2 == 1 else CANVAS)
    rect(s, PAD, ry, CW, rh, fill=fill, shape=MSO_SHAPE.RECTANGLE)
    if is_us:
        rect(s, PAD, ry, CW, rh, fill=None, line=GREEN, lw=1.5, shape=MSO_SHAPE.RECTANGLE)
    cx = PAD
    txt(s, cx+0.1, ry, cols[0][1]-0.18, rh, [dict(text=row[0], size=10.5, bold=True, color=GREEN_D if is_us else INK, line=1.0)], anchor=MSO_ANCHOR.MIDDLE)
    cx += cols[0][1]
    txt(s, cx+0.05, ry, cols[1][1]-0.1, rh, [dict(text=row[1], size=10, color=MUTED, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
    cx += cols[1][1]
    for k, v in enumerate(row[2:]):
        colw = cols[k+2][1]
        t, c, b = mark(v)
        txt(s, cx+0.04, ry, colw-0.08, rh, [dict(text=t, size=10.5, bold=b, color=c, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
        cx += colw
    ry += rh
txt(s, PAD, ry+0.05, 6.0, 0.3, [dict(text="✓ ada   ·   Parsial = sebagian   ·   — tidak ada", size=9.5, color=FAINT)])
by = ry + 0.42
rect(s, PAD, by, 5.95, 1.3, fill=WHITE, line=LINE, lw=1.0, radius=0.08)
txt(s, PAD+0.25, by+0.1, 5.5, 1.1,
    [dict(text="PERSAMAAN", size=10.5, bold=True, color=TEAL, sa=3),
     dict(text="Semua menyajikan informasi harga atau pencatatan usaha; PIHPS & PanganLaba sama-sama pakai data harga pangan resmi Kota Depok.", size=10.5, color=MUTED, line=1.15)])
rect(s, 6.78, by, 5.93, 1.3, fill=ORANGE_SOFT, line=LINE, lw=1.0, radius=0.08)
txt(s, 7.03, by+0.1, 5.45, 1.1,
    [dict(text="PERBEDAAN & KETERBATASAN", size=10.5, bold=True, color=ORANGE_D, sa=3),
     dict(text="PIHPS/Tridge/DTN: data saja, tanpa alat keputusan. Qasir/Majoo: POS & inventori kuat, tanpa prediksi harga, HPP manual. PanganLaba: prediksi + HPP per menu, tanpa manajemen stok.", size=10.5, color=INK, line=1.15)])
footer(s, 7, "Sumber: bi.go.id/hargapangan, qasir.id, majoo.id, dtn.com, tridge.com")
notes(s, "Perbandingan PanganLaba dengan website yang sudah ada, diverifikasi dari situs resmi. Kolom: informasi harga pangan, prediksi harga komoditas, algoritma machine learning, perencanaan pembelian bahan baku, manajemen persediaan, perhitungan HPP, analisis keuntungan menu. PanganLaba unggul di prediksi berbasis LSTM/GRU, HPP otomatis per menu, dan analisis keuntungan menu; keterbatasan jujur: tidak ada manajemen stok/inventori. PIHPS (Bank Indonesia) menyediakan data harga resmi tanpa prediksi; Qasir dan Majoo kuat di POS/inventori tapi tanpa prediksi harga dan HPP manual; DTN dan Tridge berorientasi B2B/global, bukan UMKM kuliner. Tidak ada klaim 'pertama' atau 'satu-satunya' — kesimpulan murni dari tabel fitur terverifikasi.")

# SLIDE 8 — COMPETITIVE ADVANTAGE
# ============================================================
s = slide()
header(s, "Keunggulan", "Pembeda PanganLaba", "Bukan sekadar angka prediksi — sistem keputusan harian untuk UMKM kuliner.")
adv = [
    ("Prediksi + keputusan", "Mengubah data harga menjadi saran beli/tunda, bukan hanya angka.", ORANGE),
    ("LSTM vs GRU teruji", "Kedua model dievaluasi pada data lokal Depok — GRU harga-saja terbaik: median MAPE ≈3,5%.", TEAL),
    ("Fitur eksternal", "Cuaca ERA5 & kalender Indonesia diuji pengaruhnya — dilaporkan jujur.", GREEN),
    ("Harga → HPP terintegrasi", "Harga bahan dari prediksi langsung masuk ke kalkulator HPP & margin.", GREEN_D),
    ("Analisis per menu", "Keuntungan setiap menu terukur, bukan sekadar laba global.", TEAL_D),
    ("Fokus UMKM kuliner", "Sederhana, bahasa Indonesia, akses browser HP tanpa instalasi.", ORANGE_D),
]
pos = [(0.65,1.75),(4.74,1.75),(8.83,1.75),(0.65,4.0),(4.74,4.0),(8.83,4.0)]
for (x,y),(t,b,c) in zip(pos, adv):
    rect(s, x, y, 3.85, 2.05, fill=WHITE, line=LINE, lw=1.0, radius=0.07)
    rect(s, x, y, 0.09, 2.05, fill=c, shape=MSO_SHAPE.RECTANGLE)
    txt(s, x+0.28, y+0.18, 3.35, 1.75,
        [dict(text=t, size=13.5, bold=True, color=INK, sa=3),
         dict(text=b, size=11, color=MUTED, line=1.18)])
rect(s, PAD, 6.3, CW, 0.75, fill=TEAL, radius=0.1)
txt(s, PAD+0.4, 6.3, CW-0.8, 0.75,
    [dict(text="Dampak & indikator: waktu belanja lebih tepat, margin per menu terjaga, keputusan berbasis data — diukur lewat uji coba UMKM (waktu tugas, kemudahan, manfaat skor 1–5).", size=12, bold=True, color=WHITE, line=1.15)],
    anchor=MSO_ANCHOR.MIDDLE)
footer(s, 8, "Evaluasi: reports/HASIL_MODEL.md, model_comparison.csv")
notes(s, "Pembeda: integrasi prediksi harga dan perencanaan belanja; perbandingan LSTM dan GRU yang dievaluasi pada data lokal; pemanfaatan fitur eksternal yang diuji jujur; integrasi harga bahan ke perhitungan HPP; analisis keuntungan per menu; dan fokus pada kebutuhan UMKM kuliner. Indikator dampak: efektivitas waktu belanja, keterjagaan margin, dan hasil uji coba aplikasi.")

# ============================================================
# SLIDE 9 — BUSINESS MODEL (sesuai kode aplikasi: 1 paket + trial)
# ============================================================
s = slide()
header(s, "Bisnis", "Model Bisnis & Paket Langganan", "Trial 7 hari → satu paket Starter berbayar, pembayaran manual.")
cards = [
    ("TRIAL 7 HARI", "Rp0", ORANGE,
     ["Login pertama dengan Google → trial 7 hari", "Tanpa kartu kredit, akses penuh", "Setelah trial: pilih paket atau akses dijeda"]),
    ("STARTER", "Rp150.000/bulan", TEAL,
     ["Satu paket berbayar (bulanan)", "Komoditas tak terbatas", "Dashboard dasar, harga PIHPS harian", "Akses browser HP tanpa instalasi"]),
    ("PEMBAYARAN", "Transfer manual", GREEN,
     ["Bayar via transfer rekening", "Konfirmasi admin sebelum paket aktif", "Status trial / aktif / berakhir di dashboard"]),
]
x = PAD
cw = 3.79
gap = 0.36
for name, price, c, items in cards:
    rect(s, x, 1.7, cw, 4.0, fill=WHITE, line=LINE, lw=1.2, radius=0.06)
    rect(s, x, 1.7, cw, 0.55, fill=c, radius=0.04)
    txt(s, x+0.25, 1.7, cw-0.5, 0.55, [dict(text=name, size=14, bold=True, color=WHITE)], anchor=MSO_ANCHOR.MIDDLE)
    txt(s, x+0.28, 2.42, cw-0.56, 0.62, [dict(text=price, size=20, bold=True, color=INK)])
    bullets(s, x+0.28, 3.18, cw-0.56, 2.5, items, size=10.5, gap=8, marker="•  ")
    x += cw + gap
rect(s, PAD, 5.95, CW, 0.95, fill=GREEN_SOFT, line=LINE, lw=1.0, radius=0.08)
txt(s, PAD+0.4, 6.03, CW-0.8, 0.79,
    [dict(text="Asumsi:  ", size=11, bold=True, color=GREEN_D),
     dict(text="ARPU Rp150.000/bln (dari kode aplikasi). Konversi asumsi 2–5% dari SOM (±500 pelanggan) → potensi Rp9–22,5 juta/tahun di Depok. Ini target simulasi, bukan proyeksi realisasi. Paket dan harga ditetapkan setelah uji kesediaan bayar.", size=10.5, color=INK, line=1.15)],
    anchor=MSO_ANCHOR.MIDDLE)
footer(s, 9)
notes(s, "Model bisnis sesuai kode aplikasi: trial 7 hari gratis sejak login pertama dengan Google (tanpa kartu kredit). Setelah trial, satu paket berbayar: Starter Rp150.000/bulan, komoditas tak terbatas, dashboard dasar, harga PIHPS harian. Pembayaran manual via transfer rekening, aktif setelah konfirmasi admin; status trial/aktif/berakhir ditampilkan di dashboard. Tidak ada paket Free/Basic/Pro. Simulasi pendapatan: ARPU Rp150.000 × konversi asumsi 2–5% dari SOM (±500 pelanggan) = Rp9–22,5 juta/tahun di Depok — target simulasi, bukan proyeksi realisasi.")

# SLIDE 10 — KESIMPULAN & ROADMAP
# ============================================================
s = slide()
header(s, "Penutup", "Kesimpulan & Roadmap Pengembangan", None)
# kesimpulan
rect(s, PAD, 1.7, 6.1, 3.3, fill=WHITE, line=LINE, lw=1.1, radius=0.06)
txt(s, PAD+0.3, 1.85, 5.5, 0.4, [dict(text="RINGKASAN", size=12, bold=True, color=ORANGE_D)])
bullets(s, PAD+0.3, 2.3, 5.55, 2.6, [
    "Masalah: fluktuasi harga bahan gerus margin UMKM kuliner.",
    "Solusi: prediksi harga (LSTM/GRU) + perencanaan belanja + HPP/margin.",
    "Target: UMKM kuliner, awal Kota Depok → skala nasional.",
    "Pembeda: belum ada kompetitor dengan kombinasi serupa.",
    "Bisnis: trial 7 hari → langganan Starter Rp150.000/bln.",
], size=11.5, gap=8)
# roadmap
rect(s, 6.95, 1.7, 5.75, 3.3, fill=GREEN_SOFT, line=LINE, lw=1.1, radius=0.06)
txt(s, 7.25, 1.85, 5.15, 0.4, [dict(text="ROADMAP", size=12, bold=True, color=GREEN_D)])
steps = [
    ("1", "Penyempurnaan website & UX"),
    ("2", "Pengumpulan & pengolahan data harga pangan"),
    ("3", "Pengujian model LSTM & GRU"),
    ("4", "Uji manfaat fitur kepada UMKM"),
    ("5", "Evaluasi & pengembangan produk"),
]
sy = 2.35
for num, t in steps:
    rect(s, 7.25, sy, 0.42, 0.42, fill=GREEN, radius=0.5)
    txt(s, 7.25, sy, 0.42, 0.42, [dict(text=num, size=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
    txt(s, 7.85, sy+0.02, 4.7, 0.42, [dict(text=t, size=12, bold=True, color=INK)], anchor=MSO_ANCHOR.MIDDLE)
    sy += 0.56
# closing
rect(s, PAD, 5.3, CW, 1.5, fill=GREEN, radius=0.08)
txt(s, PAD+0.5, 5.3, CW-1.0, 1.5,
    [dict(text="PanganLaba membantu UMKM kuliner membeli saat harga tepat, menjaga margin, dan mengambil keputusan berbasis data — bukan tebak-tebakan.",
         size=15.5, bold=True, color=WHITE, line=1.2)],
    anchor=MSO_ANCHOR.MIDDLE)
txt(s, PAD, 6.95, CW, 0.4,
    [dict(text="Terima kasih — siap menerima masukan & pertanyaan.", size=12, italic=True, color=MUTED, align=PP_ALIGN.CENTER)])
footer(s, 10)
notes(s, "Kesimpulan: masalah fluktuasi harga bahan baku yang menggerus margin UMKM kuliner dijawab PanganLaba lewat prediksi harga (LSTM/GRU + fitur eksternal), perencanaan belanja, dan analisis HPP/margin per menu. Target pasar awal Kota Depok, dengan potensi skala nasional. Belum ada kompetitor dengan kombinasi fitur ini. Model bisnis freemium + langganan. Roadmap lima tahap: penyempurnaan website, pengumpulan & pengolahan data harga, pengujian model LSTM/GRU, uji manfaat kepada UMKM, dan evaluasi pengembangan produk. Tutup dengan ajakan diskusi dan tanya jawab.")

prs.save(r"c:\pangan\reports\PanganLaba_Presentasi.pptx")
print("OK saved. slides =", len(prs.slides._sldIdLst))

