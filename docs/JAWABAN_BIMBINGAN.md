# Jawaban Bimbingan — Inti Masalah & Solusi

> Draft jawaban lisan, versi final, buat dibawa ke bimbingan/penguji.

---

## Pembuka: Cerita Nyata (Belanja Ayam)

> "Saya kasih contoh yang pernah terjadi, pak. Waktu itu saya belanja ayam untuk usaha. Kemarin harganya Rp48.000 per kg, hari ini harganya sudah Rp50.000 per kg. Naik Rp2.000 — cuma sekitar 4 persen — dalam satu malam."

> "Unitnya per kilogram, pak — bukan per ekor. Kalau per ekor bisa beda karena bobotnya beda, jadi ukuran yang adil untuk membandingkan harga adalah per kilogram."

> "Modal yang saya bawa cuma pas-pasannya untuk rencana belanja kemarin. Karena harga naik, uang saya tidak cukup untuk beli jumlah yang sama. Saya harus pilih: beli lebih sedikit, atau pakai uang cadangan yang sebenarnya untuk kebutuhan lain."

---

## Inti Masalah

> "Nah, pengalaman kecil ini yang jadi inti masalahnya, pak. UMKM kuliner itu setiap hari membeli bahan baku tanpa tahu apakah harga hari ini naik atau turun. Ketika harga naik tak terduga, modal yang sudah direncanakan jadi tidak cukup, harga jual tidak bisa langsung dinaikkan karena takut pelanggan kabur, dan akibatnya margin laba menipis. Diulang setiap hari, ini menggerus keberlangsungan usaha."

---

## Kenaikan Per Hari (Angka Konkret)

> "Contohnya, pak. Harga cabai merah kemarin Rp40.000 per kg. Hari ini naik 12 persen jadi Rp44.800 per kg. Kalau warung sambal butuh 2 kg per hari, itu tambahan Rp9.600 per hari, atau Rp288.000 per bulan di luar rencana."

---

## Rebutan: "Kalau Kenaikannya Cuma Sedikit?"

> "Justru kenaikan kecil itu paling sering terjadi, pak. Masalahnya bukan besar kecilnya per gram, tapi kalau dikali volume belanja harian. Nah, kayak contoh ayam tadi: 48 ribu ke 50 ribu itu cuma naik 4 persen — kelihatan sepele. Tapi itu per kilogram, dan ayam adalah bahan utama yang dibeli dalam jumlah banyak tiap hari. Kalau warung beli 10 kg per hari, naik Rp2.000 per kg = tambahan Rp20.000 per hari, atau Rp600.000 per bulan. Itu bukan sepele lagi."

> "Dan justru karena kenaikannya kecil, UMKM nggak sadar dan nggak ngitung — itu masalahnya."

---

## Rebutan: "Buat Apa Pakai Website Kalau Harga Jalan di Tempat?"

> "Nah ini yang penting, pak. Website ini bukan cuma buat tahu harga naik berapa. Yang lebih sering dipakai justru kalkulator labanya — ngitung modal per porsi, harga jual yang aman, margin, dan titik impas. Itu kebutuhan rutin setiap hari, bukan cuma pas harga naik. Jadi walau harga nggak naik sama sekali, website tetap berguna."

---

## Solusi

> "Solusinya: aplikasi web yang memprediksi harga 7 hari ke depan pakai model LSTM dan GRU, plus kalkulator modal dan laba. Jadi sebelum belanja, UMKM tahu kapan aman beli, berapa harga wajar, dan berapa modal yang perlu disiapkan."

---

## Nilai Plus / Kebaruan

> "Nilai lebih riset ini: pertama, diterapkan di tingkat lokal Kota Depok pakai data PIHPS 13 komoditas, bukan cuma nasional. Kedua, hasil prediksi tidak berhenti di angka akurasi — saya kembangkan jadi produk nyata yang menghitung laba, jadi langsung berguna untuk UMKM."

---

## Penutup (Paling Kuat)

> "Jadi simpulannya, pak: harga naik tak terduga menggerus laba, dan yang kecil justru paling sering. Solusinya aplikasi prediksi harga plus kalkulator laba — dan nilai utamanya bukan cuma pas harga naik, tapi kalkulator laba yang dipakai setiap hari. Itu yang membuat website ini tetap berguna walau kenaikan kecil."

---

## Versi Super Singkat (≤30 Detik)

> "Masalahnya harga bahan baku naik tak terduga dan menggerus laba UMKM. Solusinya aplikasi web yang memprediksi harga 7 hari ke depan plus kalkulator laba. Nilai plusnya: diterapkan di Depok dengan data lokal, dan hasil risetnya jadi produk yang langsung bisa dipakai UMKM."

---

## Ringkasan 1 Kalimat

> "Inti masalahnya: UMKM kuliner membeli bahan baku setiap hari tanpa tahu harga akan naik atau turun, sehingga saat harga naik tak terduga, modal tidak cukup dan laba menggerus. Solusinya: aplikasi prediksi harga plus kalkulator laba."

---

# Lampiran: Penjelasan ML

## Model yang dipakai

> "Model yang saya pakai adalah deep learning, dua arsitektur: LSTM (Long Short-Term Memory) dan GRU (Gated Recurrent Unit). Keduanya jaringan saraf berulang (RNN) yang punya memori, jadi cocok untuk data harga harian yang berurutan."

## Kenapa RNN/LSTM/GRU

> "Karena harga hari ini bergantung pada harga hari-hari sebelumnya, pak. RNN punya memori — dia baca data urut dan bawa informasi dari langkah sebelumnya ke langkah berikutnya. Jadi bisa menangkap pola, misalnya harga naik beberapa hari berturut-turut atau ada pola musiman."

## Kenapa bukan RNN biasa

> "RNN standar punya masalah: informasi lama makin lama makin hilang — namanya masalah gradien hilang. LSTM dan GRU muncul untuk mengatasi ini. Mereka punya gerbang yang mengatur informasi apa yang perlu diingat dan apa yang dibuang."

## Beda LSTM vs GRU

> "LSTM punya tiga gerbang — input, forget, dan output. GRU cuma dua — reset dan update. GRU lebih ringan dan lebih cepat dilatih, tapi kinerjanya hampir setara dengan LSTM. Makanya dua-duanya saya bandingkan, biar fair."

## Cara kerja di proyek

> "Model saya kasih jendela 30 hari data masa lalu, lalu dia belajar dari data itu untuk memprediksi 7 hari ke depan. Latihannya menggunakan data harga PIHPS Depok 2020–2026, dan diuji dengan data yang belum pernah dilihat model."

## Metrik evaluasi

> "Untuk melihat bagus tidaknya prediksi, saya pakai tiga ukuran: MAE dan RMSE (selisih prediksi vs harga asli, dalam rupiah per kg), serta MAPE (selisih dalam persen)."

## Nilai plus di sisi ML

> "Saya juga uji dua paket fitur: yang cuma pakai harga, dan yang harga + cuaca + kalender Indonesia. Jadi terlihat apakah menambah data cuaca dan hari libur benar-benar meningkatkan akurasi."

## Draf lisan singkat

> "Model yang saya pakai adalah deep learning, dua arsitektur: LSTM dan GRU. Keduanya jaringan saraf berulang yang punya memori, jadi cocok buat data harga harian yang berurutan. Saya kasih model data 30 hari terakhir, dia belajar, lalu memprediksi harga 7 hari ke depan. Kualitas prediksi diukur pakai MAE, RMSE, dan MAPE. Saya juga bandingin LSTM vs GRU, dan uji apakah nambah fitur cuaca dan kalender meningkatkan akurasi."
