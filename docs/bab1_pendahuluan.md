# BAB I PENDAHULUAN

## 1.1 Latar Belakang

Komoditas pangan merupakan kebutuhan pokok yang keberadaannya paling menentukan kesejahteraan masyarakat Indonesia. Stabilitas harga pangan menjadi perhatian pemerintah karena perubahan harga berdampak langsung pada daya beli, laju inflasi, dan keberlangsungan usaha sektor riil. Bank Indonesia mengelompokkan harga bahan pangan ke dalam komponen inflasi harga bergejolak (volatile food), yang kerap menjadi penyumbang inflasi terbesar ketika pasokan terganggu (Bank Indonesia, 2024). Fluktuasi harga terjadi karena berbagai faktor, antara lain perubahan cuaca, musim tanam dan panen, hari besar keagamaan, kebijakan distribusi, serta dinamika penawaran dan permintaan di pasar. Gejolak ini paling terasa pada komoditas yang mudah rusak seperti cabai, bawang, dan sayuran segar, yang harganya dapat berubah drastis dalam hitungan hari.

Ketidakstabilan harga ini menimbulkan masalah nyata bagi pelaku usaha mikro, kecil, dan menengah (UMKM) di sektor kuliner. Harga bahan baku merupakan komponen utama biaya produksi makanan dan minuman. Ketika harga bahan baku naik secara tiba-tiba, modal usaha yang telah direncanakan menjadi tidak mencukupi, sementara menaikkan harga jual secara mendadak sulit dilakukan karena berisiko menurunkan jumlah pembeli. Akibatnya, margin laba menipis, bahkan usaha dapat mengalami kerugian. Kota Depok, yang berada di kawasan Jabodetabek, memiliki jumlah UMKM kuliner yang terus bertumbuh, tetapi rentan terhadap gejolak harga bahan baku. Oleh karena itu, kemampuan memperkirakan pergerakan harga menjadi hal penting bagi pelaku UMKM untuk merencanakan belanja bahan baku dan menetapkan harga jual yang aman.

Pendekatan yang berkembang untuk mengantisipasi pergerakan harga adalah prediksi berbasis data deret waktu (time series forecasting). Di antara berbagai metode, deep learning, khususnya Long Short-Term Memory (LSTM) dan Gated Recurrent Unit (GRU), terbukti efektif dalam menangkap pola non-linear dan ketergantungan jangka panjang pada data deret waktu. LSTM diperkenalkan oleh Hochreiter dan Schmidhuber (1997) untuk mengatasi masalah hilangnya gradien pada jaringan saraf berulang (recurrent neural network, RNN), sementara GRU dikembangkan oleh Cho dkk. (2014) sebagai varian yang lebih sederhana dengan kinerja hampir sama tetapi komputasi lebih efisien. Kedua arsitektur ini banyak digunakan untuk meramalkan deret waktu keuangan dan harga.

Kajian mengenai penerapan deep learning untuk prediksi harga pangan makin banyak dilakukan sejak tahun 2021. Hendrawati dkk. (2026) membandingkan LSTM dan GRU untuk memprediksi harga beras di Indonesia menggunakan data harian 2021–2024; keduanya mampu menangkap pola harga beras, meski hasilnya sedikit berbeda tergantung karakteristik data. Amalia dkk. (2026) mencoba pendekatan lain dengan mengembangkan Temporal Fusion Transformer (TFT) untuk meramalkan harga 10 komoditas pangan strategis Indonesia 30 hari ke depan, lalu membandingkannya dengan LSTM, GRU, ARIMA, dan metode naïve. TFT unggul khususnya pada komoditas yang harganya bergejolak tinggi, sementara LSTM dan GRU tetap menjadi pembanding yang relevan. Sementara itu, Wang dkk. (2023) menemukan bahwa pemasukan data iklim dan lingkungan dapat menaikkan akurasi prediksi harga komoditas gandum, dan Manogna dkk. (2025) menyimpulkan bahwa model deep learning mengungguli ARIMA serta metode machine learning lain dalam memprediksi harga 23 komoditas pertanian di India.

Kendati demikian, kajian-kajian di atas umumnya dilakukan pada tingkat nasional atau global, atau berfokus pada satu jenis komoditas. Belum banyak yang mengarah pada kebutuhan praktis pelaku usaha di tingkat daerah, apalagi yang secara khusus membandingkan LSTM dan GRU untuk memprediksi harga komoditas pangan strategis di Indonesia sambil menilai peran fitur eksternal (cuaca dan kalender) secara bersamaan. Untuk konteks Kota Depok dan kebutuhan UMKM kuliner, penelitian semacam itu nyaris tidak ada. Padahal data yang dibutuhkan semakin terbuka, mulai dari harga harian Pusat Informasi Harga Pangan Strategis (PIHPS) Kementerian Perdagangan (Kementerian Perdagangan, 2024), cuaca harian reanalisis ERA5, hingga kalender libur nasional Indonesia. Ini membuka peluang untuk mengembangkan model prediksi harga pangan yang lebih sesuai dengan kondisi dan kebutuhan lokal.

Penelitian ini memakai data harga harian PIHPS untuk 13 komoditas pangan strategis di Kota Depok pada periode 2020–2026, yang digabungkan dengan cuaca harian dan kalender libur nasional Indonesia. Model yang dikembangkan membandingkan arsitektur LSTM dan GRU, masing-masing diuji dengan dua skenario fitur: hanya harga, serta harga dengan fitur eksternal berupa cuaca dan kalender.

Ada tiga hal yang menjadi kebaruan penelitian ini. Pertama, perbandingan LSTM dan GRU dilakukan pada beberapa komoditas pangan strategis sekaligus di tingkat lokal. Kedua, diuji apakah penambahan fitur eksternal benar-benar mengubah akurasi prediksi. Ketiga, hasil prediksi diarahkan langsung untuk membantu UMKM kuliner Kota Depok merencanakan belanja bahan baku dan menetapkan harga jual yang aman. Kebutuhan akan alat bantu yang bisa diandalkan ini selama ini belum banyak terpenuhi, karena sebagian besar riset prediksi harga masih berhenti pada tataran teoretis. Karena itu, penelitian ini penting dilakukan untuk menjawab kebutuhan praktis tersebut.

## 1.2 Rumusan Masalah

Berdasarkan latar belakang di atas, rumusan masalah penelitian ini adalah sebagai berikut:

1. Bagaimana kinerja model LSTM dan GRU dalam memprediksi harga komoditas pangan strategis di Kota Depok berdasarkan metrik MAE, RMSE, dan MAPE, serta manakah di antara keduanya yang memberikan kinerja lebih baik?

2. Apakah penambahan fitur eksternal berupa data cuaca dan kalender memengaruhi akurasi prediksi dibandingkan model yang hanya menggunakan data harga?

3. Bagaimana hasil prediksi harga komoditas pangan strategis dapat digunakan untuk mendukung perencanaan belanja bahan baku UMKM kuliner di Kota Depok?

## 1.3 Tujuan Penelitian

Sesuai dengan rumusan masalah, tujuan penelitian ini adalah sebagai berikut:

1. Mengimplementasikan, mengevaluasi, dan membandingkan kinerja model LSTM dan GRU dalam memprediksi harga komoditas pangan strategis di Kota Depok berdasarkan metrik MAE, RMSE, dan MAPE.

2. Menguji pengaruh penambahan fitur eksternal berupa data cuaca dan kalender terhadap akurasi prediksi harga komoditas pangan strategis.

3. Memformulasikan pemanfaatan hasil prediksi harga komoditas pangan strategis untuk mendukung perencanaan belanja bahan baku UMKM kuliner di Kota Depok.

## 1.4 Manfaat Penelitian

1. Bagi Akademisi: Menambah literatur pada bidang *machine learning* terkait perbandingan arsitektur LSTM dan GRU serta pengaruh fitur eksternal berupa cuaca dan kalender pada prediksi deret waktu harga komoditas pangan.

2. Bagi Pelaku UMKM Kuliner: Memberikan panduan yang terstruktur dalam merencanakan belanja bahan baku berdasarkan prakiraan harga tujuh hari ke depan, sehingga keputusan pembelian dan penetapan harga jual menjadi lebih terukur.

3. Bagi Pengembang Aplikasi: Menyediakan contoh penerapan model LSTM dan GRU dari tahap pelatihan hingga penyajian hasil prediksi, sebagai acuan pengembangan sistem serupa.

## 1.5 Batasan Masalah

Agar penelitian terarah, ruang lingkup penelitian dibatasi sebagai berikut:

1. Data dan komoditas: data harga berasal dari PIHPS untuk 13 komoditas pangan strategis di Kota Depok pada periode 2020–2026, yaitu beras, telur ayam, daging ayam, daging sapi, gula pasir premium, gula pasir lokal, minyak goreng bermerek, minyak goreng curah, bawang merah, bawang putih, cabai merah, cabai rawit hijau, dan cabai rawit merah.

2. Model: model yang digunakan adalah LSTM dan GRU dengan horizon prediksi 7 hari dan jendela data 30 hari.

3. Fitur eksternal: fitur yang dievaluasi dibatasi pada data cuaca harian dan kalender Indonesia (hari libur nasional, cuti bersama, akhir pekan, dan penanda Idulfitri).

4. Evaluasi: evaluasi dilakukan secara kronologis (80% data latih dan 20% data uji) dengan metrik MAE, RMSE, dan MAPE; tidak mencakup implementasi prediksi real-time.

5. Aplikasi: hasil prediksi harga digunakan sebagai dasar penghitungan modal per porsi, penentuan harga jual, serta penyusunan laporan laba-rugi bersih (laba kotor, laba bersih, margin, dan titik impas) untuk mendukung keputusan belanja bahan baku; tetapi tidak mencakup manajemen stok, fungsi kasir, atau otomatisasi keputusan pembelian.

## Daftar Pustaka

Amalia, S., Dhini, A., Zulkarnain, Za'in, C., & Surjandari, I. (2026). A temporal fusion transformer for multi-step forecasting of Indonesia's strategic food commodity prices. *Results in Engineering*, 30, 110131. https://doi.org/10.1016/j.rineng.2026.110131

Bank Indonesia. (2024). *Laporan Perekonomian Indonesia*. Jakarta: Bank Indonesia.

Cho, K., van Merriënboer, B., Gulcehre, C., Bahdanau, D., Bougares, F., Schwenk, H., & Bengio, Y. (2014). Learning phrase representations using RNN encoder-decoder for statistical machine translation. *Proceedings of EMNLP 2014*.

Hendrawati, T., Marthendra, K., Simanjuntak, B. R. J., & Pravitasari, A. A. (2026). LSTM and GRU in rice prediction for food security in Indonesia. *BAREKENG: Journal of Mathematics and Its Applications*, 20(1), 55–68. https://doi.org/10.30598/barekengvol20iss1pp0055-0068

Hochreiter, S., & Schmidhuber, J. (1997). Long short-term memory. *Neural Computation*, 9(8), 1735–1780.

Kementerian Perdagangan. (2024). *Pusat Informasi Harga Pangan Strategis (PIHPS)*. Jakarta: Kementerian Perdagangan Republik Indonesia.


Manogna, R. L., Dharmaji, V., & Sarang, S. (2025). Enhancing agricultural commodity price forecasting with deep learning. *Scientific Reports*, 15, 20903. https://doi.org/10.1038/s41598-025-05103-z


Wang, Z., French, N., James, T., Schillaci, C., Chan, F., Feng, M., & Lipani, A. (2023). Climate and environmental data contribute to the prediction of grain commodity prices using deep learning. *Journal of Sustainable Agriculture and Environment*, 2(1). https://doi.org/10.1002/sae2.12041
