# Catatan sumber data penelitian Depok

## Harga komoditas

- Sumber: 91 workbook Excel PIHPS yang diberikan pengguna, diolah dari baris wilayah `Kota Depok`.
- Wilayah aktif: Kota Depok. Dataset Jawa Barat yang pernah dipakai sebelumnya bukan sumber untuk laporan/model saat ini.
- Nama komoditas diambil dari nama file. Tanggal mengikuti isi workbook untuk mengatasi nama file yang tahunnya tidak sesuai.
- `data/raw/prices.csv`: 20.631 observasi harga, 13 komoditas, rentang keseluruhan 2020-01-02–2026-10-21. Cakupan berbeda antar komoditas; Bawang Merah mulai 2021-01-04 dan Gula Pasir Lokal mulai 2022-01-03.
- Satuan harga dataset aktif: rupiah per kilogram (Rp/kg), sesuai konfirmasi pengguna.
- `data/processed/combined_daily.csv` adalah data harga harian yang sudah dibersihkan dan digabung dengan fitur eksternal.

## Cuaca historis aktif

- Sumber aktif: Open-Meteo Historical Weather API dengan model `ERA5` eksplisit, timezone `Asia/Jakarta`, diunduh menggunakan `scripts/download_weather_open_meteo_era5.py`.
- Waktu unduh API terakhir: `2026-11-03T19:31:53Z` (UTC; 4 Nov 2026 waktu Asia/Jakarta).
- URL API dan parameter lengkap disimpan di `data/processed/weather_openmeteo_era5_metadata.json`. Titik permintaan -6.3917, 106.8167 di-snap ke grid API -6.5, 106.75 pada elevasi 84 m. Ini reanalisis grid, bukan pengukuran stasiun BMKG.
- `data/raw/weather.csv` berisi kolom model `date,temp_c,temp_max_c,temp_min_c,rain_mm,wind_max_kmh,solar_mj_m2`, bersumber dari `temperature_2m_mean`, `temperature_2m_max`, `temperature_2m_min`, `precipitation_sum`, `wind_speed_10m_max`, dan `shortwave_radiation_sum`.
- Satuan: °C untuk suhu, mm untuk presipitasi, km/h untuk angin maksimum, dan MJ/m² untuk total radiasi gelombang pendek harian.
- Rentang 2020-01-01–2026-10-26: 2.491 tanggal harian, tanpa tanggal duplikat atau nilai kosong.
- CSV lama pengguna tersimpan sebagai `data/raw/weather_depok_harian_source.csv`; versi normalisasi sebelum penggantian ERA5 ada di `data/raw/weather_pre_era5_20261104.csv`. Keduanya bukan data aktif.
- Halaman Databoks yang dirujuk membedakan prakiraan BMKG dan rekam historis ERA5/Open-Meteo. Nilai proyek aktif diambil langsung dari API ERA5; prakiraan BMKG tidak digunakan.
- Workbook bulanan terdahulu tetap disimpan di `data/raw/weather_monthly_depok.csv` sebagai referensi, bukan fitur model aktif.
- NASA POWER lama disimpan di `data/raw/weather_nasa_depok_backup_20261102.csv`, bukan fitur aktif.

## Kalender aktif dan batas penggunaan

- Sumber: `data/raw/kalender_indonesia_2020_2026_source.csv`, CSV yang diberikan pengguna; sumber primer/URL kalender belum tercantum.
- `data/raw/calendar.csv` dinormalisasi oleh `scripts/prepare_calendar.py`; 2.557 tanggal berurutan tanpa duplikasi, 2020-01-01–2026-12-31.
- Fitur: `is_libur_nasional` (114 hari), `is_cuti_bersama` (50 hari), dan `is_weekend` (730 hari), dipetakan dari kolom sumber `is_libur_nasional`, `is_cuti_bersama`, dan `is_akhir_pekan`.
- Kolom `keterangan` pada CSV sumber memuat tanggal libur/cuti terkait Idulfitri. Pipeline membentuk `is_idul_fitri` dari keterangan yang menyebut Idulfitri/Lebaran dan memasukkannya sebagai fitur eksternal tersendiri. CSV tidak menandai periode Ramadan atau rentang hari menjelang Idulfitri.
- Jika data harga, cuaca, atau kalender berubah, jalankan `scripts/prepare_data.py`, latih ulang semua model, perbarui simulasi, dan regenerasi tabel/grafik.
