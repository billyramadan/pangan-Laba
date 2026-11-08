# Ringkasan temuan proyek dari awal

Dokumen ini menyatukan temuan data, evaluasi LSTM/GRU, dan simulasi rekomendasi beli/tunda. Angka di bawah mengacu pada keluaran model terbaru yang tersimpan di folder `reports/`.

## 1. Data dan ruang lingkup penelitian

Penelitian menggunakan harga PIHPS Kota Depok untuk 13 komoditas, dengan 20.631 observasi pada rentang 2 Januari 2020 sampai 21 Oktober 2026. Satuan harga yang dipakai adalah rupiah per kilogram (Rp/kg). Fitur cuaca historis berasal dari ERA5 melalui Open-Meteo, sedangkan kalender berasal dari CSV yang diberikan pengguna. Kalender memuat libur nasional, cuti bersama, akhir pekan, dan 36 tanggal dengan keterangan terkait Idulfitri. Penanda Idulfitri sudah diproses sebagai fitur model.

Data dibersihkan dan disejajarkan per tanggal sebelum pelatihan. Setelah tanggal harian dilengkapi, hasil gabungan berisi 31.185 baris. Model membandingkan LSTM dan GRU dengan dua jenis masukan: fitur harga saja, serta fitur harga bersama cuaca, kalender, dan siklus tanggal.

## 2. Arti selisih harga dan aturan rekomendasi

Pada dashboard, perubahan prediksi dihitung dengan membandingkan rata-rata harga prediksi tujuh hari dengan harga acuan saat ini:

```text
perubahan prediksi (%) = (rata-rata prediksi 7 hari / harga acuan - 1) × 100%
```

Jika kenaikan mencapai 5% atau lebih, sistem memberi saran “Beli sekarang”. Jika penurunan mencapai 5% atau lebih, sistem memberi saran “Tunda dulu”. Di antara kedua batas itu, saran yang tampil adalah “Beli sesuai kebutuhan”. Ambang ini merupakan aturan prototipe dan masih perlu disetujui dosen pembimbing.

Simulasi retrospektif memakai siklus pembelian tujuh hari dan volume satu kilogram per transaksi. Baseline membeli pada hari pertama siklus. Strategi boleh menunda pembelian ketika prediksi menunjukkan penurunan sekurangnya 5%, dengan batas penundaan dua hari. Biaya strategi kemudian dibandingkan dengan harga aktual pada hari pembelian. Simulasi terbaru mencakup 3.460 siklus, dengan 322 siklus mengalami penundaan. Median selisih biaya per komoditas adalah 0% untuk semua kombinasi model/fitur; rata-ratanya sekitar 0,01–0,03%. Hasil ini belum menunjukkan penghematan yang konsisten dan bukan bukti penghematan nyata.

## 3. Temuan evaluasi model

Data dibagi kronologis: 80% bagian awal untuk pelatihan dan 20% bagian akhir untuk pengujian. Setiap model memakai riwayat 30 hari untuk memprediksi tujuh hari. Metrik yang dihitung adalah MAE dan RMSE dalam Rp/kg serta MAPE dalam persen. Ringkasan lintas komoditas memakai median agar komoditas dengan harga tinggi tidak mendominasi.

| Model | Fitur | Median MAE (Rp/kg) | Median RMSE (Rp/kg) | Median MAPE (%) |
|---|---|---:|---:|---:|
| GRU | Harga saja | 697,77 | 951,43 | 1,59 |
| GRU | Harga + cuaca + kalender + siklus tanggal | 789,82 | 1.046,29 | 1,87 |
| LSTM | Harga saja | 779,91 | 1.037,65 | 1,84 |
| LSTM | Harga + cuaca + kalender + siklus tanggal | 1.032,17 | 1.341,02 | 3,74 |

Pada hasil ini, fitur eksternal menghasilkan MAE yang lebih rendah daripada fitur harga saja pada 1 dari 13 komoditas untuk LSTM dan 2 dari 13 komoditas untuk GRU. Secara median, fitur harga saja lebih baik untuk kedua model. Karena paket eksternal menggabungkan cuaca, kalender, dan siklus tanggal, hasil ini tidak menunjukkan pengaruh masing-masing fitur secara terpisah.

## 4. Batas interpretasi dan langkah selanjutnya

- Fitur kalender Idulfitri sudah digunakan. CSV belum memberi penanda periode Ramadan atau rentang hari menjelang Idulfitri.
- Model memakai fitur cuaca dan kalender dari riwayat 30 hari. Nilai cuaca/kalender untuk tujuh hari yang diprediksi belum diberikan sebagai masukan masa depan tersendiri.
- Simulasi memakai volume tetap 1 kg, ambang 5%, dan batas tunda dua hari; belum memasukkan stok, kebutuhan usaha, biaya simpan, transportasi, atau mutu bahan.
- Minta persetujuan dosen pembimbing untuk aturan rekomendasi dan skenario simulasi sebelum menjadikan hasilnya sebagai kesimpulan penelitian.
- Hasil evaluasi tersedia di `model_comparison.csv`, rincian prediksi di `forecasts.csv`, dan simulasi di `purchase_simulation_summary.csv` serta `purchase_simulation_detail.csv`.

## Sumber data

- Harga: workbook PIHPS untuk wilayah Kota Depok yang diberikan pengguna.
- Cuaca historis: Open-Meteo Historical Weather API dengan model ERA5; data reanalisis grid, bukan observasi stasiun BMKG.
- Kalender: `data/raw/kalender_indonesia_2020_2026_source.csv`, CSV yang diberikan pengguna.
