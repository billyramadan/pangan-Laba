# Hasil Evaluasi LSTM dan GRU

**Pembaruan data:** 10 November 2026  
**Data harga:** 20,824 observasi PIHPS Kota Depok, 16 nama komoditas, 2020-01-02–2026-11-10.  
**Eksperimen:** 52 kombinasi pada 13 komoditas yang memiliki riwayat cukup (LSTM/GRU × harga saja/fitur eksternal). Tiga seri baru—Gula Pasir, Cabai Merah Besar, dan Cabai Merah Keriting—baru memiliki 15 observasi dan belum dimasukkan ke evaluasi maupun model aktif.  
**Konfigurasi:** jendela historis 30 hari, horizon prediksi 7 hari, split kronologis 80:20, maksimum 15 epoch pada pelatihan terbaru. Rentang target uji: 2025-06-16–2026-11-10.

Setelah evaluasi, model operasional dashboard di-fit ulang memakai seluruh histori yang tersedia per komoditas. Skor pada tabel tetap dihitung dari split uji kronologis, bukan dari model hasil fit penuh. Cakupan fit model final tercatat pada `reports/final_models_manifest.csv`.

## Ringkasan metrik median lintas komoditas

| Model | Fitur | Median MAE (Rp/kg) | Median RMSE (Rp/kg) | Median MAPE (%) |
|---|---|---:|---:|---:|
| GRU | harga + cuaca + kalender + siklus tanggal | 1,278.35 | 2,510.16 | 4.31 |
| GRU | harga saja | 976.59 | 2,318.43 | 3.48 |
| LSTM | harga + cuaca + kalender + siklus tanggal | 1,461.90 | 2,883.28 | 6.57 |
| LSTM | harga saja | 1,421.30 | 2,632.62 | 4.76 |

## Cara membaca

MAE dan RMSE dinyatakan dalam rupiah per kilogram (Rp/kg); MAPE dinyatakan dalam persen. Pada run terbaru, GRU dengan harga saja memiliki median error terendah. Paket fitur eksternal mencakup cuaca, kalender, dan siklus tanggal sekaligus, sehingga hasil ini tidak mengisolasi kontribusi satu fitur.

Hasil lengkap per komoditas ada di `reports/model_comparison.csv` dan tabel skripsi di `reports/tabel_evaluasi_skripsi.csv`. Draf metode, batasan, grafik, dan hasil yang lebih lengkap ada di `reports/BAHAN_SKRIPSI_HASIL.md`. Prediksi ini merupakan evaluasi historis, bukan jaminan harga aktual.
