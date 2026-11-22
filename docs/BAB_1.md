# BAB I PENDAHULUAN

---

## 1.1 Latar Belakang

Komoditas pangan merupakan kebutuhan pokok yang keberadaannya paling menentukan kesejahteraan masyarakat Indonesia. Stabilitas harga pangan menjadi perhatian pemerintah karena perubahan harga berdampak langsung pada daya beli, laju inflasi, dan keberlangsungan usaha sektor riil. Bank Indonesia mengelompokkan harga bahan pangan ke dalam komponen inflasi harga bergejolak (*volatile food*), yang kerap menjadi penyumbang inflasi terbesar ketika pasokan terganggu (Bank Indonesia, 2024). Fluktuasi harga terjadi karena berbagai faktor, antara lain perubahan cuaca, musim tanam dan panen, hari besar keagamaan, kebijakan distribusi, serta dinamika penawaran dan permintaan di pasar. Gejolak ini paling terasa pada komoditas yang mudah rusak seperti cabai, bawang, dan sayuran segar, yang harganya dapat berubah drastis dalam hitungan hari. Ketidakstabilan harga ini menimbulkan masalah nyata bagi pelaku usaha mikro, kecil, dan menengah (UMKM) di sektor kuliner: harga bahan baku merupakan komponen utama biaya produksi makanan dan minuman, sehingga ketika harga naik secara tiba-tiba modal yang direncanakan menjadi tidak mencukupi sementara menaikkan harga jual secara mendadak sulit dilakukan karena berisiko menurunkan jumlah pembeli. Akibatnya, margin laba menipis, bahkan usaha dapat mengalami kerugian. Kota Depok di kawasan Jabodetabek memiliki jumlah UMKM kuliner yang terus bertumbuh tetapi rentan terhadap gejolak harga bahan baku, sehingga kemampuan memperkirakan pergerakan harga menjadi penting untuk merencanakan belanja bahan baku dan menetapkan harga jual yang aman.

Pendekatan yang berkembang untuk mengantisipasi pergerakan harga adalah prediksi berbasis data deret waktu (*time series forecasting*). Di antara berbagai metode, *deep learning*, khususnya Long Short-Term Memory (LSTM) dan Gated Recurrent Unit (GRU), terbukti efektif dalam menangkap pola non-linear dan ketergantungan jangka panjang pada data deret waktu. LSTM diperkenalkan oleh Hochreiter dan Schmidhuber (1997) untuk mengatasi masalah hilangnya gradien pada jaringan saraf berulang (*recurrent neural network*, RNN), sementara GRU dikembangkan oleh Cho dkk. (2014) sebagai varian yang lebih sederhana dengan kinerja hampir sama tetapi komputasi lebih efisien. Kedua arsitektur ini banyak digunakan untuk meramalkan deret waktu keuangan dan harga.

Kajian penerapan *deep learning* untuk prediksi harga pangan makin banyak dilakukan sejak tahun 2021. Hendrawati dkk. (2026) membandingkan LSTM dan GRU untuk memprediksi harga beras di Indonesia; Amalia dkk. (2026) mengembangkan *Temporal Fusion Transformer* (TFT) untuk meramalkan harga 10 komoditas pangan strategis Indonesia dan membandingkannya dengan LSTM, GRU, ARIMA, serta metode naïve; Wang dkk. (2023) menemukan bahwa pemasukan data iklim dan lingkungan menaikkan akurasi prediksi harga gandum; dan Manogna dkk. (2025) menyimpulkan bahwa model *deep learning* mengungguli ARIMA serta metode *machine learning* lain dalam memprediksi harga 23 komoditas pertanian di India. Kendati demikian, kajian tersebut umumnya dilakukan pada tingkat nasional atau global atau berfokus pada satu jenis komoditas; belum banyak yang mengarah pada kebutuhan praktis pelaku usaha di tingkat daerah, apalagi yang secara khusus membandingkan LSTM dan GRU untuk memprediksi harga komoditas pangan strategis di Indonesia sambil menilai peran fitur eksternal (cuaca dan kalender) secara bersamaan. Untuk konteks Kota Depok dan kebutuhan UMKM kuliner, penelitian semacam itu nyaris tidak ada. Dari uraian tersebut timbul dua celah utama: pertama, hasil prediksi harga belum banyak dikemas menjadi alat yang praktis, mudah dipakai, dan relevan bagi UMKM kuliner; kedua, belum teruji apakah layanan prediksi harga dapat diterima sebagai produk berbayar, padahal keberlanjutan pengembangan aplikasi bergantung pada model pendapatan.

Untuk menjawab kedua celah tersebut, penelitian ini membangun **PanganLaba**, sebuah aplikasi web yang menggabungkan model prediksi harga berbasis LSTM dan GRU untuk memperkirakan harga komoditas pangan pada horizon 7 hari ke depan; kalkulator modal dan laba menu yang membantu pengguna menghitung biaya per porsi dan harga jual yang aman; serta sistem langganan *trial*-berbayar (7 hari gratis, kemudian paket berbayar) sebagai uji kelayakan komersial produk. Dengan demikian, penelitian ini tidak hanya berkontribusi pada evaluasi model prediksi, tetapi juga pada perancangan produk aplikatif yang bermanfaat langsung bagi UMKM.

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

---

## Daftar Pustaka

Amalia, S., Dhini, A., Zulkarnain, Za'in, C., & Surjandari, I. (2026). A temporal fusion transformer for multi-step forecasting of Indonesia's strategic food commodity prices. *Results in Engineering*, 30, 110131. https://doi.org/10.1016/j.rineng.2026.110131

Bank Indonesia. (2024). *Laporan Perekonomian Indonesia*. Jakarta: Bank Indonesia.

Cho, K., van Merriënboer, B., Gulcehre, C., Bahdanau, D., Bougares, F., Schwenk, H., & Bengio, Y. (2014). Learning phrase representations using RNN encoder-decoder for statistical machine translation. *Proceedings of EMNLP 2014*.

Hendrawati, T., Marthendra, K., Simanjuntak, B. R. J., & Pravitasari, A. A. (2026). LSTM and GRU in rice prediction for food security in Indonesia. *BAREKENG: Journal of Mathematics and Its Applications*, 20(1), 55–68. https://doi.org/10.30598/barekengvol20iss1pp0055-0068

Hochreiter, S., & Schmidhuber, J. (1997). Long short-term memory. *Neural Computation*, 9(8), 1735–1780.

Kementerian Perdagangan. (2024). *Pusat Informasi Harga Pangan Strategis (PIHPS)*. Jakarta: Kementerian Perdagangan Republik Indonesia.

Manogna, R. L., Dharmaji, V., & Sarang, S. (2025). Enhancing agricultural commodity price forecasting with deep learning. *Scientific Reports*, 15, 20903. https://doi.org/10.1038/s41598-025-05103-z

Wang, Z., French, N., James, T., Schillaci, C., Chan, F., Feng, M., & Lipani, A. (2023). Climate and environmental data contribute to the prediction of grain commodity prices using deep learning. *Journal of Sustainable Agriculture and Environment*, 2(1). https://doi.org/10.1002/sae2.12041
