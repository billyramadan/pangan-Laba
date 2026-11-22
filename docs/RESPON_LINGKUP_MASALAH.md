# Respon: "Kalau Kenaikannya Sedikit, Ngapain Pakai Website?"

> Dokumen jawaban lisan untuk sesi bimbingan. Menjawab tantangan dosen pembimbing:
> "Billy, kamu harus punya lingkup masalah yang besar terkait website ini yang berguna untuk UMKM.
> Ngapain kalau naiknya sedikit harus pakai website? Berarti sama aja website-mu nggak berguna."

---

## 1. Reframe: Bukan "Prediksi Harga", tapi "Stabilitas Margin UMKM"

Pernyataan yang salah memposisikan proyek:

> "Saya buat website untuk memprediksi harga, supaya UMKM tahu harga naik berapa."

Ini yang diserang dospem — kalau naiknya sedikit, prediksi terasa kecil.

Pernyataan yang benar (lingkup besar):

> "Masalahnya bukan 'harga naik berapa'. Masalahnya: **volatilitas biaya bahan baku menggerus margin tipis UMKM kuliner, dan ini terjadi dalam skala besar di Depok.** Website ini adalah instrumen untuk melindungi kestabilan margin — prediksi harga hanyalah salah satu alat di dalamnya."

Prediksi bukan tujuan, melainkan senjata untuk masalah yang jauh lebih besar: **ketahanan finansial UMKM**.

---

## 2. Bantahan: "Naiknya Sedikit"

### 2.1 Sedikit per kg ≠ sedikit per usaha

Angka kecil per kilogram, dikali volume belanja harian, jadi nominal besar:

- Ayam naik Rp 2.000/kg (4%). Warung beli 10 kg/hari → +Rp 20.000/hari → **Rp 600.000/bulan** di luar rencana.
- Untuk UMKM dengan modal pas-pasan, ini setara beberapa hari keuntungan yang hilang.

### 2.2 Sedikit di hari biasa ≠ sedikit di hari tertentu

Rata-rata kenaikan harian memang kecil — karena mayoritas hari tenang. Tapi kerugian justru terpusat di **sedikit hari lonjakan**:

- Menjelang Idulfitri, cuaca ekstrem, gangguan pasokan: harga bisa melonjak 12–30% dalam hitungan hari.
- Tugas prediksi bukan menebak hari tenang, melainkan **menandai hari-hari lonjakan itu lebih awal**. Kalau hanya dilihat rata-ratanya, justru hari yang paling menyakitkan yang luput.

### 2.3 Akumulasi: kecil yang berulang jadi besar

Kenaikan kecil bukan berdiri sendiri. Diulang tiap minggu, terakumulasi menjadi pergeseran besar:

- Keranjang bahan baku naik 5–8% dalam sebulan/seperempat.
- Prediksi memberi *lead time* untuk membeli sebelum tren terakumulasi, bukan reaktif setelah naik.

### 2.4 Amplitudo margin: perubahan kecil × margin tipis = dampak besar

Ukuran yang adil bukan "berapa rupiah naik", melainkan **rasio perubahan biaya vs margin**:

- Margin bersih UMKM kuliner umumnya 5–15%.
- Kenaikan bahan baku 5–8% bisa menghapus seluruh laba pada minggu itu.
- Jadi meski angkanya kecil secara absolut, dampaknya relatif **besar** di usaha bermargin tipis.

### 2.5 Nilai arah > nilai presisi

UMKM tidak butuh "tepat berapa rupiah". Mereka butuh keputusan:

- Apakah harga naik atau turun, dan kira-kira kapan?
- Belanja sekarang, tunda, atau ganti bahan?

Prediksi yang tidak sempurna pun tetap berguna untuk keputusan urutan belanja dan penetapan harga jual yang aman.

---

## 3. Lingkup Besar: Siapa dan Berapa Banyak?

Lingkup masalah bukan "satu warung", tapi **skala kota**:

- Depok berada di Jabodetabek; jumlah UMKM kuliner terus bertumbuh.
- Banyak margin tipis terkikis secara agregat = kerapuhan ekonomi lokal.
- Selaras prioritas pemerintah: Bank Indonesia mengelompokkan bahan pangan sebagai komponen inflasi *volatile food* yang kerap jadi penyumbang inflasi terbesar.
- Dampak kolektif: stabilitas harga pangan → stabilitas usaha → stabilitas lapangan kerja lokal.

Jadi harmoni masalahnya: **mengurangi kerentanan finansial ribuan UMKM kuliner terhadap gejolak harga pangan — di tingkat kota.**

---

## 4. Kenapa Website (bukan Excel/manual)?

- **Otomatisasi pipeline data:** prediksi hanya bekerja jika data PIHPS + cuaca + kalender diperbarui harian. Excel statis tidak bisa menarik data ini otomatis.
- **Menurunkan hambatan:** mayoritas UMKM bahkan belum menghitung margin secara rutin (data wawancara, B2). Website menghitung otomatis, jadi mereka benar-benar menjalankan aritmetika itu tiap hari.
- **Satu tempat:** prediksi + kalkulator laba + riwayat. Tanpa website, alat-alat ini tersebar dan tidak terpakai.
- **Akses via browser HP:** tanpa instalasi, cocok perangkat entry-level.

---

## 5. Pengakuan Jujur (Menjaga Kredibilitas)

- Hasil model: GRU harga-saja terbaik, MAPE ≈ 3,5%; fitur eksternal belum terbukti menolong pada data ini.
- Karena itu nilai produk **tidak** bertumpu pada klaim akurasi tinggi, melainkan pada **alat margin yang rutin dan berguna** dengan overlay prediksi.
- Ini menjawab "kalau harga jalan di tempat": **kalkulator laba tetap berguna setiap hari, bahkan saat harga tidak naik sama sekali.**

---

## 6. Versi Lisan Singkat (≤60 detik)

> "Dospem, masalahnya bukan 'harga naik berapa'. Masalahnya adalah volatilitas biaya bahan baku yang menggerus margin tipis UMKM kuliner, dan ini terjadi dalam skala besar di Depok. Naik Rp 2.000 per kg untuk ayam terlihat kecil, tapi warung yang beli 10 kg per hari kehilangan Rp 600.000 per bulan. Kecil per kilogram itu kelipatan volume belanja harian, dan terakumulasi. Plus margin UMKM cuma 5–15 persen, jadi kenaikan bahan 5–8 persen bisa menghapus seluruh laba seminggu. Prediksi tidak cuma memberi tahu 'naik berapa' — ia menandai hari-hari lonjakan (Idulfitri, cuaca) lebih awal, dan memberi lead time untuk beli sebelum naik. Website ini bukan sekadar prediksi; ia instrumen perlindungan margin. Dan karena kebanyakan UMKM belum menghitung margin sama sekali, website yang menghitung otomatis justru menurunkan hambatan dan membuat mereka benar-benar menghitung tiap hari. Jadi lingkup masalahnya besar: ketahanan finansial ribuan UMKM kuliner Depok terhadap gejolak harga pangan."
