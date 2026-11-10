# Bahan hasil dan evaluasi model untuk skripsi

> Draf kerja untuk ditinjau dan diselaraskan dengan arahan dosen pembimbing. Jangan menyalin tanpa memeriksa metode, satuan, dan provenance sumber data.

## Ringkasan data

- Harga PIHPS Kota Depok: 20,824 observasi, 16 komoditas, 2020-01-02–2026-11-10.
- Cuaca harian aktif: 2,491 tanggal, 2020-01-01–2026-10-26; grid ERA5 lat -6.5, lon 106.75, elevasi 84.0 m.
- Evaluasi: 52 kombinasi (13 komoditas × 2 model × 2 set fitur). Rentang target-uji antar-komoditas: 2025-06-16–2026-11-10.
- Harga PIHPS Kota Depok bersatuan rupiah per kilogram (Rp/kg), sesuai konfirmasi pengguna. Cuaca aktif diunduh langsung dari Open-Meteo Historical Weather API dengan model ERA5 eksplisit dan timezone Asia/Jakarta; pengambilan terakhir 2026-11-03T19:31:53+00:00 UTC. Satuan cuaca: suhu °C, presipitasi mm, angin km/h, dan radiasi MJ/m².

## Metode evaluasi

Data setiap komoditas diurutkan berdasarkan tanggal dan dibagi kronologis 80% pelatihan / 20% pengujian. Semua varian model pada komoditas yang sama menggunakan batas waktu dan urutan uji yang sama. Model menerima jendela 30 hari untuk memprediksi tujuh hari berikutnya. LSTM dan GRU masing-masing diuji memakai fitur harga (harga, lag 1, lag 7, rerata 7 dan 30 hari) serta paket eksternal yang menambahkan enam variabel cuaca ERA5, indikator libur nasional/cuti bersama/akhir pekan, penanda tanggal dengan keterangan Idulfitri, dan empat fitur siklus hari/bulan. Indikator kalender yang masuk ke model berasal dari jendela historis 30 hari; kalender masa depan tidak diberikan sebagai input decoder terpisah. CSV tidak menandai periode Ramadan atau rentang hari menjelang Idulfitri.

Pelatihan memakai maksimum 30 epoch, validasi 10% dari bagian pelatihan yang paling akhir, dan early stopping dengan patience 5. Jumlah epoch aktual pada run ini: 13–15 (median 15.0). Scaler dipasang pada data latih saja.

Setelah evaluasi, 52 model operasional di-fit ulang memakai seluruh urutan historis yang tersedia per komoditas. Model final ini untuk prediksi dashboard dan tidak digunakan untuk menghitung metrik holdout. Rincian rentang fit ada di `final_models_manifest.csv`.

MAE dan RMSE dilaporkan dalam rupiah per kilogram (Rp/kg); MAPE dalam persen. Tabel laporan menggabungkan error dari tujuh horizon dan semua origin harian pada bagian uji. Origin/horizon tumpang tindih sehingga error antarbaris berkorelasi. Grafik H+1 di bawah mengambil prediksi satu hari ke depan pada setiap origin uji agar seri aktual/prediksi bisa dibaca tanpa mencampur horizon.

## Ringkasan metrik lintas komoditas

Median antarkomoditas lebih layak untuk ringkasan karena nominal harga dan skala error berbeda antar-komoditas. Nilai mean tetap tersedia dalam file ringkasan.

| Model | Fitur | Median MAE (Rp/kg) | Median RMSE (Rp/kg) | Median MAPE (%) |
|---|---|---:|---:|---:|
| GRU | harga + cuaca + kalender + siklus tanggal | 1,278.353 | 2,510.157 | 4.315 |
| GRU | harga saja | 976.588 | 2,318.425 | 3.475 |
| LSTM | harga + cuaca + kalender + siklus tanggal | 1,461.901 | 2,883.281 | 6.574 |
| LSTM | harga saja | 1,421.302 | 2,632.625 | 4.760 |

Paket eksternal (cuaca, kalender, dan siklus tanggal) menghasilkan MAE lebih rendah dibanding fitur harga saja pada 1 dari 13 komoditas untuk LSTM dan 0 dari 13 untuk GRU. Karena paket menggabungkan tiga kelompok fitur sekaligus, hasil ini tidak mengisolasi pengaruh cuaca atau kalender secara terpisah.

## Sumber data

Harga menggunakan workbook PIHPS yang diolah untuk baris Kota Depok. Cuaca aktif diambil langsung dari Open-Meteo Historical Weather API menggunakan model ERA5 dan parameter lokasi/waktu yang tersimpan di `data/processed/weather_openmeteo_era5_metadata.json`. Koordinat permintaan (-6.3917, 106.8167) dipetakan API ke grid ERA5 (-6.5, 106.75), elevasi 84 m. Ini data reanalisis grid untuk satu titik representatif, bukan pengukuran stasiun BMKG atau rata-rata seluruh Kota Depok. Variabel yang digunakan: suhu rata-rata/maksimum/minimum, presipitasi harian, angin maksimum, dan radiasi gelombang pendek. Rujukan Databoks membedakan prakiraan BMKG dari rekam historis ERA5/Open-Meteo; seri aktif proyek sekarang berasal langsung dari API Open-Meteo.

## Keterbatasan

- Ini satu pembagian holdout kronologis per komoditas, bukan beberapa fold rolling-origin atau uji pada wilayah lain.
- Cakupan tanggal harga berbeda antar-komoditas; karena itu, tanggal uji tidak sama antar-komoditas, meskipun sama antarvarian dalam komoditas yang sama.
- Satuan harga aktif dikonfirmasi sebagai Rp/kg; pastikan workbook komoditas yang ditambahkan tetap menggunakan satuan yang sama.
- ERA5 merupakan reanalisis grid pada satu titik, bukan pembacaan stasiun atau representasi seragam seluruh Kota Depok.
- CSV kalender diberikan pengguna dan memuat libur nasional, cuti bersama, akhir pekan, serta keterangan tanggal Idulfitri. Penanda Ramadan dan rentang hari menjelang Idulfitri tidak tersedia. Pada model saat ini kalender masa depan juga tidak diberikan langsung kepada decoder.
- Simulasi beli/tunda memakai siklus dan volume tetap; lihat `SIMULASI_REKOMENDASI.md`. Hasilnya bukan penghematan aktual.
- Hasil angka bergantung pada konfigurasi training dan satu random seed; lakukan pengujian stabilitas tambahan bila diminta pembimbing.

## Referensi sumber

- Open-Meteo. [Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api). Parameter unduhan yang dipakai tersimpan di `data/processed/weather_openmeteo_era5_metadata.json`.
- Bank Indonesia. [Pusat Informasi Harga Pangan Strategis Nasional](https://www.bi.go.id/hargapangan/Website). Workbook harga PIHPS wilayah Kota Depok diberikan pengguna.
- Katadata Databoks. [BMKG: Kota Depok Hujan Ringan Malam Ini](https://databoks.katadata.co.id/layanan-konsumen-kesehatan/statistik/a90d7884c8c49df/bmkg-kota-depok-hujan-ringan-malam-ini). Rujukan konteks yang membedakan prakiraan BMKG dan seri historis ERA5/Open-Meteo.

## Berkas tabel dan gambar

- Tabel lengkap per komoditas/model/fitur: `tabel_evaluasi_skripsi.csv` (52 baris).
- Ringkasan metrik: `model_comparison_summary.csv`.
- Grafik median metrik: `figures/ringkasan_metrik_model.png`.
- Grafik aktual vs prediksi H+1 per komoditas: `FIGURES_INDEX.md`.

## Ringkasan simulasi beli/tunda

Parameter standar: siklus 7 hari, volume 1 kg per transaksi, harga Rp/kg, ambang penundaan 5%, maksimal tunda 2 hari. Median/rerata dihitung lintas-komoditas; hasil ini simulasi retrospektif, bukan penghematan aktual.

| Model | Fitur | Median selisih (%) | Rerata selisih (%) |
|---|---|---:|---:|
| GRU | harga + cuaca + kalender + siklus tanggal | 0.00 | -0.07 |
| GRU | harga saja | 0.00 | -0.06 |
| LSTM | harga + cuaca + kalender + siklus tanggal | 0.00 | -0.01 |
| LSTM | harga saja | 0.00 | -0.12 |
