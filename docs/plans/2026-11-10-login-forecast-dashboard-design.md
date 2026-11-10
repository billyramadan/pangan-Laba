# PanganLaba: Login, Prediksi, dan Dashboard UMKM

## Intent

Siapkan alur pelanggan PanganLaba yang bisa dipahami dan dipakai UMKM: masuk memakai Google, memperoleh masa trial satu kali, melihat prediksi harga dari data terbaru, dan memakai alat hitung usaha tanpa mencampur kontrol administrasi model.

## Approaches

1. **Perbaiki alur pelanggan, prediksi aktif, dan dashboard UMKM (dipilih pengguna).** Menyelesaikan masalah login, mengeluarkan prediksi dari model tersimpan atas riwayat terbaru, membatasi menu administrasi, dan merapikan tampilan HP. Ini memperbaiki fungsi inti yang dibutuhkan pelanggan dan kebutuhan skripsi.
2. **Polesan tampilan saja.** Lebih kecil, tetapi tetap menampilkan ramalan historis sebagai seolah-olah ramalan sekarang dan tidak memperbaiki akses login.
3. **Menyelesaikan seluruh SaaS termasuk pembayaran langsung.** Memerlukan akun dan rahasia gateway yang dikelola pemilik, HTTPS/hosting, serta aturan refund dan operasional. Di luar lingkup sampai pengelola mengonfigurasi layanan pembayaran.

## Goals

- Login Google menunjukkan hasil yang jelas saat konfigurasi, callback, pembatalan, atau sesi bermasalah.
- Login pertama membuat trial tujuh hari; login ulang tidak mengulang trial. Akun aktif masuk dashboard; akun kedaluwarsa melihat pilihan paket.
- Prediksi saat ini dibuat dari 30 hari data terbaru dan model LSTM/GRU tersimpan. Dashboard menampilkan tanggal data acuan dan tujuh tanggal target berikutnya.
- Jika tanggal harga terakhir lebih dari tujuh hari dari tanggal lokal Asia/Jakarta, tampilkan peringatan dan jangan tampilkan saran beli/tunda seolah data masih baru.
- Harga bahan dan kalkulator memakai kutipan harga serta prediksi dari backend aktif, bukan angka contoh statis.
- Pelanggan melihat harga, saran, kalkulator, analisis menu, dan riwayat. Upload data, pelatihan, dan hasil evaluasi model hanya tersedia untuk admin yang terdaftar, dengan pemeriksaan izin di server.
- Tata letak landing dan dashboard nyaman dipakai di HP, dengan menu ringkas, kontrol yang mudah disentuh, serta pesan memuat/kosong/error yang jelas.

## Non-goals

- Tidak membuat akun Google, menambah kredensial, atau menyimpan password pengguna.
- Tidak mengaktifkan pembayaran tanpa provider/rekening nyata yang dikonfigurasi pengelola.
- Tidak mengklaim laba, penghematan, atau rekomendasi sebagai hasil aktual atau jaminan.
- Tidak mengubah sumber data resmi atau mengunduh PIHPS otomatis; data PIHPS tetap diperbarui melalui proses impor yang ada.
- Tidak menambahkan demo pelanggan tanpa akun; pengguna sebelumnya menyatakan demo bukan prioritas.
- Tidak menambah Naive/ARIMA pada lingkup ini.

## Existing system and constraints

- Frontend vanilla HTML/CSS/JS; API Python `ThreadingHTTPServer`; akun dan riwayat memakai SQLite lokal.
- OAuth Google sudah dikonfigurasi dan endpoint login lokal sudah terbukti mengirim redirect 302 ke `accounts.google.com`. Login sampai callback berhasil masih perlu interaksi pemilik akun di browser.
- Akun trial tujuh hari, pengecekan expired, dan halaman paket sudah tersedia.
- `GET /api/forecast` membaca `reports/forecasts.csv`, yaitu prediksi holdout historis. Fungsi `forecast_next()` serta artefak model `.h5`/JSON tersedia untuk menghasilkan ramalan dari riwayat terbaru.
- Harga Depok terakhir yang ada di CSV proyek bertanggal 21 Oktober 2026. Sampai data diperbarui, umur data melampaui batas tujuh hari; UI harus menyatakan data basi dan meniadakan saran operasional.
- Model dan data harga bersama di tingkat instalasi, bukan per pelanggan. Karena itu hanya admin boleh mengimpor data atau melatih ulang model.
- Admin ditetapkan melalui `admin.emails` atau `PANGAN_ADMIN_EMAILS`; tanpa allowlist, kontrol admin tidak boleh tersedia bagi akun pelanggan.
- Paket pembayaran masih belum memiliki provider aktif. Tombol paket hanya memberi status konfigurasi yang jelas, bukan mengaku pembayaran berhasil.

## Behavior and design

### Authentication

- Pertahankan OpenID Connect Google yang sudah ada. Tampilkan teks login yang konsisten dan hapus klaim/demo pelanggan tanpa akun.
- Tangani `error` dari Google, state yang tidak cocok/kedaluwarsa, token exchange gagal, dan email yang belum diverifikasi dengan pesan ramah tanpa membocorkan rahasia server.
- Setelah callback sukses, buat atau ambil akun dan tampilkan nama serta status trial/langganan yang benar.
- Logout menghapus cookie sesi. Cookie tetap HttpOnly dan SameSite=Lax; tambahkan Secure hanya pada HTTPS.

### Current forecast and calculator

- Tambahkan API prediksi aktif yang memilih artefak model berdasarkan komoditas, LSTM/GRU, dan fitur. Bentuk input dari 30 hari terakhir pada `combined_daily.csv`; kembalikan harga acuan terakhir, tanggal data, riwayat singkat untuk grafik, tujuh ramalan bertanggal, umur data, model, dan status kebaruan.
- Prediksi hasil evaluasi tetap ada untuk tab admin/skripsi dan simulasi retrospektif; jangan gunakan hasil itu sebagai ramalan pelanggan untuk hari ini.
- Jika model hilang atau data tidak cukup, kembalikan keadaan kosong yang dapat dijelaskan; jangan jatuh ke angka demo.
- Kalkulator mengambil harga acuan dan perkiraan dari API aktif untuk setiap bahan. Harga pemasok yang dimasukkan pengguna tetap menjadi harga acuan biaya saat ini; gunakan prediksi model untuk skenario harga mendatang.
- Saat data basi, tampilkan tanggal sumber dan peringatan; jangan beri saran beli/tunda. Kalkulator masih boleh menghitung berdasarkan harga pemasok yang diisi sendiri, tetapi jangan menyebut prediksi usang sebagai harga mendatang yang valid.

### Access separation

- Bootstrap menampilkan status admin hanya sebagai informasi UI; semua endpoint upload, training, training status, dan evaluasi juga memeriksa allowlist di backend.
- Halaman pelanggan tidak menampilkan kontrol upload/training atau tab hasil penelitian. Admin tetap mendapat area penelitian untuk evaluasi dan pelatihan.
- Permintaan paket tetap mengikuti pemeriksaan expired yang ada. Tanpa konfigurasi pembayaran, tampilkan instruksi bahwa transaksi belum tersedia.

### Interface

- Pertahankan gaya warna PanganLaba. Rapikan header mobile menjadi brand, CTA trial/login, serta menu navigasi yang dapat dibuka/tutup.
- Dashboard UMKM menampilkan harga terbaru, umur data, prediksi tujuh hari, dan saran. Perbandingan metrik teknis diletakkan di area admin/penelitian.
- Ubah fitur tanya agar menggunakan kalkulasi dan kutipan API yang sedang aktif. Nyatakan bahwa jawabannya terbatas pada fitur/data di aplikasi; jangan mengesankan model percakapan eksternal.
- Sediakan status memuat, tidak tersedia, kedaluwarsa, dan error dengan aksi berikutnya yang jelas.

## Calls made by the builder

- Ambang data basi tujuh hari mengikuti rancangan yang disetujui; hitung terhadap `Asia/Jakarta`.
- Untuk kombinasi model pelanggan, sediakan pilihan yang tercatat pada model proyek; jangan memilih angka contoh atau mengganti ke model lain diam-diam.
- Uji login berakhir pada redirect/callback yang bisa diverifikasi secara lokal; pemilik perlu menyelesaikan pemilihan akun Google sendiri.
- Gunakan implementasi frontend/backend saat ini; hindari framework dan dependensi baru.

## Implementation plan

1. Tambahkan layanan/endpoint prediksi aktif serta quote batch untuk kalkulator, freshness 7 hari, dan pesan error terstruktur.
2. Hubungkan ringkasan, grafik, kalkulator, dan tanya ke data API aktif; hapus fallback angka demo dari area akun.
3. Perbaiki pesan dan cookie pada alur OAuth; ekspos status akun/admin secara akurat.
4. Batasi endpoint dan kontrol admin di UI serta backend.
5. Rapikan header, navigasi, dan kontrol dashboard untuk HP; perbarui README/panduan login/admin.
6. Jalankan pemeriksaan sintaks dan smoke check HTTP lokal; tidak menjalankan suite test kecuali diminta.

## Builder check

Dibaca ulang sebagai implementer. Tidak ditemukan pertanyaan penting yang menghalangi rencana. Pembayaran nyata, data PIHPS otomatis, dan partisipasi uji UMKM berada di luar batas implementasi ini.
