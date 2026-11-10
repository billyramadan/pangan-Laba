# Ringkasan temuan proyek PanganLaba

Angka evaluasi dan simulasi di bawah mengikuti data serta artefak terbaru bertanggal **10 November 2026**.

## 1. Data dan ruang lingkup

Data harga proyek berisi **20,824 observasi dari 16 nama komoditas**, dengan tanggal 2020-01-02 sampai 2026-11-10; semua baris yang ditambahkan berasal dari workbook PIHPS untuk Kota Depok dan memakai Rp/kg. Pembaruan 13 workbook menambahkan 195 observasi pada 21 Oktober–10 November 2026. Header workbook berlanjut sampai 30 November, tetapi kolom setelah 10 November belum berisi harga dan tidak dianggap sebagai data aktual.

Tiga seri baru (Gula Pasir, Cabai Merah Besar, Cabai Merah Keriting) disimpan terpisah dari seri lama yang memiliki jenis berbeda. Masing-masing baru memiliki 15 observasi, jadi belum cukup untuk pelatihan jendela 30 hari dan belum muncul pada evaluasi model. Evaluasi saat ini mencakup 13 seri historis yang memadai, menghasilkan 52 kombinasi model/fitur. Data harian setelah pembersihan berisi 31,466 baris.

Cuaca historis berasal dari ERA5 melalui Open-Meteo; kalender berasal dari CSV yang diberikan pengguna. Kalender mencakup libur nasional, cuti bersama, akhir pekan, dan penanda Idulfitri.

## 2. Evaluasi model terbaru

Data evaluasi dipisahkan secara kronologis 80:20. Model memakai 30 hari riwayat untuk memprediksi tujuh hari ke depan. MAE dan RMSE menggunakan Rp/kg, sedangkan MAPE menggunakan persen. Tabel merangkum median antar komoditas. Sesudah evaluasi, 52 model operasional dilatih ulang dengan seluruh histori yang tersedia; model final dashboard tidak dipakai untuk menghitung skor holdout. Rinciannya tercatat di `reports/final_models_manifest.csv`.

| Model | Fitur | Median MAE (Rp/kg) | Median RMSE (Rp/kg) | Median MAPE (%) |
|---|---|---:|---:|---:|
| GRU | harga + cuaca + kalender + siklus tanggal | 1,278.35 | 2,510.16 | 4.31 |
| GRU | harga saja | 976.59 | 2,318.43 | 3.48 |
| LSTM | harga + cuaca + kalender + siklus tanggal | 1,461.90 | 2,883.28 | 6.57 |
| LSTM | harga saja | 1,421.30 | 2,632.62 | 4.76 |

GRU dengan harga saja memiliki median error terendah pada run ini. Paket eksternal menggabungkan cuaca, kalender, dan siklus tanggal, sehingga perbedaan hasil tidak menunjukkan dampak terpisah setiap kelompok fitur. Rentang target uji antar-komoditas adalah 2025-06-16 sampai 2026-11-10.

## 3. Simulasi rekomendasi beli/tunda

Simulasi terbaru berisi 3,464 siklus pada 13 komoditas yang dapat dievaluasi, dengan asumsi 1 kg per transaksi, ambang tunda 5%, dan batas tunda dua hari. Median selisih biaya adalah 0% untuk seluruh varian, sedangkan rerata per varian berada dekat nol dan sedikit negatif:

| Model | Fitur | Median selisih biaya (%) | Rerata selisih biaya (%) |
|---|---|---:|---:|
| GRU | harga + cuaca + kalender + siklus tanggal | 0.00 | -0.07 |
| GRU | harga saja | 0.00 | -0.06 |
| LSTM | harga + cuaca + kalender + siklus tanggal | 0.00 | -0.01 |
| LSTM | harga saja | 0.00 | -0.12 |

Angka ini tidak menunjukkan penghematan yang konsisten. Ini simulasi retrospektif dari data uji, bukan bukti penghematan atau laba aktual; belum memasukkan stok, kebutuhan, biaya simpan, transportasi, dan mutu bahan.

## 4. Batas dan langkah lanjutan

- Tiga komoditas baru belum dapat dievaluasi sebagai LSTM/GRU karena riwayatnya baru 15 observasi; kumpulkan histori lebih panjang sebelum menampilkan prediksi model untuk seri tersebut.
- Fitur eksternal diuji sebagai satu paket, jadi kontribusi cuaca dan kalender belum terpisah.
- Minta arahan pembimbing untuk ambang rekomendasi dan desain simulasi sebelum memakai hasil sebagai kesimpulan penelitian.
- Uji dashboard dan kalkulator ke UMKM dengan data resep serta biaya aktual; angka laba tetap estimasi berdasarkan masukan pengguna.

## 5. Berkas sumber dan hasil

- Sumber 13 workbook baru: `data/source_pihps/updates/2026-11-10/`.
- Audit tanggal dan jumlah observasi: `data/processed/pihps_update_audit_20261110.csv`.
- Harga hasil gabungan: `data/raw/prices.csv`; salinan sebelumnya ada di `backups/prices_before_pihps_update_20261110.csv`.
- Hasil evaluasi terperinci: `reports/model_comparison.csv`, `reports/forecasts.csv`, dan `reports/tabel_evaluasi_skripsi.csv`.
- Narasi dan grafik: `reports/BAHAN_SKRIPSI_HASIL.md` dan `reports/FIGURES_INDEX.md`.
