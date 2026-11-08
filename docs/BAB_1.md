# BAB I PENDAHULUAN

---

## 1.1 Latar Belakang

### 1.1.1 Fluktuasi harga pangan dan dampaknya pada UMKM kuliner

Komoditas pangan merupakan kebutuhan pokok yang harganya sangat rentan berubah. Fluktuasi harga terjadi akibat berbagai faktor, antara lain perubahan cuaca, musim tanam dan panen, hari besar keagamaan, kebijakan distribusi, serta dinamika penawaran dan permintaan di pasar. Gejolak harga ini paling terasa pada komoditas yang mudah rusak (*perishable*) seperti cabai, bawang, dan sayuran segar.

Bagi pelaku usaha mikro, kecil, dan menengah (UMKM) di sektor kuliner, ketidakstabilan harga bahan baku menjadi masalah yang nyata. Harga bahan baku adalah komponen utama biaya produksi makanan dan minuman. Ketika harga bahan naik secara tiba-tiba, modal usaha yang telah direncanakan menjadi tidak cukup, sementara menaikkan harga jual secara mendadak sulit dilakukan karena berisiko menurunkan jumlah pembeli. Akibatnya, margin laba menipis, bahkan usaha bisa mengalami kerugian. Kondisi ini menunjukkan perlunya alat bantu yang membantu UMKM mengantisipasi pergerakan harga bahan baku.

### 1.1.2 Prediksi harga dengan model deep learning

Salah satu pendekatan yang berkembang untuk mengantisipasi pergerakan harga adalah prediksi berbasis data deret waktu (*time series forecasting*). Di antara berbagai metode, *deep learning* — khususnya LSTM (*Long Short-Term Memory*) dan GRU (*Gated Recurrent Unit*) — terbukti efektif dalam menangkap pola non-linear dan ketergantungan jangka panjang pada data deret waktu. Kedua arsitektur ini merupakan varian jaringan saraf berulang (*recurrent neural network*, RNN) yang dirancang untuk mengatasi masalah gradien hilang yang kerap dialami RNN standar.

Penelitian di bidang prediksi harga pangan sebagian besar masih berhenti pada tahap evaluasi akurasi model, seperti membandingkan nilai MAE, RMSE, atau MAPE dari berbagai arsitektur. Meskipun bernilai ilmiah, hasil tersebut belum menyentuh langsung kebutuhan praktis pelaku usaha. Masih jarang penelitian yang menjembatani hasil prediksi menjadi produk yang dapat digunakan sehari-hari oleh UMKM.

### 1.1.3 Celah penelitian dan gagasan solusi

Berdasarkan ulasan di atas, terdapat dua celah utama:

1. **Celah aplikatif** — hasil prediksi harga belum banyak dikemas menjadi alat yang praktis, mudah dipakai, dan relevan untuk UMKM kuliner.
2. **Celah kelayakan bisnis** — belum teruji apakah layanan prediksi harga dapat diterima sebagai produk berbayar oleh pengguna, padahal keberlanjutan pengembangan aplikasi bergantung pada model pendapatan.

Penelitian ini menjawab kedua celah tersebut melalui pembangunan **PanganLaba**, sebuah aplikasi web yang menggabungkan:

- **Model prediksi harga** berbasis LSTM dan GRU untuk memperkirakan harga komoditas pangan pada horizon 7 hari ke depan;
- **Kalkulator modal dan laba menu** yang membantu pengguna menghitung biaya per porsi dan harga jual yang aman;
- **Sistem langganan trial-berbayar** (7 hari gratis, kemudian paket berbayar) sebagai uji kelayakan komersial produk.

Dengan demikian, penelitian ini tidak hanya berkontribusi pada evaluasi model prediksi, tetapi juga pada perancangan produk aplikatif yang berpotensi bermanfaat langsung bagi UMKM.

---

## 1.2 Identifikasi Masalah

Berdasarkan latar belakang, masalah yang teridentifikasi:

1. Tingginya fluktuasi harga komoditas pangan yang menyulitkan UMKM kuliner merencanakan modal dan menetapkan harga jual yang aman.
2. Minimnya alat aplikatif yang menjembatani hasil prediksi harga model LSTM/GRU menjadi produk yang siap digunakan pelaku UMKM.
3. Belum diketahui secara empiris apakah penambahan fitur eksternal (cuaca dan kalender Indonesia) meningkatkan akurasi prediksi dibandingkan model berbasis harga saja.
4. Belum teruji kelayakan komersial layanan prediksi harga bagi UMKM, khususnya kesediaan pengguna mengikuti model langganan trial-berbayar.

---

## 1.3 Batasan Masalah

Agar penelitian terarah, ruang lingkup dibatasi sebagai berikut:

1. **Data dan komoditas.** Data harga berasal dari workbook PIHPS yang digunakan pada proyek, mencakup 13 komoditas pangan: beras, telur ayam, daging ayam, daging sapi, gula pasir premium, gula pasir lokal, minyak goreng bermerk, minyak goreng curah, bawang merah, bawang putih, cabai merah, cabai rawit hijau, dan cabai rawit merah.
2. **Model.** Model yang digunakan adalah LSTM dan GRU. Horizon prediksi dibatasi 7 hari; jendela data (*window*) 30 hari; jumlah epoch dibatasi hingga konvergensi pada data latih.
3. **Fitur eksternal.** Fitur yang dievaluasi dibatasi pada data cuaca (harian) dan kalender Indonesia (hari libur nasional, cuti bersama, Idulfitri, akhir pekan, serta siklus tanggal/bulan).
4. **Evaluasi.** Evaluasi dilakukan secara historis terhadap data uji; tidak mencakup implementasi real-time untuk prakiraan menyusul data terakhir.
5. **Aplikasi.** Pengembangan aplikasi dibatasi pada prototype Streamlit dengan basis data SQLite lokal. Pembayaran dilakukan secara manual (transfer BCA) dan diverifikasi oleh pengelola melalui panel admin; tidak mencakup integrasi gerbang pembayaran otomatis.
6. **Uji kelayakan.** Pengujian penerimaan pengguna dibatasi pada simulasi status akun (trial, aktif, berakhir) dan skenario alur pembayaran, bukan survei skala besar.

---

## 1.4 Rumusan Masalah

1. Seberapa baik model LSTM dan GRU dalam memprediksi harga komoditas pangan, diukur dengan metrik MAE, RMSE, dan MAPE?
2. Di antara model LSTM dan GRU, manakah yang memberikan akurasi lebih baik pada data komoditas pangan?
3. Apakah penambahan fitur eksternal (cuaca dan kalender) meningkatkan akurasi prediksi dibandingkan model yang hanya menggunakan data harga?
4. Bagaimana merancang dan membangun aplikasi web prediksi harga dengan model langganan trial-berbayar yang layak digunakan oleh UMKM?

---

## 1.5 Tujuan Penelitian

Sesuai rumusan masalah, tujuan penelitian adalah:

1. Mengimplementasikan dan mengevaluasi model LSTM dan GRU untuk prediksi harga komoditas pangan berdasarkan metrik MAE, RMSE, dan MAPE.
2. Membandingkan akurasi model LSTM dan GRU serta pengaruh penambahan fitur eksternal (cuaca dan kalender).
3. Membangun aplikasi web PanganLaba yang memadukan hasil prediksi harga dengan kalkulator modal dan laba menu.
4. Menerapkan dan menguji model langganan trial-berbayar sebagai dasar uji kelayakan komersial produk.

---

## 1.6 Manfaat Penelitian

### 1.6.1 Manfaat teoritis

1. Memberikan bukti empiris perbandingan kinerja LSTM dan GRU pada data harga komoditas pangan lokal.
2. Menyumbang pengetahuan mengenai pengaruh fitur eksternal (cuaca dan kalender) terhadap akurasi prediksi harga komoditas pangan.
3. Menjadi referensi penelitian lanjutan di bidang prediksi harga pangan berbasis *deep learning* dan aplikasinya.

### 1.6.2 Manfaat praktis

1. **Bagi UMKM kuliner:** menyediakan alat bantu untuk merencanakan belanja bahan baku, menghitung modal per porsi, dan menetapkan harga jual yang aman.
2. **Bagi pengembang aplikasi:** menyediakan kerangka produk layanan prediksi berbasis langganan (trial-berbayar) yang dapat dijadikan acuan komersialisasi layanan serupa.
3. **Bagi akademisi:** menjadi contoh integrasi riset model deret waktu dengan pengembangan produk perangkat lunak.

---

## 1.7 Definisi Istilah

1. **LSTM (Long Short-Term Memory)** — arsitektur RNN yang mampu mempelajari ketergantungan jangka panjang dengan menggunakan gerbang *input*, *forget*, dan *output*.
2. **GRU (Gated Recurrent Unit)** — varian RNN yang lebih ringan dari LSTM karena hanya memiliki dua gerbang (*reset* dan *update*).
3. **MAE (Mean Absolute Error)** — rata-rata selisih absolut antara nilai aktual dan prediksi (Rp/kg).
4. **RMSE (Root Mean Square Error)** — akar rata-rata kuadrat error; memberi penalti lebih besar pada error besar.
5. **MAPE (Mean Absolute Percentage Error)** — rata-rata persentase error absolut; memudahkan interpretasi relatif terhadap harga.
6. **Trial** — masa percobaan gratis, dalam penelitian ini 7 hari sejak login pertama.
7. **Langganan berbayar** — paket akses berbayar (Starter/Pro/Enterprise) dengan batas jumlah komoditas yang dianalisis.
8. **Paywall** — penghalang akses yang muncul setelah masa trial berakhir hingga pengguna berlangganan.

---

## 1.8 Sistematika Penulisan

- **Bab I — Pendahuluan:** latar belakang, identifikasi masalah, batasan masalah, rumusan masalah, tujuan, manfaat, definisi istilah, dan sistematika.
- **Bab II — Tinjauan Pustaka:** landasan teori deret waktu, LSTM/GRU, metrik evaluasi, tinjauan harga pangan, model langganan, serta penelitian terdahulu.
- **Bab III — Metodologi:** alur penelitian, sumber dan pengolahan data, perancangan model, perancangan aplikasi dan model langganan, serta skenario pengujian.
- **Bab IV — Hasil dan Pembahasan:** hasil evaluasi model LSTM/GRU, perbandingan konfigurasi fitur, pembahasan aplikasi, dan hasil uji kelayakan.
- **Bab V — Penutup:** kesimpulan jawaban atas rumusan masalah dan saran untuk penelitian lanjutan.
