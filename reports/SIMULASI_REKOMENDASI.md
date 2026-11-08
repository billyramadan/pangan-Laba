# Protokol dan hasil awal simulasi beli/tunda

## Status

Dokumen ini mencatat **protokol simulasi prototipe** untuk ditinjau bersama dosen pembimbing. Asumsi belum dianggap disetujui. Hasilnya tidak membuktikan penghematan nyata.

## Aturan simulasi

1. Gunakan prediksi pada bagian uji untuk setiap model, fitur, dan komoditas.
2. Susun siklus pembelian tetap sepanjang 7 hari. Baseline membeli pada hari pertama setiap siklus.
3. Pada strategi, hitung rata-rata prediksi 7 hari relatif terhadap harga acuan di tanggal keputusan.
4. Jika rata-rata prediksi turun sekurangnya 5% (`perubahan <= -5%`), tunda satu hari dan nilai kembali prediksi pada hari berikutnya. Batas standar penundaan adalah 2 hari.
5. Beli saat rekomendasi tidak lagi “Tunda dulu”, atau tetap beli ketika batas penundaan tercapai.
6. Asumsikan satu transaksi dengan volume tetap dalam kilogram pada setiap siklus. Harga PIHPS pada project dinyatakan dalam Rp/kg; volume default satu kilogram dan dapat diubah dari kontrol dashboard.
7. Keputusan hanya memakai prediksi yang tersedia pada tanggal itu. Biaya retrospektif memakai harga acuan aktual pada tanggal pembelian.

Rumus untuk setiap komoditas dan varian:

```text
biaya baseline (Rp) = jumlah(harga aktual (Rp/kg) pada awal siklus × volume (kg))
biaya strategi (Rp) = jumlah(harga aktual (Rp/kg) pada tanggal beli strategi × volume (kg))
selisih biaya = biaya baseline − biaya strategi
persentase selisih = selisih biaya (Rp) ÷ biaya baseline (Rp) × 100%
```

Nilai positif berarti strategi lebih murah pada simulasi, nilai negatif berarti lebih mahal.

## Hasil awal

Hasil memakai prediksi terbaru dari model dengan data ERA5 dan kalender, 13 komoditas, 4 kombinasi model/fitur, dan 865 siklus per kombinasi (3.460 siklus keseluruhan). Dengan parameter standar volume 1 kg dan penundaan maksimum 2 hari, 322 transaksi ditunda.

| Model | Fitur | Median selisih per komoditas | Rerata selisih per komoditas |
|---|---|---:|---:|
| GRU | Harga saja | 0,00% | 0,02% |
| GRU | Harga + cuaca + kalender + siklus tanggal | 0,00% | 0,01% |
| LSTM | Harga saja | 0,00% | 0,03% |
| LSTM | Harga + cuaca + kalender + siklus tanggal | 0,00% | 0,02% |

Median 0% menunjukkan bahwa sebagian besar komoditas tidak memperoleh perubahan biaya pada aturan ini. Ada komoditas dengan selisih negatif maupun positif. Jadi, hasil awal belum menunjukkan manfaat penghematan yang konsisten.

## Batas interpretasi

- Harga pada project dinyatakan dalam Rp/kg dan volume simulasi dalam kg. Jangan menjumlahkan biaya nominal lintas-komoditas sebagai satu total belanja UMKM.
- Asumsi belum memasukkan kebutuhan riil, stok, kualitas, biaya penyimpanan/transportasi, atau biaya transaksi.
- Simulasi ini mengukur selisih harga pada data uji historis, bukan penghematan aktual atau bukti bahwa strategi akan selalu lebih murah.
- Periode uji dan jumlah siklus tiap komoditas tersedia pada `model_comparison.csv` dan `purchase_simulation_summary.csv`.

## Berkas hasil

- `purchase_simulation_summary.csv`: ringkasan per komoditas/model/fitur.
- `purchase_simulation_detail.csv`: rincian tanggal dan harga untuk setiap siklus.
- `forecasts.csv`: prediksi tujuh hari yang menjadi masukan keputusan.

Sebelum menjadikan metode dan hasil ini sebagai kesimpulan skripsi, konfirmasikan definisi siklus, volume, ambang 5%, dan batas penundaan dengan dosen pembimbing.
