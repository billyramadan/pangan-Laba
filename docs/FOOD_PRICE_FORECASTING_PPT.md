# Food Price Forecasting — Materi 3 Slide (PanganLaba)

> Draf siap pindah ke PowerPoint. Berbasis kode nyata: [data.py](../backend/src/pangan_forecast/data.py), [features.py](../backend/src/pangan_forecast/features.py), [models.py](../backend/src/pangan_forecast/models.py), [SOURCE_NOTES.md](../data/SOURCE_NOTES.md), dan hasil evaluasi terbaru [model_comparison_summary.csv](../reports/model_comparison_summary.csv).
> Fokus hanya pada **Food Price Forecasting**. Hasil prediksi 7 hari = dasar untuk fitur lain (Smart Purchasing Planning, Menu Profitability Analysis), tidak dibahas di sini.

---

## Slide 1
### Judul saran: **Data & Pengolahan untuk Prediksi Harga**

**Poin inti di slide:**

1. **Sumber data utama — harga komoditas:**
   - PIHPS (Pusat Informasi Harga Pangan Strategis) Bank Indonesia, workbook Excel wilayah **Kota Depok**.
   - Data aktif: **20.824 observasi harga**, **16 nama komoditas**, rentang **2020-01-02 – 2026-11-10**, satuan **Rp/kg**.
   - 13 komoditas punya riwayat cukup untuk model; 3 seri baru belum cukup panjang.
2. **Data pendukung — cuaca ERA5 (Open-Meteo Historical Weather API):**
   - Model **ERA5** eksplisit, timezone Asia/Jakarta, satu titik grid (-6,5; 106,75), elevasi 84 m — reanalisis grid, bukan stasiun BMKG.
   - Variabel: suhu harian (`temp_c`, `temp_max_c`, `temp_min_c`), presipitasi (`rain_mm`), angin maksimum (`wind_max_kmh`), radiasi gelombang pendek (`solar_mj_m2`).
   - Rentang 2020-01-01 – 2026-10-26 (2.491 tanggal).
3. **Data pendukung — kalender Indonesia:**
   - CSV kalender 2020–2026 → variabel biner: `is_libur_nasional`, `is_cuti_bersama`, `is_weekend`, `is_idul_fitri` (dari keterangan Idulfitri/Lebaran).
   - Catatan: penanda **Ramadan / hari menjelang Idulfitri tidak tersedia** di sumber.
4. **Pengolahan & preprocessing (dari kode):**
   - Validasi: buang tanggal & harga invalid, harga harus positif, rata-rata duplikat per tanggal-komoditas.
   - **Reindex ke kalender harian penuh** per komoditas (tanggal tanpa observasi diisi gap).
   - **Gabung** cuaca & kalender ke kalender harian.
   - **Interpolasi linear hanya di dalam seri** (limit_area="inside") untuk harga & suhu/curah hujan; `ffill/bfill` untuk kategori; NaN kalender → 0.
   - **Pembentukan fitur** untuk model (lihat Slide 2).
5. **Fit ur utama vs fitur tambahan:**
   - **Fitur utama (harga):** `price`, `lag_1`, `lag_7`, `mean_7`, `mean_30`.
   - **Fitur tambahan (eksternal):** cuaca ERA5 + indikator kalender + siklus hari/bulan.

**Narasi lisan (≈60–90 detik):**
> "Dosen, saya mulai dari data yang dipakai untuk memprediksi harga. Data utamanya adalah harga komoditas pangan dari PIHPS Bank Indonesia untuk wilayah Kota Depok, dengan 20.824 observasi harga dari 16 komoditas, rentang 2020 sampai November 2026, dalam rupiah per kilogram. Karena harga pangan sangat dipengaruhi faktor di luar harga itu sendiri, saya menambahkan dua data pendukung. Pertama, cuaca harian dari model reanalisis ERA5 melalui API Open-Meteo — enam variabel, yaitu suhu, presipitasi, angin, dan radiasi matahari. Kedua, kalender Indonesia yang memberi tanda hari libur nasional, cuti bersama, akhir pekan, dan Idulfitri.
>
> Kemudian data diolah. Prosesnya: validasi dan pembersihan, menyatukan semua tanggal menjadi kalender harian penuh, menggabungkan harga dengan cuaca dan kalender, mengisi nilai yang hilang dengan interpolasi, lalu membentuk fitur. Penting untuk dibedakan: fitur utamanya adalah riwayat harga — harga hari ini, harga seminggu lalu, dan rata-rata harga 7 serta 30 hari. Sedangkan cuaca dan kalender berperan sebagai fitur tambahan yang membantu model mengenali pola perubahan harga."

**Catatan kerja:**
- Angka jumlah observasi, nama komoditas, dan rentang tanggal diambil langsung dari `SOURCE_NOTES.md` — sudah terverifikasi.
- Jika data diperbarui, angka ini harus disesuaikan.

---

## Slide 2
### Judul saran: **Model Machine Learning: LSTM vs GRU**

**Poin inti di slide:**

1. **Mengapa LSTM & GRU?**
   - Harga pangan adalah **deret waktu harian yang berurutan**; LSTM/GRU adalah jaringan saraf yang dirancang khusus untuk memproses informasi **berurutan (sekuensial)**.
   - Mereka menyimpan **memori dari masa lalu** — cocok menangkap pola historis harga (mis. kenaikan Hari Raya, fluktuasi musiman).
   - LSTM & GRU muncul sebagai solusi masalah **vanishing gradient** pada RNN biasa, sehingga mampu belajar dependensi jangka pendek-menengah (7–30 hari).
2. **LSTM (Long Short-Term Memory):**
   - Sel memori + **3 gerbang**: input, forget, output — mengontrol info yang disimpan/dibuang.
   - Lebih banyak parameter, lebih ekspresif, sedikit lebih berat secara komputasi.
3. **GRU (Gated Recurrent Unit):**
   - Varian ringkas LSTM, **2 gerbang**: reset & update.
   - Parameter lebih sedikit → lebih efisien, lebih cepat dilatih, akurasi sering sebanding.
4. **Cara kerja dalam penelitian ini (konfigurasi nyata dari `models.py`):**
   - Input: **jendela 30 hari** data historis → memprediksi **7 hari berikutnya**.
   - Arsitektur: `Input(30, fitur)` → `LSTM/GRU(48)` → `Dropout(0,15)` → `Dense(32, relu)` → `Dense(7)`.
   - Optimizer Adam, loss MSE; **StandardScaler** dipasang hanya pada data latih; seed tetap 42.
   - Setiap komoditas **dibagi kronologis 80% latih : 20% uji**.
   - 13 komoditas × 2 model × 2 set fitur = **52 eksperimen**.
5. **Kelebihan & keterbatasan**
   - **LSTM:** kelebihan — kontrol memori lebih kaya, cocok deret waktu panjang; keterbatasan — lebih banyak parameter, latih lebih lama.
   - **GRU:** kelebihan — lebih ringkas & cepat, hasil sering setara; keterbatasan — kontrol memori lebih sederhana.
6. **Alasan layak dibandingkan:**
   - Keduanya sama-sama arsitektur RNN ber-gerbang, sehingga perbandingannya adil; perbedaan hanya pada efisiensi & kompleksitas. Pemilihan ini berdasarkan **kesesuaian dengan karakteristik data deret waktu**, bukan berdasarkan hasil akhir.

**Narasi lisan (≈90–120 detik):**
> "Mengapa memilih LSTM dan GRU? Harga pangan adalah data yang berurutan menurut waktu, dan kedua model ini memang dirancang untuk memproses data berurutan. Mereka punya kemampuan menyimpan memori dari masa lalu, sehingga bisa belajar dari pola historis harga — misalnya kenaikan menjelang hari raya atau fluktuasi musiman — dan mengatasi masalah pelupaan informasi pada jaringan saraf berulang biasa.
>
> LSTM menyimpan memori lewat sel memori dengan tiga gerbang: input untuk menulis informasi baru, forget untuk membuang informasi lama yang tidak berguna, dan output untuk mengeluarkan hasil. GRU adalah varian yang lebih ringkas: cukup dua gerbang, reset dan update, dengan parameter lebih sedikit sehingga lebih cepat dan lebih efisien, sementara akurasinya sering sebanding dengan LSTM.
>
> Dalam penelitian ini, kedua model diberi masukan riwayat harga 30 hari terakhir untuk memprediksi harga 7 hari ke depan. Arsitekturnya: satu lapisan LSTM atau GRU dengan 48 unit, dropout untuk mencegah overfitting, satu lapisan padat, lalu keluaran 7 nilai harga. Datanya dibagi secara kronologis, 80 persen untuk pelatihan dan 20 persen untuk pengujian. Total ada 52 eksperimen: 13 komoditas, dua model, dan dua set fitur.
>
> Kedua model ini layak dibandingkan karena sama-sama berbasis gerbang, jadi perbandingannya adil — bedanya pada kompleksitas dan efisiensi. Pemilihan ini berdasar karakteristik data deret waktu, bukan karena hasil akhir tertentu."

**Catatan kerja:**
- Angka arsitektur (unit, dropout, optimizer, seed, split) persis dari `models.py` — terverifikasi.
- Jumlah eksperimen 52 = 13 komoditas × 2 model × 2 fitur — terverifikasi dari `model_comparison.csv`.
- Uraian LSTM/GRU adalah penjelasan konsep umum, bukan klaim implementasi; sesuaikan bahasa dengan kebutuhan akademik.

---

## Slide 3
### Judul saran: **Alur Proses Prediksi Harga PanganLaba**

**Poin inti di slide (alur):**
> Pengumpulan Data (PIHPS + ERA5 + Kalender) → Preprocessing & Penggabungan → Pembentukan Fitur → Pembentukan Dataset Time Series (jendela 30 hari → target 7 hari) → Pembagian Data (80% latih / 20% uji, kronologis) → Normalisasi (StandardScaler) → Pelatihan LSTM & GRU → Evaluasi (MAE, RMSE, MAPE) → Prediksi Harga 7 Hari ke Depan.

1. **Pengumpulan:** harga PIHPS Kota Depok, cuaca ERA5, kalender Indonesia.
2. **Preprocessing:** pembersihan, reindex harian, gabung, interpolasi.
3. **Fitur:** harga (lag/mean) + eksternal (cuaca, kalender, siklus tanggal).
4. **Sequence:** jendela 30 hari → prediksi 7 hari (target multi-step).
5. **Split:** kronologis 80:20 per komoditas.
6. **Pelatihan:** LSTM & GRU, scaler hanya dari data latih, early stopping, seed 42.
7. **Evaluasi:** MAE / RMSE / MAPE pada bagian uji holdout.
8. **Deploy & prediksi:** model di-fit ulang dengan seluruh histori, lalu `forecast_next` mengambil 30 hari fitur terakhir dan menghasilkan harga 7 hari ke depan → menjadi dasar rekomendasi belanja & analisis laba menu.

**Catatan integritas (penting untuk disampaikan):**
- Hasil evaluasi terbaru (Nov 2026) menunjukkan **GRU dengan fitur harga saja** punya error median terendah: **MAE ≈ Rp976,59/kg**, **RMSE ≈ Rp2.318/kg**, **MAPE ≈ 3,48%** (LSTM harga saja ≈ 4,76%).
- Paket fitur eksternal (cuaca + kalender + siklus sekaligus) **belum memperbaiki error keseluruhan** pada run ini. Ini disampaikan jujur; karena ketiga kelompok digabung sekaligus, pengaruh masing-masing fitur belum terisolasi dan perlu verifikasi lebih lanjut (mis. uji per fitur, beberapa seed, rolling-origin).
- Model akhir dashboard di-fit ulang dengan seluruh histori; skor tetap dihitung dari split uji, bukan dari model final.

**Narasi lisan (≈90 detik):**
> "Terakhir, saya perlihatkan alur keseluruhannya. Dimulai dari pengumpulan tiga sumber data: harga PIHPS Kota Depok, cuaca ERA5, dan kalender Indonesia. Lalu data dibersihkan, disatukan ke kalender harian, dan diisi nilai yang hilang. Selanjutnya fitur dibentuk, dan data disusun menjadi urutan time series — setiap contoh masukan adalah 30 hari riwayat, dengan target harga 7 hari ke depan. Data kemudian dibagi secara kronologis, 80 persen untuk latih dan 20 persen untuk uji. Setelah dinormalisasi, LSTM dan GRU dilatih dan dievaluasi memakai MAE, RMSE, dan MAPE pada bagian uji yang belum pernah dilihat model. Terakhir, model di-fit ulang dengan seluruh data yang tersedia dan digunakan untuk menghasilkan prediksi harga 7 hari ke depan, yang menjadi dasar bagi fitur perencanaan belanja dan analisis laba menu.
>
> Saya juga ingin menyampaikan hasilnya secara jujur. Pada evaluasi terbaru, GRU dengan fitur harga saja memberikan error median terkecil, sekitar 3,5 persen MAPE. Artinya rata-rata kesalahan prediksi relatif terhadap harga aktual sekitar 3,5 persen. Penambahan paket cuaca dan kalender sekaligus belum memperbaiki error keseluruhan pada run ini. Ini perlu saya sampaikan apa adanya, dan pengaruh masing-masing fitur eksternal masih perlu diteliti lebih lanjut secara terpisah."

**Catatan kerja:**
- Diagram alur sudah tersedia: [ml_pipeline_diagram.png](../reports/figures/ml_pipeline_diagram.png) (dan .svg) — bisa langsung dipakai di slide ini.
- Angka hasil evaluasi adalah versi terbaru dari `model_comparison_summary.csv`; jika run baru dijalankan, perbarui.

---

## Lampiran: Fakta kunci yang terverifikasi (untuk persiapan tanya-jawab)

| Aspek | Nilai (terverifikasi) |
|---|---|
| Sumber harga | PIHPS Bank Indonesia, Kota Depok |
| Jumlah observasi harga | 20.824 |
| Nama komoditas | 16 (13 punya model) |
| Rentang harga | 2020-01-02 – 2026-11-10 |
| Satuan | Rp/kg |
| Sumber cuaca | Open-Meteo Historical API, model ERA5, grid -6,5;106,75, elevasi 84 m |
| Variabel cuaca | temp_c, temp_max_c, temp_min_c, rain_mm, wind_max_kmh, solar_mj_m2 |
| Rentang cuaca | 2020-01-01 – 2026-10-26 (2.491 hari) |
| Kalender | libur nasional, cuti bersama, weekend, Idulfitri (tanpa Ramadan/near-Eid) |
| Fitur harga | price, lag_1, lag_7, mean_7, mean_30 |
| Fitur eksternal | cuaca + kalender + dow_sin/cos, month_sin/cos |
| Arsitektur | Input(30) → LSTM/GRU(48) → Dropout(0,15) → Dense(32, ReLU) → Dense(7) |
| Optimizer / loss | Adam / MSE |
| Scaler | StandardScaler (hanya data latih) |
| Seed | 42 |
| Split | kronologis 80:20 per komoditas |
| Jendela / horizon | 30 hari → 7 hari |
| Eksperimen | 52 (13 komoditas × 2 model × 2 fitur) |
| Metrik | MAE, RMSE, MAPE (Rp/kg untuk MAE/RMSE) |
| Hasil terbaik (terbaru) | GRU harga saja: median MAE 976,59; RMSE 2.318,43; MAPE 3,48% |

**Hal yang perlu diperiksa / disiapkan sebelum presentasi (jangan dipaksakan):**
- Kontribusi **masing-masing** fitur eksternal belum terisolasi (paket dicampur) — bila dosen menanyai, sampaikan ini sebagai arah kerja lanjutan.
- Uji stabilitas (beberapa seed, rolling-origin) belum dilakukan.
- Belum ada baseline Naive/ARIMA untuk pembanding.
- Kalender tidak memberi penanda Ramadan / hari menjelang Idulfitri.
