# Narasi Detail Presentasi — Food Price Forecasting (PanganLaba)

> Naskah lisan lengkap untuk slide 5–7 deck 13 slide (`PanganLaba_Presentasi_13Slide_v2.pptx`).
> Ditulis untuk menjawab 7 tujuan akhir dosen. Semua angka/konfigurasi terverifikasi dari kode & laporan
> ([models.py](../backend/src/pangan_forecast/models.py), [features.py](../backend/src/pangan_forecast/features.py),
> [data.py](../backend/src/pangan_forecast/data.py), [SOURCE_NOTES.md](../data/SOURCE_NOTES.md),
> [model_comparison_summary.csv](../reports/model_comparison_summary.csv), [HASIL_MODEL.md](../reports/HASIL_MODEL.md)).
> Konteks justifikasi (mis. "suhu memengaruhi produktivitas") bersifat konseptual, ditandai di teks.

---

## Peta: 7 tujuan dosen → lokasi di slide

| # | Tujuan dosen | Slide / elemen |
|---|---|---|
| 1 | Data apa yang digunakan? | Slide 5 — kartu sumber (harga, cuaca, kalender) |
| 2 | Dari mana data diperoleh? | Slide 5 — kartu sumber (PIHPS, Open-Meteo ERA5, CSV kalender) |
| 3 | Bagaimana data diolah? | Slide 5 — kartu "Preprocessing & Normalisasi" |
| 4 | Mengapa LSTM & GRU? | Slide 6 — "Mengapa LSTM & GRU?" |
| 5 | Bagaimana kedua model bekerja? | Slide 6 — panel LSTM/GRU + "Cara Kerja di Penelitian" |
| 6 | Peran cuaca ERA5 & kalender? | Slide 5 — "Mengapa Ditambahkan?" + Slide 7 hasil evaluasi |
| 7 | Proses hingga prediksi 7 hari? | Slide 7 — alur 6 tahap + diagram |

---

## Slide 5 — Data & Pengolahan untuk Prediksi Harga

### Narasi lisan (≈2–2,5 menit)

> "Dosen, saya mulai dari bahan dasar yang kami pakai untuk memprediksi harga. Ada tiga sumber data. Yang pertama dan utama adalah **harga komoditas pangan strategis**. Datanya diambil dari **PIHPS — Pusat Informasi Harga Pangan Strategis — Bank Indonesia**, khusus untuk wilayah **Kota Depok**. Total ada **20.824 observasi harga**, mencakup **16 komoditas**, dengan rentang waktu dari **2 Januari 2020 sampai 10 November 2026**, dalam satuan **rupiah per kilogram**. Dari 16 komoditas itu, **13 di antaranya memiliki riwayat data yang cukup panjang**, sehingga dipakai untuk melatih model; sisanya masih terlalu pendek.
>
> Dua sumber berikutnya adalah data pendukung. Yang kedua, **cuaca harian** dari model reanalisis **ERA5**, diambil lewat **API Open-Meteo**. Ini data grid pada satu titik representatif di Depok — koordinat minus 6,5 lintang selatan, 106,75 bujur timur, elevasi 84 meter. Perlu saya tekankan, ini **data reanalisis grid, bukan pengukuran stasiun BMKG**. Ada enam variabel cuaca yang dipakai: suhu rata-rata, suhu maksimum, suhu minimum, presipitasi harian, kecepatan angin maksimum, dan radiasi matahari gelombang pendek. Cakupannya 2.491 tanggal, dari 2020 sampai Oktober 2026.
>
> Sumber ketiga, **kalender Indonesia**, berupa CSV yang menandai **hari libur nasional, cuti bersama, dan akhir pekan**, serta tanggal-tanggal yang berhubungan dengan **Idulfitri**. Satu hal yang perlu diketahui: sumber kalender ini **tidak menandai periode Ramadan maupun hari-hari menjelang Idulfitri** — jadi fitur itu memang tidak tersedia dalam model.
>
> Lalu bagaimana data diolah? Ada empat tahap. Pertama, **validasi**: kami membuang tanggal dan harga yang tidak valid, memastikan harga bernilai positif, dan merata-ratakan data duplikat pada tanggal yang sama. Kedua, **penyatuan ke kalender harian penuh** — setiap komoditas direntangkan ke semua tanggal yang ada, lalu digabungkan dengan cuaca dan kalender. Ketiga, **pengisian nilai hilang**: dipakai interpolasi linear, dan hanya untuk sela di dalam seri, bukan untuk memperkirakan di luar rentang data; sedangkan penanda kalender yang kosong diisi nol. Keempat, **normalisasi** memakai StandardScaler, dan penting dicatat — scaler ini **hanya dipasang pada data pelatihan**, agar tidak membocorkan informasi dari data uji.
>
> Terakhir, kami membedakan dua jenis fitur. **Fitur utama** adalah riwayat harga itu sendiri: harga hari ini, harga satu hari lalu, harga tujuh hari lalu, serta rata-rata harga tujuh dan tiga puluh hari. **Fitur tambahan** adalah cuaca ERA5, kalender, dan siklus hari/bulan. Tiga kartu paling bawah di slide ini merangkum: preprocessing dan normalisasi, pembedaan fitur utama versus tambahan, dan alasan mengapa fitur tambahan itu ditambahkan."

### Poin penting
- Membedakan **fakta terverifikasi** (jumlah, rentang, variabel, sumber) vs **justifikasi konseptual** (alasan fitur tambahan).
- Kalau ditanya "kenapa 13 bukan 16 komoditas?" → jawab: 3 seri baru cuma punya 15 observasi, belum cukup untuk membentuk model.

---

## Slide 6 — Model Machine Learning: LSTM vs GRU

### Narasi lisan (≈2–2,5 menit)

> "Sekarang saya jelaskan mengapa penelitian ini memilih **LSTM dan GRU**, dan bagaimana keduanya bekerja — dikaitkan langsung dengan data harga yang tadi.
>
> **Mengapa LSTM dan GRU?** Harga pangan adalah **data deret waktu yang berurutan menurut waktu**: nilai hari ini bergantung pada nilai hari-hari sebelumnya. LSTM dan GRU adalah jaringan saraf tiruan yang **dirancang khusus untuk memproses data berurutan** seperti ini. Keduanya punya kemampuan **menyimpan memori dari masa lalu**, sehingga bisa belajar pola historis harga — misalnya kenaikan menjelang hari raya, atau fluktuasi yang bersifat musiman. Selain itu, kedua model ini hadir sebagai solusi atas masalah **vanishing gradient** pada jaringan saraf berulang biasa — masalah di mana informasi dari masa lalu lama-lama hilang. Karena jendela prediksi kami adalah **7 sampai 30 hari**, kemampuan mengingat jangka pendek-menengah ini memang yang dibutuhkan.
>
> **Bagaimana LSTM bekerja?** LSTM menyimpan memori lewat sebuah sel memori yang dikendalikan tiga gerbang. Gerbang *input* memutuskan informasi baru apa yang ditulis ke memori; gerbang *forget* memutuskan informasi lama apa yang dibuang karena sudah tidak berguna; dan gerbang *output* memutuskan informasi apa yang dikeluarkan sebagai hasil. Karena kontrolnya lebih kaya, LSTM lebih ekspresif, tetapi parameternya lebih banyak sehingga sedikit lebih berat dikomputasi.
>
> **Bagaimana GRU bekerja?** GRU adalah varian yang lebih ringkas. Ia cukup memakai **dua gerbang: reset dan update**. Karena parameternya lebih sedikit, GRU lebih efisien dan lebih cepat dilatih, sementara akurasinya sering sebanding dengan LSTM.
>
> **Bagaimana keduanya diterapkan di penelitian ini?** Kedua model menerima masukan berupa **jendela 30 hari** data historis — berupa fitur-fitur yang tadi — untuk menghasilkan prediksi **harga 7 hari ke depan**. Arsitekturnya: satu lapisan input berbentuk 30 hari kali jumlah fitur; lalu lapisan LSTM atau GRU dengan **48 unit**; diikuti **dropout** sebesar 15 persen untuk mencegah overfitting; satu lapisan padat dengan 32 unit dan aktivasi ReLU; dan lapisan keluaran dengan 7 nilai, sesuai horizon tujuh hari. Optimizer yang dipakai **Adam**, fungsi kerugian **MSE**, dan setiap kombinasi dilatih dengan random seed tetap 42 supaya bisa dibandingkan secara adil.
>
> Data setiap komoditas dibagi **secara kronologis: 80 persen untuk pelatihan, 20 persen untuk pengujian** — bukan acak. Total ada **52 eksperimen**: 13 komoditas, dua model, dan dua macam set fitur.
>
> Terakhir, mengapa kedua model ini layak dibandingkan? Karena keduanya sama-sama berbasis gerbang pada RNN, jadi perbandingannya adil — perbedaannya murni pada kompleksitas dan efisiensi. **Pemilihan ini berdasar karakteristik data deret waktu, bukan berdasarkan hasil akhir.** Jadi ini kerangka yang jujur: hasilnya kami laporkan apa adanya di slide berikutnya."

### Poin penting
- Tekankan "bukan berdasarkan hasil akhir" — ini persis yang diminta dosen.
- Semua angka arsitektur (48 unit, dropout 0,15, 32 unit, Adam, MSE, seed 42, split 80:20, 52 eksperimen) langsung dari `models.py` — terverifikasi.

---

## Slide 7 — Alur Proses Prediksi Harga

### Narasi lisan (≈2 menit)

> "Terakhir, saya rangkai semuanya menjadi satu alur proses prediksi, yang sesuai dengan implementasi di kode penelitian.
>
> **Tahap pertama, pengumpulan data** — tiga sumber yang tadi: harga PIHPS Kota Depok, cuaca ERA5, dan kalender Indonesia.
>
> **Tahap kedua, preprocessing dan normalisasi** — validasi, penyatuan ke kalender harian, interpolasi nilai hilang, dan normalisasi dengan StandardScaler pada data latih.
>
> **Tahap ketiga, pembentukan fitur dan dataset time series** — fitur harga dan eksternal dibentuk, lalu data disusun menjadi urutan: setiap contoh masukan adalah riwayat 30 hari, dengan target harga 7 hari ke depan.
>
> **Tahap keempat, pembagian data** — secara kronologis, 80 persen untuk latih, 20 persen untuk uji.
>
> **Tahap kelima, pelatihan dan evaluasi** — LSTM dan GRU dilatih, lalu dievaluasi memakai tiga metrik: **MAE**, **RMSE**, dan **MAPE** pada bagian uji yang belum pernah dilihat model.
>
> **Tahap keenam, prediksi** — model di-fit ulang dengan seluruh histori yang tersedia, lalu digunakan untuk menghasilkan prediksi harga 7 hari ke depan. Hasil prediksi inilah yang menjadi dasar bagi fitur-fitur lain di aplikasi, seperti perencanaan belanja dan analisis laba menu.
>
> Saya juga ingin menyampaikan hasil evaluasinya secara jujur. Pada evaluasi terbaru, **GRU dengan fitur harga saja memberikan error median terkecil**: median MAPE sekitar **3,48 persen**, dengan median MAE sekitar 976 rupiah per kilogram. Ini berarti rata-rata kesalahan prediksi relatif terhadap harga aktual sekitar 3,5 persen. Penting untuk saya sampaikan: **penambahan paket cuaca dan kalender sekaligus belum memperbaiki error keseluruhan** pada run ini. Karena ketiga kelompok fitur itu digabung sekaligus, pengaruh masing-masing fitur belum terisolasi, dan itu menjadi bahan evaluasi lanjutan."

### Poin penting
- Alur persis 6 tahap; cocok dengan diagram di slide.
- Tahap 6 sengaja hanya menyebut luasdasar fitur lain" tanpa memperluas ke pembahasan Smart Purchasing / Menu Profitability.

---

## Antisipasi tanya-jawab dosen

**T: Kenapa cuma 13 komoditas, bukan 16?**
J: Ada 16 nama komoditas dalam dataset. Tiga seri terbaru hanya memiliki 15 observasi per komoditas — belum cukup untuk membentuk model dengan jendela 30 hari. Jadi evaluasi dan model operasional memakai 13 komoditas.

**T: Berapa rentang data uji?**
J: Rentang target uji antar-komoditas sekitar pertengahan 2025 sampai November 2026 (contoh: 2025-06-16 – 2026-11-10). Karena cakupan tanggal berbeda antar-komoditas, tanggal uji tidak identik antar-komoditas, tetapi identik antar-varian pada komoditas yang sama.

**T: Data cuaca itu hasil prediksi apa rekaman historis?**
J: Rekaman historis reanalisis grid ERA5, diambil langsung dari API Open-Meteo. Bukan prakiraan BMKG. Titik grid mewakili satu lokasi, bukan rata-rata seluruh Depok.

**T: Kenapa tidak pakai data stasiun BMKG langsung?**
J: Sumber aktif proyek adalah ERA5/Open-Meteo; CSV lama dari pengguna dan data NASA POWER disimpan sebagai referensi, bukan fitur aktif. Ini sesuai catatan sumber data.

**T: Kenapa fitur eksternal tidak menurunkan error?**
J: Paket eksternal menggabungkan cuaca, kalender, dan siklus tanggal sekaligus, sehingga kontribusi masing-masing belum terisolasi. Ini satu split holdout kronologis dan satu seed; uji rolling-origin, beberapa seed, dan uji per fitur diperlukan sebelum menyimpulkan fitur eksternal berguna atau tidak.

**T: Apakah ada baseline pembanding selain LSTM/GRU?**
J: Belum. Evaluasi saat ini membandingkan LSTM dan GRU; baseline Naive atau ARIMA belum dimasukkan.

**T: Apa arti MAPE 3,48%?**
J: Itu median besar kesalahan relatif rata-rata per komoditas terhadap harga aktual, bukan klaim akurasi "100% − 3,48%". Diperoleh dari harga PIHPS yang semuanya positif.

**T: Frame prediksi 7 hari dihitung bagaimana?**
J: Setiap origin harian pada bagian uji menghasilkan 7 langkah prediksi. Karena jendela prediksi saling tumpang tindih, kesalahan antar-baris tidak independen; itu batas interpretasi yang perlu disampaikan.

---

## Lampiran — Fakta kunci (untuk pegangan cepat)

| Aspek | Nilai (terverifikasi) |
|---|---|
| Sumber harga | PIHPS Bank Indonesia, Kota Depok |
| Jumlah observasi | 20.824 |
| Komoditas | 16 nama; 13 dengan model |
| Rentang harga | 2020-01-02 – 2026-11-10 |
| Satuan | Rp/kg |
| Sumber cuaca | Open-Meteo API, model ERA5, grid -6,5;106,75, elevasi 84 m |
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
| Eksperimen | 52 (13 × 2 × 2) |
| Metrik | MAE, RMSE, MAPE (Rp/kg untuk MAE/RMSE) |
| Hasil terbaik (terbaru) | GRU harga-saja: median MAE 976,59; RMSE 2.318,43; MAPE 3,48% |
| Baseline | belum ada (Naive/ARIMA belum diuji) |
| Stabilitas | belum ada uji multi-seed / rolling-origin |
