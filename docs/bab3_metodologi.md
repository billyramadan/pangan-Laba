# BAB III METODOLOGI PENELITIAN

## 3.1 Desain Penelitian

Penelitian ini termasuk jenis penelitian terapan (*applied research*) dengan metode kuantitatif, karena menghasilkan produk berupa model prediksi dan aplikasi yang diuji secara numerik. Desain penelitian mengikuti alur: pengumpulan data → pra-pemrosesan → pelatihan model LSTM dan GRU → evaluasi model → pengembangan aplikasi → uji coba aplikasi pada pelaku UMKM kuliner. Perbandingan dilakukan secara berpasangan: setiap arsitektur (LSTM, GRU) diuji dengan dua paket fitur (harga saja; harga + cuaca + kalender), sehingga diperoleh empat konfigurasi model yang dievaluasi pada data uji yang sama.

## 3.2 Variabel dan Sumber Data

### 3.2.1 Variabel Penelitian

| Jenis | Variabel | Keterangan |
|-------|----------|------------|
| Dependen | Harga komoditas pangan (Rp/kg) | Variabel yang diprediksi |
| Independen utama | Harga historis harian | Jendela 30 hari terakhir |
| Independen pendukung | Cuaca harian (curah hujan mm, suhu °C) | Data ERA5 via Open-Meteo |
| Independen pendukung | Kalender Indonesia | Libur nasional, cuti bersama, akhir pekan, penanda Idulfitri |
| Independen pendukung | Siklus waktu | Encoding sinus/kosinus hari dan bulan |

### 3.2.2 Sumber Data

1. **Data harga**: Pusat Informasi Harga Pangan Strategis (PIHPS) Kementerian Perdagangan, 13 komoditas pangan strategis di Kota Depok, periode 2020–2026, granularitas harian.
2. **Data cuaca**: Reanalisis ERA5 melalui Open-Meteo Historical Weather API untuk wilayah Depok, periode 1 Januari 2020–26 Oktober 2026, variabel curah hujan (*rain_mm*) dan suhu (*temp_c*).
3. **Data kalender**: Hari libur nasional, cuti bersama, akhir pekan, dan keterangan Idulfitri untuk Indonesia.

## 3.3 Lokasi dan Waktu Penelitian

Lokasi penelitian adalah Kota Depok, Provinsi Jawa Barat, dengan pertimbangan ketersediaan data PIHPS tingkat kota dan konsentrasi UMKM kuliner. Pengumpulan data dilakukan secara retrospektif dari sumber terbuka; uji coba aplikasi dilakukan bersama pelaku UMKM kuliner di Kota Depok pada kurun waktu penelitian berjalan. *(Jadwal rinci disesuaikan dengan kalender bimbingan.)*

## 3.4 Alat dan Bahan

**Perangkat lunak**: Python 3.13; pandas, NumPy, scikit-learn untuk pra-pemrosesan dan metrik; TensorFlow/Keras untuk arsitektur LSTM dan GRU; OpenPyXL untuk pembacaan workbook PIHPS; framework *HTTP server* Python untuk *backend* aplikasi; HTML/CSS/JavaScript (*vanilla*, Canvas API) untuk *frontend*.

**Perangkat keras**: komputer dengan *RAM* memadai untuk pelatihan *deep learning* (48 unit *recurrent* per model).

**Bahan data**: workbook Excel PIHPS Kota Depok; berkas CSV cuaca dan kalender.

## 3.5 Tahapan Penelitian

1. **Pengumpulan data**: unduh harga PIHPS 13 komoditas, cuaca ERA5, dan kalender Indonesia; simpan dalam format terstruktur.
2. **Pra-pemrosesan**: *merge* ketiga sumber berdasarkan tanggal; penanganan nilai hilang; penskalaan fitur (*scaler*) yang *fit* **hanya pada data latih** untuk mencegah *data leakage*; pembentukan jendela 30 hari sebagai masukan dan 7 hari sebagai target.
3. **Pembagian data**: kronologis, 80% awal untuk pelatihan dan 20% akhir untuk pengujian (tanpa pengacakan, menjaga urutan waktu).
4. **Pelatihan model**: LSTM dan GRU, masing-masing dua paket fitur; *early stopping* dengan patience 5; *seed* tetap 42 untuk reproduktibilitas.
5. **Evaluasi model**: MAE (Rp/kg), RMSE, dan MAPE pada data uji; perbandingan antar model dan antar paket fitur.
6. **Pengembangan aplikasi**: integrasi model tersimpan ke aplikasi web PanganLaba.
7. **Uji coba aplikasi**: percobaan oleh pelaku UMKM kuliner; pengumpulan umpan balik anonim.

## 3.6 Arsitektur Model

Kedua arsitektur menggunakan struktur yang identik agar perbandingan adil:

```
Input (30 hari × fitur)
   ↓
LSTM/GRU: 48 unit
   ↓
Dropout 0,15
   ↓
Dense 32 (ReLU)
   ↓
Output: 7 langkah (7 hari ke depan)
```

- **Optimizer**: Adam
- **Fungsi loss**: *Mean Squared Error* (MSE)
- **Pelatihan**: maksimum 15–30 epoch, *early stopping* patience 5
- **Reproduktibilitas**: *seed* 42, *scaler* dari data latih

Perbedaan satu-satunya antara LSTM dan GRU adalah tipe sel *recurrent* (tiga gerbang pada LSTM vs dua gerbang pada GRU), sesuai teori pada Bab II.

## 3.7 Evaluasi Model

Evaluasi menggunakan tiga metrik (persamaan pada Bab II):

- **MAE** (Rp/kg): rata-rata selisih absolut aktual vs prediksi
- **RMSE** (Rp/kg): penalti lebih besar pada kesalahan besar
- **MAPE** (%): kesalahan relatif terhadap harga aktual

Hasil per model dan per komoditas dirangkum dalam tabel metrik, dilengkapi median lintas komoditas. Pengaruh fitur eksternal dinilai dari selisih MAE paket fitur eksternal terhadap MAE paket fitur harga saja pada pasangan komoditas–model yang sama.

**Ambang rekomendasi beli/tunda**: perubahan prediksi ≥ +5% → tunda beli; ≤ −5% → beli; di antara keduanya → beli sesuai kebutuhan.

## 3.8 Pengembangan Aplikasi PanganLaba

Aplikasi dibangun sebagai produk *web* yang menyajikan hasil prediksi menjadi keputusan usaha. Arsitektur aplikasi:

- **Backend**: Python (*HTTP server*), *endpoint* REST untuk prediksi, kalkulator laba, simulasi belanja, riwayat, dan otentikasi Google (OAuth 2.0).
- **Frontend**: HTML/CSS/JavaScript tanpa *framework*, grafik digambar pada Canvas API agar ringan di perangkat entry-level.
- **Penyimpanan**: SQLite, terpisah per akun; data pengguna tidak tercampur.

Rincian fitur yang diuji:

| Modul | Fungsi |
|-------|--------|
| Ringkasan usaha | Harga PIHPS terakhir, rerata prediksi 7 hari, saran beli/tunda |
| Kalkulator laba menu | Modal per porsi, omzet, laba bersih, margin, titik impas, skenario harga prediksi |
| Simulasi belanja | Perbandingan belanja rutin vs strategis (tunda) per siklus |
| Tanya PanganLaba | Jawaban bahasa sehari-hari dari data aplikasi |
| Riwayat & unduh | Rekap laba-rugi, ekspor CSV |

## 3.9 Uji Coba Aplikasi pada UMKM

Uji coba dilakukan kepada pelaku UMKM kuliner di Kota Depok *(jumlah dan kriteria responden disesuaikan dengan desain uji coba: misalnya 5–10 pelaku usaha yang bersedia)*. Setiap peserta menjalani dua tugas:

1. **Tugas kalkulator**: menghitung modal dan laba satu menu.
2. **Tugas dashboard**: mencari harga aktual dan prediksi suatu komoditas.

Yang diukur: keberhasilan tugas (mandiri / terbantu / gagal), waktu penyelesaian (menit), kemudahan, kejelasan hasil, manfaat (skala 1–5), kesesuaian hitungan dengan manual, dan kesiap-pakian ulang. Umpan balik dicatat secara anonim (kode sesi, tanpa nama/kontak) setelah persetujuan peserta.

## 3.10 Definisi Operasional

| Istilah | Definisi operasional |
|---------|---------------------|
| Prediksi harga | Keluaran model LSTM/GRU 7 hari ke depan, satuan Rp/kg |
| Kebutuhan belanja | Kebutuhan bahan baku untuk satu siklus produksi |
| Modal per porsi | Jumlah (gram bahan × harga/kg) untuk satu porsi menu |
| Saran beli/tunda | Rekomendasi berdasarkan ambang perubahan prediksi ±5% |
| Titik impas | Jumlah porsi saat omzet sama dengan total biaya |

## 3.11 Teknik Analisis Data

Analisis terdiri atas dua lapis: (1) **kuantitatif** — perbandingan MAE/RMSE/MAPE keempat konfigurasi model dan uji pengaruh fitur eksternal; (2) **deskriptif** — rekap hasil uji coba UMKM (frekuensi keberhasilan tugas, rata-rata skor kemudahan/kejelasan/manfaat) untuk menilai kemanfaatan aplikasi.
