# Naskah Lisan Presentasi — PanganLaba (13 slide)

> Baca pelan, jeda 1 detik tiap koma, 2 detik tiap titik. Angka dibaca seperti tertulis.
> Slide 5–7 = bagian Food Price Forecasting (fokus utama). Sisanya ringkas.

---

## Slide 1 — Sampul

"Selamat pagi, Pak. Saya akan mempresentasikan tugas akhir saya, PanganLaba. Judul lengkapnya: Prediksi Harga Komoditas Pangan Strategis Menggunakan LSTM dan GRU untuk Mendukung Keputusan Belanja dan Analisis Laba Menu UMKM Kuliner. PanganLaba adalah platform yang membantu UMKM kuliner memantau dan memprediksi harga bahan pangan, agar belanja bahan baku lebih tepat waktu."

---

## Slide 2 — Permasalahan

"Masalahnya dekat dengan kehidupan UMKM kuliner. Contoh: kemarin ayam Rp48.000 per kilogram, hari ini Rp50.000. Kelihatan cuma naik Rp2.000, tapi kalau warung pakai 10 kilogram per hari, berarti tambahan Rp20.000 per hari, Rp600.000 per bulan. Belum lagi cabai: Rp40.000 naik jadi Rp44.800, naik 12 persen. UMKM baru tahu harga ini saat sudah di pasar. Dampaknya, biaya produksi naik, tapi harga jual sulit dinaikkan karena takut kehilangan pelanggan. Akhirnya margin habis."

---

## Slide 3 — Solusi

"Solusinya ada tiga lapisan yang menyatu. Pertama, prediksi harga 7 hari ke depan memakai model LSTM dan GRU, dengan bantuan data cuaca dan kalender. Kedua, perencanaan pembelian: sistem memberi saran kapan beli dan kapan tunda. Ketiga, perhitungan harga pokok produksi dan margin per menu. Manfaatnya: beli saat harga murah, stok tidak menumpuk, harga jual aman, margin terjaga."

---

## Slide 4 — Fitur Utama & Alur Kerja

"Ada tiga fitur inti: Food Price Forecasting untuk prediksi harga, Smart Purchasing Planning untuk perencanaan belanja, dan Menu Profitability Analysis untuk analisis laba menu. Alurnya: input dari data PIHPS Depok, cuaca ERA5, dan kalender Indonesia; masuk ke model LSTM atau GRU dengan jendela 30 hari; keluar prediksi 7 hari; lalu jadi saran beli atau tunda, sampai ke perhitungan margin. Di kanan ada tampilan dashboard asli, bukan desain konsep."

---

## Slide 5 — Data & Pengolahan (FPF 1/3)

"Saya mulai dari data apa yang dipakai, dari mana, dan bagaimana diolah.

Data utamanya adalah harga komoditas pangan strategis dari PIHPS, Pusat Informasi Harga Pangan Strategis, Bank Indonesia, khusus wilayah Kota Depok. Jumlahnya 20.824 observasi, untuk 16 komoditas, rentang 2 Januari 2020 sampai 10 November 2026, dalam rupiah per kilogram. Dari 16 komoditas itu, 13 punya riwayat cukup panjang untuk dilatih model; 3 sisanya baru 15 observasi, belum cukup. Tiga komoditas yang belum masuk itu adalah Gula Pasir, Cabai Merah Besar, dan Cabai Merah Keriting. Alasannya sederhana: model butuh jendela 30 hari untuk memprediksi 7 hari ke depan, sementara data 15 hari terlalu pendek untuk membentuk pola. Jadi eksperimen dan model aktif hanya memakai 13 komoditas yang datanya cukup panjang.

Data pendukung pertama adalah cuaca harian dari model reanalisis ERA5, diambil lewat API Open-Meteo. Ini data grid pada satu titik di Depok, bukan pengukuran stasiun BMKG. Enam variabel: suhu rata-rata, maksimum, minimum, presipitasi, angin maksimum, dan radiasi matahari. Cakupannya 2.491 tanggal.

Data pendukung kedua adalah kalender Indonesia: hari libur nasional, cuti bersama, akhir pekan, dan tanggal Idulfitri. Perlu saya jujur, sumber kalender ini tidak menandai periode Ramadan maupun hari-hari menjelang Idulfitri, jadi itu memang belum tersedia.

Cara pengolahannya begini. Pertama, validasi: tanggal dan harga yang tidak valid dibuang, harga wajib positif, data duplikat dirata-ratakan. Kedua, data disatukan ke kalender harian penuh, lalu digabung dengan cuaca dan kalender. Ketiga, nilai yang hilang diisi dengan interpolasi linear, hanya di dalam rangkaian data, tidak menebak ke depan atau ke belakang. Keempat, normalisasi memakai StandardScaler, dan scaler ini hanya dipasang pada data latih, agar data uji tidak bocor ke proses pelatihan.

Terakhir, saya bedakan dua jenis fitur. Fitur utama adalah riwayat harga itu sendiri: harga hari ini, harga satu hari lalu, tujuh hari lalu, plus rata-rata 7 dan 30 hari. Fitur tambahan adalah cuaca ERA5, kalender, dan siklus hari serta bulan. Kenapa fitur tambahan itu ditambahkan? Secara konsep: suhu dan radiasi memengaruhi produktivitas pertanian, presipitasi ekstrem berpotensi mengganggu pasokan, libur nasional dan Idulfitri memicu lonjakan permintaan, dan siklus hari-bulan menangkap pola pasar yang berulang. Tujuannya satu: agar model bisa mengenali pola perubahan harga, bukan hanya menghafal angka."

---

## Slide 6 — Model LSTM vs GRU (FPF 2/3)

"Sekarang saya jelaskan mengapa memilih LSTM dan GRU, serta bagaimana keduanya bekerja.

Alasannya sederhana. Harga pangan adalah data yang berurutan menurut waktu. Nilai hari ini dipengaruhi nilai hari-hari sebelumnya. LSTM dan GRU adalah jaringan saraf yang memang dirancang untuk data berurutan seperti ini. Keduanya bisa menyimpan memori dari masa lalu, sehingga bisa belajar pola historis, misalnya kenaikan menjelang hari raya atau pola musiman. Keduanya juga mengatasi masalah yang disebut vanishing gradient, yaitu kondisi di mana jaringan saraf biasa lupa informasi dari masa lalu.

Bagaimana cara kerja LSTM? LSTM punya sel memori yang dikontrol oleh tiga gerbang. Gerbang input menulis informasi baru. Gerbang forget membuang informasi lama yang tidak berguna. Gerbang output mengeluarkan hasil. Karena kontrolnya lebih kaya, LSTM lebih ekspresif, tetapi parameternya lebih banyak sehingga sedikit lebih berat.

Bagaimana cara kerja GRU? GRU adalah versi ringkas LSTM dengan hanya dua gerbang, yaitu reset dan update. Parameternya lebih sedikit, sehingga lebih efisien dan lebih cepat dilatih, dan akurasinya sering sebanding dengan LSTM.

Bagaimana keduanya diterapkan di penelitian ini? Model menerima riwayat 30 hari terakhir sebagai masukan, lalu memprediksi harga 7 hari ke depan. Arsitekturnya: satu lapisan LSTM atau GRU dengan 48 unit, lalu dropout 15 persen untuk mencegah overfitting, satu lapisan padat 32 unit dengan aktivasi ReLU, dan lapisan keluaran 7 nilai. Pelatihan memakai optimizer Adam, fungsi kerugian mean squared error, dan seed tetap 42 agar hasil bisa diperbandingkan. Data tiap komoditas dibagi secara kronologis, 80 persen latih dan 20 persen uji, bukan acak. Total ada 52 eksperimen: 13 komoditas, dua model, dua paket fitur.

Kenapa keduanya layak dibandingkan? Karena sama-sama jaringan saraf berulang berbasis gerbang, jadi perbandingannya adil. Perbedaannya hanya pada kompleksitas dan efisiensi. Pemilihan ini saya dasarkan pada karakteristik data deret waktu, bukan pada hasil akhir."

---

## Slide 7 — Alur Proses Prediksi (FPF 3/3)

"Terakhir, saya rangkai alur lengkapnya, sesuai yang benar-benar terjadi di kode.

Langkah pertama, pengumpulan data: harga PIHPS Kota Depok, cuaca ERA5, dan kalender Indonesia.

Langkah kedua, preprocessing dan normalisasi: validasi, penyatuan ke kalender harian, interpolasi nilai hilang, dan normalisasi StandardScaler pada data latih.

Langkah ketiga, pembentukan fitur dan dataset time series: setiap contoh masukan adalah riwayat 30 hari, dan targetnya adalah harga 7 hari ke depan.

Langkah keempat, pembagian data secara kronologis, 80 persen latih dan 20 persen uji.

Langkah kelima, pelatihan LSTM dan GRU, lalu evaluasi memakai MAE, RMSE, dan MAPE pada bagian uji yang belum pernah dilihat model.

Langkah keenam, model di-fit ulang dengan seluruh histori yang tersedia, supaya model operasional memakai semua data, bukan hanya bagian latih.

Langkah ketujuh, prediksi harga 7 hari ke depan dari 30 hari fitur terakhir. Hasil prediksi ini menjadi dasar bagi fitur perencanaan belanja dan analisis laba menu, meskipun hari ini saya tidak membahas kedua fitur itu.

Grafik di kolom kanan menunjukkan contoh nyata: harga aktual cabai merah dibanding prediksi satu hari ke depan. Garis prediksi mengikuti pergerakan aktual, termasuk saat lonjakan.

Saya juga ingin menyampaikan hasil evaluasinya secara jujur. Pada evaluasi terbaru, GRU dengan fitur harga saja memberikan error median terkecil: MAPE sekitar 3,48 persen, MAE sekitar Rp976 per kilogram, RMSE sekitar Rp2.318. LSTM dengan harga saja sekitar 4,76 persen MAPE. Artinya, rata-rata kesalahan prediksi GRU terhadap harga aktual sekitar 3,5 persen. Evaluasi ini dilakukan pada data uji holdout dari 16 Juni 2025 sampai 10 November 2026, dengan 52 model. Perlu saya tegaskan: penambahan paket cuaca dan kalender sekaligus belum memperbaiki error keseluruhan pada run ini.

Dan ini yang belum bisa saya simpulkan. Pertama, pengaruh tiap fitur eksternal belum terpisahkan, karena ketiganya digabung sekaligus. Kedua, evaluasi baru satu kali dengan satu seed, jadi belum ada uji stabilitas. Ketiga, belum ada perbandingan dengan cara paling simpel, misalnya menebak harga besok sama dengan harga kemarin. Keempat, karena prediksi tiap hari tumpang tindih, angka kesalahan saling terkait, bukan benar-benar independen. Semua ini saya catat sebagai arah evaluasi lanjutan, bukan sebagai kelemahan yang disembunyikan."

---

## Slide 8 — Pasar

"Target pengguna kami adalah UMKM kuliner. Ukurannya saya pendekati dengan kerangka TAM, SAM, SOM. TAM, seluruh UMKM kuliner Indonesia, sekitar 20,8 juta, dari asumsi 40 persen dari 52 juta UMKM. SAM, yang punya akses digital dan bahan baku volatile, sekitar 12,5 juta. SOM, target awal kami di Kota Depok, sekitar 500 pelanggan dalam 2 sampai 3 tahun, yaitu 3 sampai 5 persen dari SAM. Angka ini campuran data resmi dan asumsi yang saya nyatakan terbuka."

---

## Slide 9 — Validasi

"Data dari pengguna belum ada, jadi yang saya tunjukkan adalah rencana validasinya, bukan hasil. Ada enam dimensi yang akan saya tanyakan: frekuensi kenaikan harga, dampaknya ke keuntungan, kebiasaan waktu belanja, cara menghitung harga pokok produksi, kebutuhan prediksi 7 hari, dan ketertarikan memakai aplikasi dengan skala Likert. Respondennya pelaku UMKM kuliner Kota Depok, anonim."

---

## Slide 10 — Kompetitor

"Ada enam kompetitor yang saya bandingkan, diverifikasi dari situs resminya. RacikLaba.id menyediakan analisis menu dan harga pokok produksi, tetapi tanpa prediksi harga. PIHPS, Tridge, dan DTN hanya menyediakan data, tanpa alat keputusan. Qasir dan Majoo kuat di kasir dan inventori, tapi tanpa prediksi harga, dan harga pokok produksinya manual. PanganLaba unggul di prediksi berbasis LSTM dan GRU, harga pokok produksi otomatis per menu, dan analisis keuntungan menu. Saya juga jujur: kami belum punya manajemen stok."

---

## Slide 11 — Keunggulan

"Enam pembeda kami. Satu, prediksi plus keputusan, bukan sekadar angka. Dua, model LSTM dan GRU sudah diuji pada data lokal Depok, dan GRU harga-saja memberi hasil terbaik. Tiga, fitur eksternal seperti cuaca dan kalender diuji pengaruhnya, dan hasilnya saya laporkan apa adanya. Empat, harga terhubung langsung ke harga pokok produksi. Lima, analisis per menu. Keenam, fokus UMKM kuliner, sederhana, bahasa Indonesia, dan jalan di browser HP tanpa instalasi."

---

## Slide 12 — Bisnis

"Model bisnisnya sesuai kode aplikasi. Awalnya trial 7 hari gratis, login dengan Google, tanpa kartu kredit. Setelah trial, ada satu paket berbayar, Starter, Rp150.000 per bulan, komoditas tidak terbatas. Pembayaran manual lewat transfer, dikonfirmasi admin. Untuk asumsi pendapatan, saya pakai ARPU Rp150.000 dan konversi asumsi 2 sampai 5 persen dari sekitar 500 pelanggan, jadi potensi Rp9 sampai 22,5 juta per tahun. Ini target simulasi, bukan proyeksi realisasi."

---

## Slide 13 — Penutup

"Simpulannya: masalahnya adalah fluktuasi harga bahan yang menggerus margin UMKM kuliner. Solusinya, prediksi harga dengan LSTM dan GRU, ditambah perencanaan belanja dan analisis margin per menu. Targetnya UMKM kuliner, awal di Depok, lalu nasional. Roadmap lima tahap: penyempurnaan website, pengumpulan data, pengujian model, uji coba ke UMKM, dan evaluasi produk. Dengan PanganLaba, UMKM bisa belanja saat harga tepat dan mengambil keputusan berbasis data. Terima kasih, saya siap menerima masukan."

---

## Referensi cepat kalau ditanya di tengah

- Data harga: PIHPS Bank Indonesia, Kota Depok, 20.824 observasi, 16 komoditas, 2020-01-02 – 2026-11-10, Rp/kg.
- Cuaca: ERA5 lewat Open-Meteo, 6 variabel, 2.491 tanggal, grid (-6,5; 106,75), bukan stasiun BMKG.
- Kalender: libur nasional, cuti bersama, akhir pekan, Idulfitri. Ramadan & menjelang Idulfitri belum tersedia.
- Model: jendela 30 hari → prediksi 7 hari; LSTM/GRU 48 unit; dropout 0,15; Adam + MSE; seed 42; split kronologis 80:20; 52 eksperimen.
- Hasil: GRU harga-saja MAPE ≈ 3,48%, MAE ≈ Rp976, RMSE ≈ Rp2.318; LSTM harga-saja MAPE ≈ 4,76%.
- Belum: isolasi tiap fitur eksternal, uji multi-seed/rolling-origin, baseline Naive/ARIMA.
