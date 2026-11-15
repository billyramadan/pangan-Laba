# BAB II KAJIAN PUSTAKA

## 2.1 Landasan Teori

### 2.1.1 Harga Komoditas Pangan Strategis

Komoditas pangan merupakan kebutuhan pokok yang pergerakan harganya sangat menentukan stabilitas ekonomi rumah tangga dan nasional. Bank Indonesia mengelompokkan harga bahan pangan ke dalam komponen inflasi harga bergejolak (*volatile food*), yang kerap menjadi penyumbang inflasi terbesar ketika pasokan terganggu (Bank Indonesia, 2024). Gejolak harga terjadi karena kombinasi faktor sisi penawaran, seperti cuaca, musim tanam dan panen, biaya distribusi, serta sisi permintaan seperti pendapatan rumah tangga dan perilaku konsumen. Komoditas yang mudah rusak (*perishable*) seperti cabai, bawang, dan sayuran segar paling rentan mengalami perubahan harga yang tajam dalam waktu singkat.

Dalam konteks Indonesia, Pusat Informasi Harga Pangan Strategis (PIHPS) Kementerian Perdagangan menyediakan data harga harian komoditas strategis di tingkat nasional maupun daerah (Kementerian Perdagangan, 2024). Data ini menjadi dasar penting bagi penelitian dan perumusan kebijakan stabilisasi harga. Pada tingkat usaha mikro, kecil, dan menengah (UMKM) sektor kuliner, fluktuasi harga bahan baku berdampak langsung pada biaya produksi dan margin laba, sehingga kemampuan memperkirakan pergerakan harga menjadi kebutuhan yang aplikatif.

### 2.1.2 Prediksi Deret Waktu (Time Series Forecasting)

Prediksi deret waktu adalah proses memperkirakan nilai masa depan berdasarkan pola historis data berurutan waktu. Ketepatan prediksi sangat bergantung pada kemampuan metode menangkap pola tren, musiman, siklus, dan ketidakpastian. Pendekatan klasik seperti ARIMA (Autoregressive Integrated Moving Average) terbukti efektif untuk data yang relatif linear, tetapi memiliki keterbatasan dalam memodelkan dinamika non-linear yang kompleks pada harga pangan. Keterbatasan ini mendorong adopsi pendekatan berbasis jaringan saraf.

### 2.1.3 Deep Learning untuk Deret Waktu

Deep learning merupakan bagian dari machine learning yang menggunakan jaringan saraf berlapis untuk mempelajari representasi data secara hierarkis. Untuk data deret waktu, jaringan saraf berulang (Recurrent Neural Network, RNN) dirancang menangkap ketergantungan temporal. Namun, RNN standar mengalami masalah gradien hilang (*vanishing gradient*) ketika memproses urutan panjang. Masalah ini diatasi oleh dua varian utama: Long Short-Term Memory (LSTM) dan Gated Recurrent Unit (GRU).

Manogna dkk. (2025) mengevaluasi berbagai metode — ARIMA, Support Vector Regression, XGBoost, MLP, RNN, LSTM, GRU, dan Echo State Network — untuk memprediksi harga 23 komoditas pertanian di India. Hasilnya menunjukkan bahwa model deep learning, khususnya LSTM dan GRU, mengungguli metode statistik dan machine learning lain dalam menangkap pola temporal yang kompleks. Temuan ini memperkuat pemilihan LSTM dan GRU sebagai model utama penelitian.

### 2.1.4 Long Short-Term Memory (LSTM)

LSTM diperkenalkan oleh Hochreiter dan Schmidhuber (1997) sebagai solusi atas masalah gradien hilang pada RNN. LSTM memiliki sel memori yang dijaga oleh tiga gerbang: gerbang *forget* (melupakan informasi tidak relevan), gerbang *input* (menyimpan informasi baru), dan gerbang *output* (mengeluarkan informasi yang diperlukan). Struktur ini memungkinkan LSTM menyimpan informasi jangka panjang sekaligus membuang gangguan, sehingga cocok untuk data deret waktu yang panjang dan bergejolak.

### 2.1.5 Gated Recurrent Unit (GRU)

GRU dikembangkan oleh Cho dkk. (2014) sebagai varian LSTM yang lebih sederhana. GRU hanya memiliki dua gerbang, yaitu gerbang *reset* dan gerbang *update*, tanpa sel memori terpisah. Kesederhanaan ini membuat GRU memiliki jumlah parameter lebih sedikit sehingga komputasinya lebih efisien, sementara kinerjanya hampir setara dengan LSTM pada banyak kasus. Dalam penelitian dengan data regional dan horizon menengah, efisiensi komputasi GRU menjadi pertimbangan praktis yang penting.

### 2.1.6 Fitur Eksternal: Cuaca, Kalender, dan Siklus

Kualitas prediksi deret waktu tidak hanya ditentukan oleh arsitektur model, tetapi juga oleh fitur yang digunakan. Selain harga historis, fitur eksternal berpotensi memperkaya informasi bagi model. Wang dkk. (2023) menunjukkan bahwa penambahan data iklim dan lingkungan meningkatkan akurasi prediksi harga komoditas gandum menggunakan deep learning. Temuan ini menegaskan bahwa variabel lingkungan dapat menjadi sinyal yang relevan bagi pergerakan harga pertanian. Selain itu, kalender libur nasional dan hari besar keagamaan memengaruhi pola permintaan, terutama menjelang Idulfitri di Indonesia (Murtani dkk., 2026). Komponen siklus hari dan bulan, yang direpresentasikan dalam bentuk sinus dan kosinus, membantu model menangkap periodisitas.

### 2.1.7 Metrik Evaluasi

Kinerja model prediksi dievaluasi menggunakan tiga metrik utama: Mean Absolute Error (MAE), Root Mean Square Error (RMSE), dan Mean Absolute Percentage Error (MAPE). MAE mengukur rata-rata selisih absolut antara nilai aktual dan prediksi, RMSE memberi penalti lebih besar pada kesalahan besar, sedangkan MAPE menyajikan kesalahan relatif dalam bentuk persentase sehingga mudah diinterpretasikan terhadap harga aktual (Amalia dkk., 2026).

### 2.1.8 Analisis Laba Menu UMKM Kuliner

UMKM kuliner memiliki karakteristik biaya yang didominasi bahan baku. Modal per porsi dihitung dari takaran bahan dikalikan harga satuan, sehingga perubahan harga bahan langsung mengubah laba kotor, laba bersih, margin, dan titik impas. Integrasi prediksi harga ke dalam kalkulator laba memungkinkan pelaku usaha mengantisipasi perubahan biaya dan menetapkan harga jual yang aman.

## 2.2 Penelitian Terdahulu

Kajian terhadap penelitian terdahulu bertujuan memetakan posisi dan kebaruan penelitian ini. Terdapat tujuh penelitian relevan yang dibandingkan dari sisi metode, objek, variabel, dan hasil.

**Amalia dkk. (2026)** mengembangkan Temporal Fusion Transformer (TFT) untuk peramalan multi-langkah (30 hari) harga 10 komoditas pangan strategis Indonesia, lalu membandingkannya dengan LSTM, GRU, ARIMA, dan metode naïve. Hasil menunjukkan TFT unggul pada komoditas bergejolak tinggi, sementara LSTM dan GRU tetap menjadi pembanding yang relevan. Perbedaan dengan penelitian ini terletak pada arsitektur (LSTM/GRU), jumlah komoditas (13), cakupan wilayah (Kota Depok), dan arah aplikasi (UMKM).

**Hendrawati dkk. (2026)** membandingkan LSTM dan GRU untuk memprediksi harga beras Indonesia menggunakan data harian 2021–2024. Kedua model mampu menangkap pola harga beras dengan hasil sedikit berbeda tergantung karakteristik data. Penelitian ini memiliki kesamaan metode dengan studi tersebut, namun meluaskan cakupan ke 13 komoditas dan menambahkan fitur eksternal.

**Murtani dkk. (2026)** melakukan kajian komparatif algoritma machine learning untuk memprediksi harga pangan multi-komoditas menjelang Idulfitri di Indonesia (2026–2030). Penelitian ini menegaskan pentingnya faktor kalender dan hari besar keagamaan sebagai penentu pola harga, yang menjadi dasar penggunaan fitur kalender pada penelitian ini.

**Lestari dkk. (2025)** memprediksi harga komoditas pertanian (bawang putih, bawang merah, cabai rawit, cabai merah) di Kota Singkawang menggunakan tiga model ensemble: Linear Regression, Random Forest, dan XGBoost. Penelitian ini menunjukkan relevansi prediksi harga di tingkat kota, sejalan dengan fokus lokal penelitian ini, meskipun menggunakan metode yang berbeda.

**Wang dkk. (2023)** membuktikan bahwa data iklim dan lingkungan meningkatkan akurasi prediksi harga komoditas gandum menggunakan deep learning. Temuan ini menjadi dasar teoretis penggunaan fitur cuaca pada penelitian ini.

**Manogna dkk. (2025)** menunjukkan keunggulan LSTM dan GRU dibandingkan ARIMA dan metode machine learning lain dalam memprediksi harga 23 komoditas pertanian di India. Penelitian ini memperkuat pemilihan LSTM dan GRU sebagai model utama.

**Utama dan Sari (2026)** mengembangkan model LSTM multi-horizon untuk memprediksi harga pangan Indonesia sebagai dukungan program Makan Bergizi Gratis (MBG). Penelitian ini menegaskan pemanfaatan prediksi harga untuk kebutuhan praktis, meskipun untuk skala kebijakan nasional, bukan untuk UMKM.

## 2.3 Research Gap

Berdasarkan perbandingan penelitian terdahulu, dapat diidentifikasi beberapa celah penelitian (*research gap*). Pertama, mayoritas penelitian dilakukan pada tingkat nasional atau global, sedangkan penelitian di tingkat kota masih terbatas. Kedua, penelitian yang secara khusus membandingkan LSTM dan GRU untuk prediksi harga komoditas pangan di Indonesia pada tingkat daerah masih jarang. Ketiga, integrasi fitur eksternal berupa cuaca dan kalender secara bersamaan pada prediksi harga pangan lokal belum banyak dieksplorasi. Keempat, pemanfaatan hasil prediksi harga sebagai dasar analisis laba menu UMKM kuliner belum ditemukan pada penelitian sebelumnya. Celah-celah inilah yang menjadi posisi dan kebaruan penelitian ini.

## 2.4 Kerangka Pemikiran

Kerangka pemikiran penelitian ini menjelaskan alur hubungan antarkonsep secara logis. Fluktuasi harga komoditas pangan dipengaruhi oleh faktor cuaca, kalender, dan siklus. Data harga historis beserta fitur eksternal tersebut menjadi masukan bagi model LSTM dan GRU untuk menghasilkan prediksi harga tujuh hari ke depan. Kinerja kedua model dibandingkan menggunakan metrik MAE, RMSE, dan MAPE. Prediksi harga selanjutnya digunakan sebagai dasar perhitungan modal per porsi, laba bersih, margin, dan titik impas pada kalkulator laba menu, yang pada akhirnya mendukung perencanaan belanja bahan baku UMKM kuliner. Dengan demikian, alur berangkat dari masalah fluktuasi harga, menuju solusi prediksi berbasis deep learning, dan berakhir pada pemanfaatan aplikatif bagi UMKM.

## 2.5 Hipotesis Penelitian

Berdasarkan kerangka pemikiran dan penelitian terdahulu, dirumuskan hipotesis sebagai berikut:

**H1:** Terdapat perbedaan kinerja antara model LSTM dan GRU dalam memprediksi harga komoditas pangan strategis di Kota Depok.

**H2:** Penambahan fitur eksternal berupa data cuaca dan kalender berpengaruh terhadap akurasi prediksi harga komoditas pangan strategis.

**H3:** Hasil prediksi harga komoditas pangan strategis dapat dimanfaatkan untuk mendukung perencanaan belanja bahan baku UMKM kuliner di Kota Depok.

## Daftar Pustaka

Amalia, S., Dhini, A., Zulkarnain, Za'in, C., & Surjandari, I. (2026). A temporal fusion transformer for multi-step forecasting of Indonesia's strategic food commodity prices. *Results in Engineering*, 30, 110131. https://doi.org/10.1016/j.rineng.2026.110131

Bank Indonesia. (2024). *Laporan Perekonomian Indonesia*. Jakarta: Bank Indonesia.

Cho, K., van Merriënboer, B., Gulcehre, C., Bahdanau, D., Bougares, F., Schwenk, H., & Bengio, Y. (2014). Learning phrase representations using RNN encoder-decoder for statistical machine translation. *Proceedings of EMNLP 2014*.

Hendrawati, T., Marthendra, K., Simanjuntak, B. R. J., & Pravitasari, A. A. (2026). LSTM and GRU in rice prediction for food security in Indonesia. *BAREKENG: Journal of Mathematics and Its Applications*, 20(1), 55–68. https://doi.org/10.30598/barekengvol20iss1pp0055-0068

Hochreiter, S., & Schmidhuber, J. (1997). Long short-term memory. *Neural Computation*, 9(8), 1735–1780.

Kementerian Perdagangan. (2024). *Pusat Informasi Harga Pangan Strategis (PIHPS)*. Jakarta: Kementerian Perdagangan Republik Indonesia.

Lestari, D. R., Bangun, E. A. S., Gaol, F. L., & Matsuo, T. (2025). Machine learning-based forecasting of agricultural commodity prices using ensemble models. *Journal of Human, Earth, and Future*, 6(4), 887–899.

Manogna, R. L., Dharmaji, V., & Sarang, S. (2025). Enhancing agricultural commodity price forecasting with deep learning. *Scientific Reports*, 15, 20903. https://doi.org/10.1038/s41598-025-05103-z

Murtani, Kobi, D., & Imelda. (2026). Multi-commodity food price forecasting ahead of Eid Al-Fitr in Indonesia (2026–2030): A comparative study of machine learning algorithms using time-series data. *MALCOM: Indonesian Journal of Machine Learning and Computer Science*, 6(1), 404–413. https://doi.org/10.57152/malcom.v6i1.2572

Utama, D., & Sari, D. N. (2026). Multi-horizon LSTM forecasting of Indonesian food commodity prices to support the Free Nutritious Meal (MBG) program. *TEKNIKA*, 15(1), 123–129. https://doi.org/10.34148/teknika.v15i1.1453

Wang, Z., French, N., James, T., Schillaci, C., Chan, F., Feng, M., & Lipani, A. (2023). Climate and environmental data contribute to the prediction of grain commodity prices using deep learning. *Journal of Sustainable Agriculture and Environment*, 2(1). https://doi.org/10.1002/sae2.12041
