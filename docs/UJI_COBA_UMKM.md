# Panduan Uji Kalkulator dan Dashboard ke UMKM

## Tujuan

Menguji apakah pemilik/pengelola/pekerja UMKM kuliner dapat memakai kalkulator modal menu dan memahami dashboard harga pangan. Uji ini mengumpulkan bukti penggunaan dan masukan; bukan bukti bahwa angka laba di website sama dengan laba aktual usaha.

## Sebelum sesi

1. Buka website dan jelaskan singkat: website menghitung **estimasi** dari data yang dimasukkan; prediksi harga dan rekomendasi juga bukan jaminan hasil di masa depan.
2. Minta persetujuan sebelum mencatat umpan balik. Jangan masukkan nama peserta, nama usaha, nomor telepon, atau informasi pengenal ke formulir.
3. Minta peserta memilih satu menu yang benar-benar dijual dan menyiapkan takaran resep, harga jual, jumlah porsi dalam satu periode, biaya tambahan, biaya tetap yang ingin dialokasikan, serta harga beli bahan dari nota/pemasok.
4. Jelaskan bahwa riwayat kalkulator menyimpan rincian menu/resep ke akun. Jika peserta tidak ingin resep dan harga pemasok tersimpan, matikan centang **“Simpan rincian resep dan hasil ke riwayat akun”** sebelum menghitung.
5. Beri kode sesi anonim, misalnya `UMKM-01`. Jangan menuliskan kunci yang menghubungkan kode dengan nama di file aplikasi.

## Tugas peserta

Minta peserta mengerjakan sendiri sebisa mungkin. Jangan memberi petunjuk sebelum mereka meminta bantuan; catat bagian tempat mereka berhenti atau meminta bantuan.

### A. Hitung modal dan estimasi laba menu

Minta peserta:

- memasukkan nama menu, harga jual per porsi, dan jumlah porsi pada periode yang sama dengan biaya tetap;
- menambahkan bahan resep dan takaran dalam gram per porsi;
- mengisi harga beli bahan dalam Rp/kg berdasarkan nota atau pemasok;
- memasukkan biaya lain per porsi serta biaya tetap periode tersebut jika datanya tersedia;
- menghitung hasil dan menjelaskan sendiri arti modal per porsi, omzet, dan estimasi laba.

Minta peserta membandingkan modal bahan per porsi dengan hitungan manual mereka. Jika berbeda, tanyakan bahan atau biaya apa yang menjelaskan selisihnya. Jangan mengubah angka agar tampak cocok.

### B. Baca dashboard harga dan saran belanja

Minta peserta:

- memilih komoditas yang memang mereka beli;
- menemukan harga acuan, rata-rata prediksi tujuh hari, dan saran yang ditampilkan;
- menjelaskan dengan kata-kata sendiri apa arti perubahan prediksi dan apa yang akan mereka pertimbangkan sebelum membeli.

Jelaskan bahwa saran bukan perintah membeli/menunda. Keputusan usaha tetap memperhitungkan stok, kebutuhan, harga pemasok, daya simpan, dan kondisi kas.

## Catat hasil sesi

Di bagian **“Catat umpan balik uji coba UMKM”** pada tab Beranda usaha, isi setelah peserta menyelesaikan tugas. Formulir menyimpan kode sesi, jenis/peran usaha, keberhasilan tugas, waktu, rating kemudahan/kejelasan/manfaat, kecocokan dengan hitungan manual, serta masukan. Formulir tidak menyimpan resep atau harga bahan.

Hasil formulir tersimpan lokal di `data/umkm_user_tests/feedback.csv`. Untuk setiap sesi, catat juga secara terpisah bila ada hal yang tidak terekam, misalnya peserta salah memahami “estimasi laba” atau mengira rekomendasi sebagai jaminan. Jangan mengarang jawaban jika peserta tidak menyampaikan pendapat.

## Ringkasan setelah beberapa sesi

Laporkan jumlah peserta yang benar-benar mengikuti uji, bukan jumlah yang direncanakan. Ringkas:

- jumlah yang menyelesaikan masing-masing tugas sendiri, dengan bantuan, atau belum selesai;
- median rating kemudahan, kejelasan, dan manfaat;
- apakah modal menu cocok dengan hitungan manual, dan penyebab selisih yang ditemukan;
- hambatan atau masukan yang berulang;
- perubahan website yang dibuat setelah uji, lalu apakah perubahan itu dicoba lagi.

Simpan kutipan hanya jika peserta mengizinkan dan anonimisasi kutipannya. Jangan menyimpulkan representasi seluruh UMKM dari beberapa sesi uji eksploratif. Jika belum ada peserta dan baris umpan balik, tulis statusnya **belum diuji ke UMKM**; jangan menyebut temuan pengguna sudah selesai.
