# -*- coding: utf-8 -*-
"""Food Price Forecasting — deck 3 slide, 16:9, gaya identik deck utama (make_deck2.py).
Materi bersandar pada implementasi nyata (models.py, features.py, data.py, SOURCE_NOTES.md,
model_comparison_summary.csv). Siap digabung ke PanganLaba_Presentasi.pptx.
"""
from pptx import Presentation
from pptx.util import Inches as In, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

INK       = RGBColor(0x2A, 0x21, 0x1C)
MUTED     = RGBColor(0x5E, 0x51, 0x49)
FAINT     = RGBColor(0x9A, 0x8E, 0x84)
GREEN     = RGBColor(0x35, 0x5F, 0x4E)
GREEN_D   = RGBColor(0x27, 0x4A, 0x3C)
TEAL      = RGBColor(0x2E, 0x6E, 0x6A)
TEAL_D    = RGBColor(0x22, 0x55, 0x52)
ORANGE    = RGBColor(0xE4, 0x57, 0x2E)
ORANGE_D  = RGBColor(0xC1, 0x3E, 0x1D)
SPICE     = RGBColor(0xE9, 0xA3, 0x3B)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
CREAM     = RGBColor(0xFF, 0xFD, 0xFA)
CANVAS    = RGBColor(0xFA, 0xF5, 0xEE)
LINE      = RGBColor(0xE6, 0xDB, 0xCC)
NAV       = RGBColor(0xF5, 0xED, 0xE2)
GREEN_SOFT = RGBColor(0xEA, 0xF3, 0xED)
TEAL_SOFT  = RGBColor(0xE6, 0xF1, 0xF1)
ORANGE_SOFT = RGBColor(0xF8, 0xF0, 0xE5)

F = "Segoe UI"

prs = Presentation()
prs.slide_width = In(13.333)
prs.slide_height = In(7.5)
BLANK = prs.slide_layouts[6]
W, H = 13.333, 7.5
PAD = 0.62
CW = W - 2*PAD
DIAGRAM = r"c:\pangan\reports\figures\ml_pipeline_diagram.png"

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

def bullets(s, x, y, w, h, items, size=12.5, color=MUTED, gap=7, bold=False, line=1.14, marker=None):
    paras = []
    for b in items:
        t = b if marker is None else marker + b
        paras.append(dict(text=t, size=size, bold=bold, color=color, line=line, sa=gap))
    txt(s, x, y, w, h, paras)

def header(s, kicker, title, sub=None, color=TEAL):
    y = 0.42
    rect(s, PAD, y, 0.12, 0.86, fill=color)
    txt(s, PAD+0.32, y-0.05, CW, 0.3, [dict(text=kicker.upper(), size=11.5, bold=True, color=ORANGE_D)])
    txt(s, PAD+0.32, y+0.22, CW, 0.62, [dict(text=title, size=27, bold=True, color=INK)])
    if sub:
        txt(s, PAD+0.32, y+0.94, CW, 0.34, [dict(text=sub, size=12.5, color=MUTED)])

def footer(s, n, source=None):
    txt(s, PAD, H-0.40, 8.6, 0.28, [dict(text="PanganLaba — Tugas Akhir · Bagian Food Price Forecasting", size=9, color=FAINT)])
    if source:
        txt(s, 6.6, H-0.40, 6.1, 0.28, [dict(text=source, size=8, color=FAINT, align=PP_ALIGN.RIGHT)])
    txt(s, W-0.62, H-0.48, 0.5, 0.3, [dict(text=str(n), size=11, bold=True, color=ORANGE, align=PP_ALIGN.RIGHT)])

def notes(s, text):
    nf = s.notes_slide.notes_text_frame
    nf.text = text

def source_card(s, x, y, w, h, tag, tagc, title, body):
    rect(s, x, y, w, h, fill=WHITE, line=LINE, lw=1.1, radius=0.06)
    rect(s, x, y, w, 0.42, fill=tagc, radius=0.04)
    txt(s, x+0.22, y, w-0.44, 0.42, [dict(text=tag, size=11, bold=True, color=WHITE)], anchor=MSO_ANCHOR.MIDDLE)
    txt(s, x+0.22, y+0.55, w-0.44, 0.4, [dict(text=title, size=13, bold=True, color=INK)])
    txt(s, x+0.22, y+0.98, w-0.44, h-1.1, [dict(text=body, size=10.5, color=MUTED, line=1.14)])

# ============================================================
# SLIDE 1 — DATA & PENGOLAHAN
# ============================================================
s = slide()
header(s, "Food Price Forecasting · 1/3", "Data & Pengolahan untuk Prediksi Harga",
       "Tiga sumber data → preprocessing → fitur utama vs tambahan.")
# tiga kartu sumber
source_card(s, PAD, 1.7, 3.93, 2.75, "Sumber utama", ORANGE, "Harga komoditas — PIHPS Bank Indonesia",
    "20.824 observasi · 16 komoditas · Kota Depok\nRentang 2020-01-02 – 2026-11-10 · Rp/kg\n13 komoditas punya riwayat cukup untuk model")
source_card(s, PAD+4.13, 1.7, 3.93, 2.75, "Data pendukung", TEAL, "Cuaca ERA5 — Open-Meteo",
    "Model ERA5, grid (-6,5; 106,75), elevasi 84 m\n6 variabel: suhu, presipitasi, angin, radiasi\n2.491 tanggal (2020–2026) · reanalisis, bukan stasiun")
source_card(s, PAD+8.26, 1.7, 3.93, 2.75, "Data pendukung", GREEN, "Kalender Indonesia",
    "Libur nasional · cuti bersama · akhir pekan\nIdulfitri (dari keterangan Lebaran)\nCatatan: penanda Ramadan / hari menjelang Idulfitri tidak tersedia")
# preprocessing strip
rect(s, PAD, 4.6, 6.2, 2.3, fill=CANVAS, line=LINE, lw=1.1, radius=0.06)
txt(s, PAD+0.28, 4.74, 5.7, 0.34, [dict(text="PREPROCESSING & PENGOLAHAN", size=11, bold=True, color=GREEN)])
bullets(s, PAD+0.28, 5.12, 5.7, 1.7, [
    "Validasi: buang tanggal/harga invalid, harga positif, rata-rata duplikat.",
    "Reindex ke kalender harian penuh per komoditas; gabung cuaca & kalender.",
    "Interpolasi linear hanya di dalam seri; NaN kalender → 0.",
    "Pembentukan fitur untuk model (slide berikutnya).",
], size=11, gap=6)
# fitur utama vs tambahan
rect(s, 7.0, 4.6, 5.71, 2.3, fill=ORANGE_SOFT, line=LINE, lw=1.1, radius=0.06)
txt(s, 7.28, 4.74, 5.2, 0.34, [dict(text="FITUR UTAMA vs TAMBAHAN", size=11, bold=True, color=ORANGE_D)])
txt(s, 7.28, 5.12, 5.15, 1.7, [
    dict(text="Fitur utama (harga):", size=11.5, bold=True, color=INK, sa=2),
    dict(text="price · lag_1 · lag_7 · mean_7 · mean_30", size=11, color=MUTED, sa=6),
    dict(text="Fitur tambahan (eksternal):", size=11.5, bold=True, color=INK, sa=2),
    dict(text="cuaca ERA5 + kalender + siklus hari/bulan · cuaca BMKG bulanan (diuji)", size=11, color=MUTED),
])
footer(s, 1, "Sumber: data/SOURCE_NOTES.md, backend/src/pangan_forecast/data.py")
notes(s, "Data utama: harga komoditas PIHPS Bank Indonesia wilayah Kota Depok, 20.824 observasi, 16 komoditas, rentang 2020 sampai November 2026, dalam rupiah per kilogram. Data pendukung: cuaca harian model reanalisis ERA5 lewat API Open-Meteo (enam variabel: suhu, presipitasi, angin, radiasi), kalender Indonesia (libur nasional, cuti bersama, akhir pekan, Idulfitri), dan cuaca bulanan stasiun Klimatologi BMKG yang juga diuji. Penanda Ramadan dan hari menjelang Idulfitri tidak tersedia di sumber. Pengolahan: validasi dan pembersihan, penyatuan ke kalender harian penuh, penggabungan harga dengan cuaca dan kalender, interpolasi nilai hilang, lalu pembentukan fitur. Dibedakan fitur utama riwayat harga (price, lag 1, lag 7, rata-rata 7 dan 30 hari) dan fitur tambahan cuaca, kalender, dan siklus tanggal.")

# ============================================================
# SLIDE 2 — MODEL LSTM vs GRU
# ============================================================
s = slide()
header(s, "Food Price Forecasting · 2/3", "Model Machine Learning: LSTM vs GRU",
       "RNN ber-gerbang untuk deret waktu harga pangan.")
# LSTM panel
rect(s, PAD, 1.7, 6.2, 2.6, fill=GREEN_SOFT, line=LINE, lw=1.1, radius=0.06)
txt(s, PAD+0.3, 1.86, 5.6, 0.35, [dict(text="LSTM — Long Short-Term Memory", size=14, bold=True, color=GREEN_D)])
txt(s, PAD+0.3, 2.28, 5.6, 1.9, [
    dict(text="Sel memori + 3 gerbang:", size=11.5, bold=True, color=INK, sa=3),
    dict(text="input (tulis) · forget (buang) · output (keluarkan)", size=11, color=MUTED, sa=4),
    dict(text="Mampu menyimpan informasi jangka panjang.", size=11, color=MUTED, sa=4),
    dict(text="Parametrik lebih banyak → lebih ekspresif, sedikit lebih berat.", size=11, color=MUTED),
])
# GRU panelrect(s, 6.93, 1.7, 5.78, 2.6, fill=TEAL_SOFT, line=LINE, lw=1.1, radius=0.06)
txt(s, 7.23, 1.86, 5.2, 0.35, [dict(text="GRU — Gated Recurrent Unit", size=14, bold=True, color=TEAL_D)])
txt(s, 7.23, 2.28, 5.2, 1.9, [
    dict(text="Varian ringkas LSTM, 2 gerbang:", size=11.5, bold=True, color=INK, sa=3),
    dict(text="reset & update", size=11, color=MUTED, sa=4),
    dict(text="Parameter lebih sedikit → lebih efisien & cepat dilatih.", size=11, color=MUTED, sa=4),
    dict(text="Akurasi sering sebanding dengan LSTM.", size=11, color=MUTED),
])
# alasan
rect(s, PAD, 4.45, 6.2, 2.0, fill=WHITE, line=LINE, lw=1.1, radius=0.06)
txt(s, PAD+0.28, 4.58, 5.6, 0.34, [dict(text="MENGAPA LSTM & GRU?", size=11, bold=True, color=ORANGE_D)])
bullets(s, PAD+0.28, 4.95, 5.7, 1.4, [
    "Harga pangan = deret waktu harian berurutan; LSTM/GRU dirancang untuk pemrosesan sekuensial.",
    "Menyimpan memori masa lalu → belajar pola historis & fluktuasi musiman/hari raya.",
    "Mengatasi masalah vanishing gradient pada RNN biasa — cocok untuk dependensi 7–30 hari.",
], size=10.5, gap=5)
# konfigurasi
rect(s, 6.93, 4.45, 5.78, 2.0, fill=CANVAS, line=LINE, lw=1.1, radius=0.06)
txt(s, 7.23, 4.58, 5.2, 0.34, [dict(text="CARA KERJA DI PENELITIAN INI", size=11, bold=True, color=GREEN)])
txt(s, 7.23, 4.95, 5.2, 1.42, [
    dict(text="Input jendela 30 hari → prediksi 7 hari.", size=11, bold=True, color=INK, sa=3),
    dict(text="Arsitektur: Input(30, fitur) → LSTM/GRU(48) → Dropout(0,15) → Dense(32, ReLU) → Dense(7).", size=10.5, color=MUTED, sa=3),
    dict(text="Adam · MSE · StandardScaler (hanya latih) · 3 seed (42/123/2026).", size=10.5, color=MUTED, sa=3),
    dict(text="Split kronologis 80:20 · 13 komoditas · 6 paket fitur × 3 seed = 468 eksperimen; 78 model deploy final.", size=10.5, color=MUTED),
])
rect(s, PAD, 6.55, CW, 0.5, fill=ORANGE, radius=0.1)
txt(s, PAD+0.35, 6.55, CW-0.7, 0.5,
    [dict(text="Layak dibandingkan: sama-sama RNN ber-gerbang → adil; berbeda di kompleksitas & efisiensi. Pilihan berdasar karakteristik data, bukan hasil akhir.", size=11.5, bold=True, color=WHITE, line=1.1)],
    anchor=MSO_ANCHOR.MIDDLE)
footer(s, 2, "Sumber: backend/src/pangan_forecast/models.py, features.py")
notes(s, "Mengapa LSTM dan GRU: harga pangan adalah data berurutan menurut waktu, dan kedua model dirancang untuk pemrosesan sekuensial. Mereka menyimpan memori masa lalu sehingga bisa belajar pola historis harga, dan mengatasi masalah vanishing gradient. LSTM punya sel memori dengan tiga gerbang — input untuk menulis, forget untuk membuang, output untuk mengeluarkan; lebih ekspresif tapi lebih berat. GRU varian ringkas dengan dua gerbang reset dan update; parameter lebih sedikit, lebih cepat, akurasi sering sebanding. Dalam penelitian ini model menerima riwayat 30 hari untuk memprediksi 7 hari ke depan; arsitektur: lapisan LSTM/GRU 48 unit, dropout, lapisan padat, keluaran 7 harga. Kos 80:20 kronologis; 13 komoditas × 6 paket fitur × 3 seed = 468 eksperimen, plus 78 model deploy final. Keduanya layak dibandingkan karena sama-sama berbasis gerbang; pemilihan berdasar karakteristik data, bukan hasil akhir.")

# ============================================================
# SLIDE 3 — ALUR PROSES PREDIKSI
# ============================================================
s = slide()
header(s, "Food Price Forecasting · 3/3", "Alur Proses Prediksi Harga",
       "Dari data mentah hingga prediksi 7 hari ke depan.")
# Kolom kiri: diagram alur native 6 langkah
flow_steps = [
    ("1", "Pengumpulan data — PIHPS · ERA5 · Kalender", ORANGE),
    ("2", "Preprocessing & normalisasi — validasi, reindex harian, interpolasi, StandardScaler", TEAL),
    ("3", "Fitur & dataset time series — jendela 30 hari → target 7 hari", GREEN),
    ("4", "Pembagian kronologis — 80% latih / 20% uji", GREEN_D),
    ("5", "Pelatihan LSTM & GRU + evaluasi MAE/RMSE/MAPE", TEAL_D),
    ("6", "Prediksi harga 7 hari → dasar fitur belanja & laba menu", ORANGE_D),
]
fx0, fx1 = PAD, 6.95
fbox_h, fbox_gap, farr_h = 0.62, 0.14, 0.14
fy0 = 1.72
for i, (num, t, c) in enumerate(flow_steps):
    y = fy0 + i * (fbox_h + fbox_gap)
    rect(s, fx0, y, fx1 - fx0, fbox_h, fill=c, radius=0.10)
    rect(s, fx0 + 0.18, y + (fbox_h - 0.36) / 2, 0.36, 0.36, fill=WHITE, radius=0.5)
    txt(s, fx0 + 0.18, y + (fbox_h - 0.36) / 2, 0.36, 0.36,
        [dict(text=num, size=12, bold=True, color=c, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
    txt(s, fx0 + 0.68, y, fx1 - fx0 - 0.84, fbox_h,
        [dict(text=t, size=11.5, bold=True, color=WHITE, line=1.05)], anchor=MSO_ANCHOR.MIDDLE)
    if i < len(flow_steps) - 1:
        ay = y + fbox_h
        rect(s, fx0 + (fx1 - fx0) / 2 - 0.16, ay, 0.32, farr_h, fill=LINE, radius=0.5)
# Kolom kanan: hasil + batasan
rect(s, 7.15, 1.72, 5.56, 3.05, fill=ORANGE_SOFT, line=LINE, lw=1.1, radius=0.06)
txt(s, 7.43, 1.86, 5.0, 0.34, [dict(text="HASIL EVALUASI (TERBARU) — JUJUR", size=11, bold=True, color=ORANGE_D)])
bullets(s, 7.43, 2.28, 5.05, 2.4, [
    "Baseline Naive terendah: median MAPE ≈ 1,13% (MAE ≈ Rp409/kg); SMA-7 ≈ 2,09%.",
    "ANN terbaik: GRU harga+kalender ≈ 3,53%; GRU harga-saja ≈ 3,72%; LSTM terbaik ≈ 4,58%.",
    "Paket eksternal memperbaiki error pada sebagian model (mis. GRU+kalender), tapi belum konsisten mengungguli harga-saja.",
    "Cuaca BMKG bulanan justru menaikkan error (MAPE ≈ 5,8–8,5%) — resolusi tidak cocok dengan model harian.",
], size=10.5, gap=6)
rect(s, 7.15, 4.95, 5.56, 1.95, fill=CANVAS, line=LINE, lw=1.1, radius=0.06)
txt(s, 7.43, 5.09, 5.0, 0.34, [dict(text="BATAS INTERPRETASI", size=11, bold=True, color=GREEN)])
bullets(s, 7.43, 5.47, 5.05, 1.4, [
    "Di dalam satu paket eksternal, pengaruh tiap fitur belum dipisahkan (dicoba per-paket).",
    "Evaluasi memakai 3 seed untuk stabilitas, namun tetap satu split holdout kronologis.",
    "Baseline Naive & SMA-7 sudah dilibatkan; ARIMA belum.",
], size=10.5, gap=6)
footer(s, 3, "Sumber: reports/model_comparison_summary.csv, reports/HASIL_MODEL.md")
notes(s, "Alur proses: pengumpulan tiga sumber data (harga PIHPS Kota Depok, cuaca ERA5, kalender Indonesia) → preprocessing dan normalisasi (validasi, penyatuan ke kalender harian, interpolasi, StandardScaler) → pembentukan fitur dan penyusunan dataset time series (setiap contoh masukan = 30 hari riwayat, target = 7 hari ke depan) → pembagian secara kronologis 80 persen latih dan 20 persen uji → pelatihan LSTM dan GRU lalu evaluasi memakai MAE, RMSE, dan MAPE pada bagian uji → model di-fit ulang dengan seluruh histori dan menghasilkan prediksi harga 7 hari ke depan, yang menjadi dasar fitur perencanaan belanja dan analisis laba menu. Hasil dievaluasi secara jujur: baseline Naive dan SMA-7 menghasilkan error terendah; di antara jaringan saraf, GRU harga+kalender terbaik (MAPE sekitar 3,53 persen), GRU harga-saja sekitar 3,72 persen, LSTM terbaik sekitar 4,58 persen. Cuaca BMKG bulanan menaikkan error (MAPE sekitar 5,8–8,5 persen) karena resolusinya tidak cocok dengan model harian. Batasan: di dalam satu paket eksternal pengaruh tiap fitur belum dipisahkan, evaluasi memakai 3 seed namun tetap satu split holdout, dan ARIMA belum dilibatkan.")

prs.save(r"c:\pangan\reports\FoodPriceForecasting_3Slide_v2.pptx")
print("OK saved. slides =", len(prs.slides._sldIdLst))
