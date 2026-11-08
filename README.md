# Prediksi Harga Komoditas Pangan Strategis

**Judul:** Prediksi Harga Komoditas Pangan Strategis Menggunakan LSTM dan GRU dengan Fitur Eksternal untuk Mendukung Pembelian Bahan Baku UMKM Kuliner.

Proyek ini membandingkan LSTM dan GRU untuk memprediksi harga harian komoditas pangan strategis. Setiap model diuji dengan fitur harga saja dan fitur eksternal. Model memakai 30 hari pengamatan terakhir untuk memprediksi 7 hari berikutnya. Prakiraan digunakan sebagai pertimbangan waktu pembelian bahan baku; sistem ini tidak menghitung jumlah stok atau kebutuhan resep.

## Isi proyek

- `src/pangan_forecast/data.py`: validasi, penggabungan, dan pembersihan data.
- `src/pangan_forecast/features.py`: fitur harga, cuaca, dan kalender.
- `src/pangan_forecast/models.py`: eksperimen LSTM/GRU dengan/ tanpa fitur eksternal.
- `src/pangan_forecast/recommend.py`: aturan rekomendasi pembelian.
- `scripts/`: pembersihan, pelatihan, dan pembuatan data demo sintetis.
- `scripts/prepare_calendar.py`: menormalisasi kalender sumber ke indikator hari libur nasional, cuti bersama, akhir pekan, dan label keterangan Idulfitri.
- `data/raw/weather.csv`: data cuaca harian Depok yang sudah dinormalisasi untuk model.
- `data/raw/weather_depok_harian_source.csv`: salinan CSV cuaca harian lama dari pengguna.
- `data/raw/weather_pre_era5_20261104.csv`: salinan seri aktif sebelum diganti dengan ERA5 langsung, disimpan untuk pelacakan sumber.
- `data/raw/kalender_indonesia_2020_2026_source.csv`: CSV kalender asli yang diberikan pengguna; versi normalisasi dipakai dari `data/raw/calendar.csv`.
- `data/raw/weather_monthly_depok.csv`: sumber suhu maksimum bulanan terdahulu, disimpan sebagai referensi dan bukan fitur aktif.
- `scripts/download_weather_depok_nasa.py`: skrip alternatif NASA POWER; bukan sumber cuaca aktif saat ini. `scripts/download_weather_nasa.py` adalah skrip lama untuk Jawa Barat.
- `app.py`: dashboard Streamlit untuk melihat evaluasi dan rekomendasi.
- `data/`: tempat meletakkan data mentah dan hasil olahan.
- `models/`: model terlatih dalam format HDF5 dan metadata scaler. File `.keras` lama mungkin berasal dari eksperimen sebelumnya; dashboard memakai model yang tercatat pada laporan terbaru.
- `reports/`: hasil evaluasi dari data proyek saat ini.
- `reports/model_comparison.csv`: metrik setiap komoditas dan varian; `reports/model_comparison_summary.csv`: ringkasan mean/median lintas komoditas.
- `scripts/simulate_recommendations.py`: membuat `reports/purchase_simulation_summary.csv` dan `reports/purchase_simulation_detail.csv` dari prediksi pada data uji.
- `reports/SIMULASI_REKOMENDASI.md`: protokol, asumsi, ringkasan hasil awal, dan batas interpretasi.
- `scripts/create_thesis_materials.py`: membuat tabel evaluasi siap olah, grafik aktual-vs-prediksi H+1, grafik ringkasan, serta draf ringkasan metode/hasil/keterbatasan.
- `reports/BAHAN_SKRIPSI_HASIL.md` dan `reports/FIGURES_INDEX.md`: draf narasi hasil dan indeks grafik.

## Mulai

Gunakan Python 3.10 atau 3.11. Buat virtual environment, lalu pasang paket:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Untuk mencoba alur tanpa data resmi, buat data sintetis yang ditandai jelas sebagai demo:

```bash
python scripts/make_demo_data.py
python scripts/prepare_data.py
python scripts/train.py --epochs 15
```

Data harga PIHPS Kota Depok, cuaca historis ERA5 dari Open-Meteo, dan kalender Indonesia dari CSV yang diberikan pengguna tersedia pada `data/raw/`. Kalender mencakup libur nasional, cuti bersama, akhir pekan, dan penanda tanggal yang keterangannya memuat Idulfitri. CSV ini tidak memberi penanda periode Ramadan atau hari-hari menjelang Idulfitri. Jangan gabungkan data demo dan data penelitian. Jalankan dashboard setelah model tersimpan:

```bash
streamlit run app.py
```

Dashboard menyediakan bagian **Unggah data dan latih ulang model**. Unggah langsung satu atau beberapa workbook Excel PIHPS format “Tabel Harga Berdasarkan Komoditas”. Di setiap workbook, pilih baris provinsi/kota/pasar dan isi nama komoditas karena nama komoditas tidak tercantum pada tabel ekspor. Untuk file tahunan, gunakan baris wilayah yang sama. File cuaca historis dan kalender CSV bisa ditambahkan secara opsional. Workbook sumber disimpan terpisah di `data/uploads/`, lalu hasil pelatihan memperbarui folder `models/` dan `reports/`.

Setelah melatih ulang model, perbarui laporan simulasi dengan `python scripts/simulate_recommendations.py`, lalu buat ulang tabel/grafik skripsi dengan `python scripts/create_thesis_materials.py`. Dashboard juga menghitung simulasi untuk komoditas/model/fitur yang sedang dipilih dan menyediakan unduhan CSV.

## Format data

### Data penelitian

Data harga PIHPS adalah data utama dan harus memiliki tanggal, nama komoditas, harga numerik, wilayah/pasar, serta satuan yang konsisten. Untuk dataset aktif project ini, pengguna mengonfirmasi harga dinyatakan dalam rupiah per kilogram (Rp/kg). Simpan sebagai `data/raw/prices.csv` dengan kolom `date,commodity,price,location`; `location` dapat dihilangkan jika hanya ada satu wilayah. Satu baris mewakili satu komoditas, lokasi, dan tanggal.

Agar pengujian fitur eksternal bermakna, siapkan juga data historis yang tanggalnya selaras dengan data harga:

- `data/raw/weather.csv`: data harian `date,temp_c,temp_max_c,temp_min_c,rain_mm,wind_max_kmh,solar_mj_m2` untuk 1 Januari 2020–26 Oktober 2026; 2.491 tanggal tanpa duplikasi atau nilai kosong.
- `data/raw/weather_depok_harian_source.csv`: CSV harian lama yang diberikan pengguna; bukan seri aktif setelah penggantian ke ERA5 langsung.
- `data/raw/weather_pre_era5_20261104.csv`: backup seri aktif lama; tidak dipakai pada hasil evaluasi terbaru.
- `data/raw/weather_monthly_depok.csv`: sumber bulanan terdahulu (82 bulan, Januari 2020–Oktober 2026), disimpan sebagai referensi, bukan lagi fitur model aktif.
- `data/raw/calendar.csv`: 2.557 tanggal dari 2020-01-01 sampai 2026-12-31, dengan kolom `date,is_libur_nasional,is_cuti_bersama,is_weekend,is_idul_fitri` (penanda 0/1). `is_idul_fitri` diturunkan dari teks `keterangan` yang menyebut Idul Fitri/Lebaran; ini mencakup libur/cuti yang terkait, tidak menandai periode Ramadan atau beberapa hari sebelum Idulfitri.

Hari dalam minggu dan bulan dihitung otomatis. Cuaca historis aktif diunduh langsung dari Open-Meteo Historical Weather API dengan model `era5`, timezone Asia/Jakarta, dan variabel suhu, presipitasi, angin, serta radiasi. Titik permintaan (-6.3917, 106.8167) di-snap ke grid ERA5 (-6.5, 106.75), elevasi 84 m; ini reanalisis grid, bukan observasi stasiun BMKG. Kalender mencakup libur nasional, cuti bersama, akhir pekan, dan tanggal dengan keterangan Idulfitri. Metadata cuaca tercatat di `data/processed/weather_openmeteo_era5_metadata.json`.

PIHPS menyediakan tabel harga dan unduhan laporan melalui portal resminya. Data harga proyek ini dipilih untuk wilayah Kota Depok. Ambil laporan manual sesuai wilayah, komoditas, pasar, dan periode; cocokkan nama kolomnya ke format di atas. Hindari mengambil data dengan scraping. Data cuaca historis proyek menggunakan ERA5 melalui Open-Meteo; jika data atau periode cuaca diperbarui, sesuaikan kolom dan satuannya, lalu latih ulang model. Catat sumber, periode, cakupan wilayah, satuan, dan izin pemakaian di `data/SOURCE_NOTES.md`.

CSV cuaca aktif diunduh langsung melalui [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api), dengan model ERA5 eksplisit. Rujukan konteks yang diberikan pengguna: [Databoks—BMKG: Kota Depok Hujan Ringan Malam Ini](https://databoks.katadata.co.id/layanan-konsumen-kesehatan/statistik/a90d7884c8c49df/bmkg-kota-depok-hujan-ringan-malam-ini). Databoks menyebut BMKG untuk prakiraan dan ERA5/Open-Meteo untuk catatan historis; nilai CSV aktif sekarang berasal dari API ERA5 langsung, bukan prakiraan BMKG atau CSV lama.

## Metode dan batas interpretasi

Split data dilakukan secara kronologis (80% latih, 20% uji), bukan acak. Untuk setiap komoditas, semua varian memakai rentang uji dan urutan target yang sama. Model memakai jendela 30 hari untuk memprediksi 7 hari; epoch maksimum 30 dengan early stopping berdasarkan 10% bagian akhir data latih. Laporan mencatat rentang tanggal target latih/uji, epoch aktual, dan jumlah urutan. Metrik MAE, RMSE, dan MAPE dihitung dengan menggabungkan seluruh langkah prediksi tujuh hari dari setiap origin uji; karena jendela prediksi saling tumpang tindih, kesalahan antarbaris tidak independen. Dashboard menampilkan median metrik lintas komoditas agar komoditas berharga tinggi tidak mendominasi ringkasan. Empat eksperimen dibandingkan: LSTM dan GRU masing-masing dengan fitur harga saja dan paket eksternal yang menambahkan cuaca, kalender libur/cuti/akhir pekan/Idulfitri, serta siklus hari/bulan. Paket ini mencampur beberapa kelompok fitur, sehingga pengaruh cuaca atau kalender tidak terisolasi. Penanda Ramadan atau rentang hari menjelang Idulfitri belum tersedia. MAPE dapat menyesatkan jika harga mendekati nol.

Rekomendasi membandingkan rerata harga prakiraan tujuh hari dengan harga terakhir. Jika kenaikan prakiraan melewati ambang 5%, sistem menyarankan “beli sekarang”; jika perubahan di bawah −5%, “tunda dulu”; selain itu “beli sesuai kebutuhan”. Ini alat bantu sederhana, belum memperhitungkan stok, biaya penyimpanan, kualitas, pemasok, maupun ketidakpastian prediksi, sehingga bukan keputusan otomatis.

Simulasi retrospektif membandingkan pembelian pada hari pertama setiap siklus 7 hari dengan strategi yang boleh menunda pembelian hingga 2 hari apabila rekomendasi dari rerata prakiraan 7 hari adalah “tunda dulu”. Keputusan hanya menggunakan prediksi; biaya dihitung dari harga aktual di tanggal pembelian. Harga menggunakan Rp/kg dan volume diasumsikan tetap dalam kilogram per transaksi (default 1 kg). Dashboard memungkinkan volume dan batas tunda diubah serta mengunduh rincian simulasi. Hasil ini adalah perbedaan harga pada data uji, bukan bukti penghematan nyata, karena belum memasukkan stok, biaya simpan/transaksi, perubahan kebutuhan, atau risiko mutu.

Data demo dibangkitkan secara sintetis dan hanya untuk memeriksa alur teknis. Jangan menggunakannya sebagai hasil penelitian atau klaim kinerja pasar.
