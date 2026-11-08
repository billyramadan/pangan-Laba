# Evaluasi Ulang Model LSTM dan GRU

## Ringkasan pelatihan

Pelatihan ulang dijalankan pada 7 November 2026 menggunakan data olahan PIHPS Kota Depok dan fitur cuaca historis ERA5, kalender, serta siklus tanggal yang tersedia. Dataset olahan berisi 31.185 baris harian untuk 13 komoditas, pada rentang 2020-01-02 sampai 2026-10-21. Hasil evaluasi mencakup 52 kombinasi model dan fitur, serta 170.352 nilai prediksi uji.

Setiap komoditas dibagi secara kronologis: sekitar 80% periode awal untuk pelatihan dan 20% periode akhir untuk pengujian. Model menggunakan jendela 30 hari untuk memprediksi tujuh hari berikutnya. LSTM dan GRU dilatih dengan fitur harga saja, lalu dibandingkan dengan paket eksternal yang menambahkan cuaca ERA5, kalender, dan siklus tanggal. Batas maksimum pelatihan 15 epoch; early stopping memakai patience 5. Scaler dipasang pada data latih saja dan seed ditetapkan 42.

## Hasil median antar-komoditas

Median metrik per komoditas dipakai sebagai ringkasan utama agar komoditas dengan skala harga besar tidak mendominasi hasil.

| Model | Fitur | Median MAE (Rp/kg) | Median RMSE (Rp/kg) | Median MAPE | Rerata MAE (Rp/kg) | Rerata RMSE (Rp/kg) | Rerata MAPE |
|---|---|---:|---:|---:|---:|---:|---:|
| GRU | harga + cuaca + kalender + siklus tanggal | 939.09 | 1,217.52 | 2.46% | 1,959.22 | 2,596.95 | 3.82% |
| GRU | harga saja | 656.00 | 881.28 | 1.98% | 1,497.54 | 2,106.82 | 2.84% |
| LSTM | harga + cuaca + kalender + siklus tanggal | 1,243.57 | 1,563.21 | 3.54% | 2,378.86 | 3,063.66 | 4.83% |
| LSTM | harga saja | 989.35 | 1,209.70 | 2.36% | 1,744.21 | 2,391.98 | 3.48% |

## Arti metrik dan interpretasi

- **MAE (Mean Absolute Error)** adalah rata-rata besar selisih absolut antara prediksi dan harga aktual. Median MAE lintas komoditas untuk GRU harga saja sebesar Rp656/kg. Ini berarti median besar kesalahan absolut rata-rata per komoditas berada di sekitar Rp656/kg.
- **RMSE (Root Mean Squared Error)** juga mengukur selisih dalam Rp/kg, tetapi lebih menghukum kesalahan yang besar. Median RMSE konfigurasi terbaik adalah Rp881/kg.
- **MAPE (Mean Absolute Percentage Error)** menyatakan rata-rata besar kesalahan relatif terhadap harga aktual. Median MAPE konfigurasi terbaik adalah 1,98%; ini bukan klaim akurasi model sebesar 100% dikurangi MAPE.

Pada evaluasi ini, **GRU dengan harga saja** memiliki median terendah untuk ketiga metrik. Dibandingkan GRU harga saja, median error GRU dengan paket eksternal naik: MAE 43,2%, RMSE 38,2%, dan MAPE 24,5%. Pada LSTM, paket eksternal juga memiliki median yang lebih tinggi untuk ketiga metrik. Jadi, pada run ini penambahan paket tersebut belum memperbaiki hasil keseluruhan.

Paket eksternal menggabungkan cuaca, kalender, dan siklus tanggal sekaligus. Evaluasi ini tidak menunjukkan kontribusi masing-masing fitur secara terpisah dan tidak membuktikan bahwa fitur eksternal selalu merugikan pada komoditas atau periode lain.

## Batas interpretasi

- Hasil ini berasal dari satu pembagian holdout kronologis dan satu seed. Uji rolling-origin dan beberapa seed diperlukan untuk menilai kestabilan hasil.
- Prediksi dihitung untuk tujuh horizon pada origin harian yang tumpang tindih. Karena itu, banyak baris uji saling berkorelasi dan bukan observasi independen.
- Evaluasi ini membandingkan LSTM dan GRU, tetapi belum mencakup baseline Naive atau ARIMA.
- MAPE dapat menjadi tidak stabil bila harga aktual mendekati nol; harga PIHPS yang dipakai di sini positif.
- Hasil simulasi beli/tunda dihitung ulang dari ramalan baru, namun merupakan simulasi retrospektif dengan asumsi tetap, bukan penghematan aktual.

## Berkas hasil

- `model_comparison.csv`: 52 baris metrik per komoditas/model/fitur.
- `model_comparison_summary.csv`: ringkasan median dan rerata.
- `tabel_evaluasi_skripsi.csv`: tabel dengan nama kolom dan satuan untuk naskah.
- `forecasts.csv`: prediksi hasil pengujian untuk tujuh horizon.
- `purchase_simulation_summary.csv` dan `purchase_simulation_detail.csv`: simulasi rekomendasi yang dihitung ulang.
- Artefak model aktif `.h5` dan metadata `.json` tersimpan di folder `models/`.
