# Hasil Model — PanganLaba (ringkas untuk bimbingan)

**Data:** 13 komoditas harga pangan (Depok, sumber PIHPS)
**Konfigurasi:** Model (GRU vs LSTM) × Fitur (harga saja vs harga + cuaca + kalender + siklus tanggal)
**Desain uji:** jendela 30 hari, horizon 7 hari, data uji historis (akhir ~ Okt 2026)

---

## 1. Ringkasan / (median antar 13 komoditas)

| Model | Fitur | median MAE (Rp/kg) | median RMSE | median MAPE (%) |
|---|---|---|---|---|
| **GRU** | harga saja | **656** | 881 | **1,98** |
| GRU | +cuaca/kalender | 939 | 1218 | 2,46 |
| LSTM | harga saja | 989 | 1210 | 2,36 |
| LSTM | +cuaca/kalender | 1244 | 1563 | 3,54 |

**Temuan kunci (penting, jujur):**
1. **GRU mengungguli LSTM** pada hampir semua kasus (error lebih rendah).
2. **Menambah fitur cuaca + kalender justru menaikkan error** pada semua konfigurasi → pada data ini fitur eksternal belum membantu. Ini temuan yang menarik & siap diakui, bukan disembunyikan.

---

## 2. Uji terbaik vs terberat (per komoditas, GRU harga saja)

| Komoditas | MAE (Rp/kg) | MAPE (%) | Catatan |
|---|---|---|---|
| Gula Pasir Lokal | 102 | 0,55 | termudah |
| Minyak goreng bermerk | 164 | 0,73 | sangat baik |
| Beras | 309 | 1,98 | baik |
| Telur Ayam | 482 | 1,68 | baik |
| Daging Ayam | 825 | 2,01 | baik |
| Bawang Putih | 617 | 1,37 | sangat baik |
| Daging Sapi | 1643 | 1,09 | baik |
| Bawang Merah | 2040 | 3,79 | sedang |
| Minyak Curah | 656 | 2,99 | sedang |
| Cabai Merah | 3387 | 5,85 | volatile |
| Cabai Rawit Hijau | 3349 | 5,97 | volatile |
| Cabai Rawit Merah | 5618 | 7,53 | terberat |

> Pola: komoditas **volatile (cabai)** jauh lebih sulit diprediksi; yang **stabil (gula, minyak)** akurat.

---

## 3. Kalimat siap pakai

**Kesimpulan model:**
"Model GRU berbasis harga saja memberi rata-rata galat ~2% (median MAPE 1,98) pada 13 komoditas. GRU konsisten mengungguli LSTM. Penambahan fitur cuaca dan kalender belum memperbaiki akurasi pada data ini, sehingga menjadi bahan diskusi untuk penyempurnaan."
**Batasan:**
"Akurasi bervariasi antar komoditas; cabai yang sangat fluktuatif punya galat lebih tinggi (~7–8%). Prediksi berguna untuk perencanaan, bukan jaminan harga aktual."

---

## 4. Slide hasil (outline)

1. **Setup eksperimen** — 13 komoditas; GRU vs LSTM × harga saja vs +fitur; horizon 7 hari.
2. **Tabel ringkasan cortisol** (di atas).
3. **Grafik perbandingan** — bar chart MAE/MAPE per konfigurasi (bisa di-generate dari `reports/model_comparison_summary.csv`).
4. **Analisis per komoditas** — stabil vs volatile (tabel di atas).
5. **Temuan & batasan** — GRU lebih baik; fitur eksternal belum menolong; cabai sulit.

---

## 5. Referensi file data

- `reports/model_comparison.csv` — detail per komoditas × model × fitur
- `reports/model_comparison_summary.csv` — agregat (median/mean)
- `reports/tabel_evaluasi_skripsi.csv` — tabel rapi siap cetak
- `reports/forecasts.csv` — hasil prakiraan
