# Penjelasan Per Slide: Deck PanganLaba

> Naskah presentasi lisan, 10 slide, urut. Tiap slide: apa yang ditampilkan + penjelasan lisan + kaitan ke 6 tuntutan dosen.

---

## Slide 1: Sampul

**Ditampilkan:** Logo, nama produk, judul penelitian lengkap, tangkapan layar beranda asli website, institusi.

**Penjelasan lisan:**
"Selamat pagi, Pak. Pada kesempatan ini, saya akan mempresentasikan tugas akhir saya yang bernama PanganLaba. PanganLaba adalah sebuah platform yang dapat memperkirakan harga bahan pangan untuk membantu UMKM kuliner. Judul lengkapnya adalah Prediksi Harga Komoditas Pangan Strategis Menggunakan LSTM dan GRU untuk Mendukung Keputusan Belanja dan Analisis Laba Menu UMKM Kuliner. Di sebelah kanan, Pak dapat melihat tampilan asli website yang sudah berjalan, bukan sekadar desain konsep."

---

## Slide 2: Latar Belakang / Masalah

**Ditampilkan:** Contoh kasus ayam & cabai, 4 titik nyeri, inti masalah.

**Penjelasan lisan:**
"Jadi, permasalahan yang saya angkat sebenarnya cukup dekat dengan kehidupan sehari-hari pelaku UMKM kuliner, yaitu harga bahan baku pangan yang sering berubah dan sulit diprediksi.

Contohnya seperti harga ayam dan cabai, Pak. Dua bahan ini hampir setiap hari dibutuhkan oleh banyak usaha kuliner. Misalnya, harga ayam kemarin Rp48.000 per kilogram, kemudian hari ini naik menjadi Rp50.000. Kelihatannya memang hanya naik Rp2.000, tetapi kalau sebuah warung membutuhkan 10 kilogram ayam setiap hari, berarti ada tambahan pengeluaran Rp20.000 per hari. Kalau dihitung selama satu bulan, tambahan biayanya bisa mencapai Rp600.000.

Belum lagi cabai, Pak. Misalnya harga cabai naik dari Rp40.000 menjadi Rp44.800 per kilogram. Kalau warung membutuhkan 2 kilogram setiap hari, tentu pengeluaran untuk bahan baku juga ikut bertambah.

Nah, yang menjadi masalah adalah kenaikan harga seperti ini sering kali tidak bisa diperkirakan oleh pelaku UMKM. Mereka biasanya baru mengetahui perubahan harga ketika sudah datang ke pasar atau ketika akan membeli bahan baku.

Dampaknya cukup besar, Pak. Ketika harga bahan baku naik, otomatis biaya produksi ikut meningkat. Sementara itu, pelaku UMKM tidak bisa sembarangan menaikkan harga jual makanan karena harus mempertimbangkan pelanggan dan daya beli masyarakat. Akhirnya, keuntungan yang seharusnya mereka dapatkan justru semakin berkurang."

**Kaitan tuntutan dosen:** Masalahnya disajikan secara jelas, disertai kasus nyata, angka yang konkret, dan rantai sebab-akibat yang runtut.

---

## Slide 3: Solusi

**Ditampilkan:** Tiga solusi menyatu + strip manfaat langsung.

**Penjelasan lisan:**
"Solusi yang saya tawarkan terdiri dari tiga lapisan yang menyatu menjadi satu alur harian. Pertama, prediksi harga tujuh hari ke depan. Dengan menggunakan model LSTM dan GRU, ditambah fitur eksternal seperti cuaca dan kalender, sistem dapat memperkirakan harga tiga belas komoditas pangan strategis. Dengan begitu, UMKM bisa tahu kapan waktu yang aman untuk membeli atau menunda pembelian. Kedua, perencanaan pembelian. Sistem memberikan saran kapan dan berapa banyak belanja, berdasarkan hasil prediksi dan ambang perubahan harga. Ini menggantikan cara lama yang masih tebak-tebakan. Ketiga, perhitungan harga pokok produksi dan analisis menu. Biaya per porsi, harga jual yang aman, margin, dan keuntungan setiap menu dihitung secara otomatis.

Manfaat langsungnya, UMKM bisa membeli saat harga lebih murah, stok tidak menumpuk, harga jual tetap aman, dan margin terlindungi. Semuanya cukup dari satu aplikasi."

**Kaitan tuntutan dosen:** Solusi yang ditawarkan relevan, karena bukan sekadar membuat website, melainkan bagaimana sistem tersebut memberikan manfaat nyata bagi pengguna.

---

## Slide 4: Fitur Utama & Alur Kerja

**Ditampilkan:** Tiga fitur inti, alur kerja INPUT → MODEL → PREDIKSI → KEPUTUSAN, dashboard asli.

**Penjelasan lisan:**
"Fitur inti ada tiga: Food Price Forecasting untuk memperkirakan harga, Smart Purchasing Planning untuk mengatur belanja, dan Menu Profitability Analysis untuk menghitung keuntungan menu. Alur kerjanya dari kiri ke kanan. Pertama, input, yaitu data PIHPS Depok, cuaca ERA5, dan kalender Indonesia. Kedua, model, yaitu LSTM atau GRU dengan jendela tiga puluh hari, untuk memperkirakan tujuh hari ke depan. Ketiga, prediksi, yaitu harga tiga belas komoditas dengan ambang plus minus lima persen, sehingga muncul saran untuk membeli atau menunda. Keempat, keputusan, yaitu perencanaan belanja, perhitungan harga pokok produksi dan margin, serta penentuan harga jual yang aman.

Di sebelah kanan adalah dashboard asli PanganLaba, bukan mockup. Output-nya berupa rekomendasi belanja dan informasi margin, yang diperbarui setiap hari."

**Kaitan tuntutan dosen:** Solusi relevan karena cara kerja sistemnya terukur, bukan sekadar klaim.

---

## Slide 5: Pasar

**Ditampilkan:** KPI ukuran pasar + TAM/SAM/SOM.

**Penjelasan lisan:**
"Target pengguna kami adalah UMKM kuliner. Sekarang saya sampaikan ukuran pasarnya. Total UMKM Indonesia ada 52 juta, dan saya asumsikan 40 persennya bergerak di bidang kuliner, sehingga sekitar 20,8 juta UMKM kuliner. Khusus untuk Kota Depok, jumlah UMKM diperkirakan sekitar 45 ribu, dengan populasi Depok sebesar 2,168 juta jiwa menurut BPS tahun 2025.

Untuk mengukur pasar, saya menggunakan pendekatan TAM-SAM-SOM. TAM adalah total seluruh UMKM kuliner, sekitar 20,8 juta. Dari situ, SAM, yaitu pasar yang benar-benar bisa dilayani, sekitar 60 persen dari TAM yang memiliki akses digital dan bahan-bahan yang volatil, sehingga sekitar 12,5 juta. Sedangkan target awal kami, SOM, adalah sekitar 3 sampai 5 persen dari SAM dalam waktu 2 sampai 3 tahun, yaitu sekitar 500 pelanggan. Perlu digarisbawahi, saya tidak menganggap semua UMKM sebagai calon pengguna. Angka-angka ini bersumber dari data aktual ditambah asumsi penetrasi yang saya sampaikan secara eksplisit."

**Kaitan tuntutan dosen:** Target pasar terukur, dengan kerangka TAM/SAM/SOM dan asumsi yang dinyatakan secara jelas.

---

## Slide 6: Validasi

**Ditampilkan:** 6 dimensi rencana wawancara & kuesioner, status belum ada data.

**Penjelasan lisan:**
"Jujur, data dari pengguna belum tersedia. Oleh karena itu, di sini saya menampilkan rencana validasinya, bukan hasil yang dibuat-buat. Ada enam dimensi yang akan saya tanyakan kepada responden: frekuensi kenaikan harga dalam satu bulan terakhir, dampaknya terhadap keuntungan, kebiasaan waktu belanja, cara mereka menghitung harga pokok produksi dan laba selama ini, kebutuhan prediksi tujuh hari, serta ketertarikan menggunakan aplikasi dengan skala Likert. Respondennya adalah pelaku UMKM kuliner Kota Depok, dan identitasnya anonim. Ini penting agar masalah dan solusi divalidasi langsung dari mulut pengguna, bukan hanya asumsi saya."

---

## Slide 7: Kompetitor

**Ditampilkan:** Tabel PanganLaba vs 6 produk lain, 8 kolom fitur, persamaan & keterbatasan.

**Penjelasan lisan:**
"Kompetitor yang saya analisis semuanya sudah diverifikasi dari situs resminya per 17 November 2026. Ada RacikLaba.id, PIHPS Bank Indonesia, Qasir, Majoo, DTN, dan Tridge. Saya bandingkan dari kolom fitur, yaitu info harga, prediksi, machine learning, perencanaan belanja, inventori, harga pokok produksi, dan analisis menu.

Temuannya sebagai berikut. PIHPS, Tridge, dan DTN hanya menyediakan data, tanpa alat keputusan. Qasir dan Majoo kuat di POS dan inventori, tetapi tidak memiliki prediksi harga, dan harga pokok produksinya masih manual. PanganLaba unggul pada prediksi berbasis LSTM/GRU, harga pokok produksi otomatis per menu, dan analisis keuntungan menu. Namun, saya juga jujur mengenai keterbatasan, yaitu kami tidak memiliki manajemen stok. Adapun persamaannya, semua produk sama-sama menyajikan informasi harga atau pencatatan usaha."

**Kaitan tuntutan dosen:** Kompetitor dianalisis dengan tabel fitur yang terverifikasi serta kekurangan dari masing-masing produk.

---

## Slide 8: Keunggulan

**Ditampilkan:** 6 pembeda + strip dampak & indikator.

**Penjelasan lisan:**
"Ada enam hal yang membedakan PanganLaba. Pertama, prediksi plus keputusan. Sistem tidak hanya memberikan angka harga, tetapi mengubahnya menjadi saran untuk membeli atau menunda. Kedua, model LSTM dan GRU sudah diuji pada data lokal Depok, dan GRU dengan harga saja memberikan hasil terbaik dengan median MAPE sekitar 3,5 persen. Ketiga, fitur eksternal seperti cuaca ERA5 dan kalender Indonesia juga diuji pengaruhnya, dan hasilnya saya laporkan secara jujur. Keempat, harga hingga harga pokok produksi terintegrasi. Kelima, analisis per menu, sehingga keuntungan setiap menu terukur. Keenam, fokus pada UMKM kuliner, sederhana, menggunakan bahasa Indonesia, dan dapat diakses melalui browser HP tanpa instalasi.

Dampaknya diukur melalui uji coba ke UMKM, meliputi waktu tugas, kemudahan, dan manfaat, dengan skor 1 sampai 5."

**Kaitan tuntutan dosen:** Keunggulan yang signifikan, dengan pembeda yang jelas dan berbasis evaluasi model nyata.

---

## Slide 9: Bisnis

**Ditampilkan:** Trial 7 hari, paket Starter, pembayaran manual, asumsi pendapatan.

**Penjelasan lisan:**
"Model bisnis ini sesuai dengan yang sudah ada di kode aplikasi. Awalnya, trial 7 hari gratis, login pertama menggunakan Google, tanpa kartu kredit, dan akses penuh. Setelah masa trial, ada satu paket berbayar bernama Starter, Rp150.000 per bulan. Fiturnya mencakup komoditas tidak terbatas, dashboard dasar, harga PIHPS harian, dan akses melalui browser HP tanpa instalasi. Pembayaran dilakukan secara manual melalui transfer rekening, kemudian admin melakukan konfirmasi sebelum paket aktif. Status trial, aktif, atau berakhir terlihat di dashboard.

Untuk asumsi pendapatan, saya menggunakan ARPU Rp150.000 per bulan, dengan konversi diasumsikan 2 sampai 5 persen dari SOM sekitar 500 pelanggan, sehingga potensinya Rp9 sampai 22,5 juta per tahun di Depok. Namun, ini adalah target simulasi, bukan proyeksi realisasi. Paket dan harganya baru ditetapkan setelah uji kesediaan bayar."

**Kaitan tuntutan dosen:** Model bisnisnya jelas, dengan cara menghasilkan pendapatan yang terdefinisi dan asumsi yang diberikan label.

---

## Slide 10: Penutup

**Ditampilkan:** Ringkasan, roadmap 5 tahap, penutup.

**Penjelasan lisan:**
"Jika diringkas, permasalahannya adalah fluktuasi harga bahan yang menggerus margin UMKM kuliner. Solusinya, prediksi harga menggunakan LSTM/GRU, ditambah perencanaan belanja, dan harga pokok produksi per menu. Targetnya UMKM kuliner, awalnya di Depok, kemudian berkembang ke skala nasional. Pembedanya, belum ada kompetitor dengan kombinasi serupa. Dan untuk bisnisnya, dimulai dari trial 7 hari, lalu lanjut ke langganan Starter.

Roadmap-nya terdiri dari lima tahap: penyempurnaan website dan UX, pengumpulan dan pengolahan data harga pangan, pengujian model LSTM dan GRU, uji manfaat fitur kepada UMKM, serta evaluasi dan pengembangan produk. Dengan PanganLaba, UMKM kuliner dapat membeli saat harga tepat, menjaga margin, dan mengambil keputusan berbasis data, bukan tebak-tebakan. Sekian presentasi dari saya. Terima kasih, dan saya siap menerima masukan."

---

## Referensi cepat (jika ditanya di tengah)

- Angka contoh: ayam 48→50rb/kg (+4%), 10 kg/hari = +Rp600rb/bulan; cabai 40→44,8rb/kg (+12%), 2 kg/hari = +Rp288rb/bulan.
- Model: LSTM & GRU, jendela 30 hari, horizon 7 hari, data PIHPS Depok 2020–2026, metrik MAE/RMSE/MAPE, median MAPE GRU harga-saja ≈3,5%.
- HPP = Harga Pokok Produksi: biaya total bahan untuk membuat satu porsi menu.
- Pasar: TAM 20,8 jt, SAM 12,5 jt, SOM ±500 pelanggan (asumsi).
- Bisnis: trial 7 hari, Starter Rp150.000/bln, potensi Rp9–22,5 jt/thn (simulasi).
- Sumber data: PIHPS Bank Indonesia, cuaca ERA5 Open-Meteo, kalender Indonesia, BPS Kota Depok 2025.
