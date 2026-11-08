# Pendaftaran, trial, dan langganan

## Yang sudah tersedia

- Pendaftaran dan login menggunakan Google OpenID Connect melalui `st.login`. Login Google membuat akun aplikasi saat pertama masuk; aplikasi tidak menyimpan password pengguna.
- Akun baru mendapat trial 7 hari, satu kali per alamat email terverifikasi.
- Setelah trial berakhir, dashboard terkunci sampai pengelola mengaktifkan langganan.
- Paket berbayar ditampilkan dari konfigurasi dan dapat memakai hosted payment link atau instruksi transfer manual.
- Setelah pembayaran diterima dan diverifikasi, pengelola mengaktifkan akses untuk periode yang tercantum.

## Konfigurasi paket dan metode pembayaran

Salin `.streamlit/secrets.example.toml` menjadi `.streamlit/secrets.toml`, lalu isi bagian `[billing]` dengan harga dan metode pembayaran usaha. File `secrets.toml` diabaikan Git; jangan dibagikan atau diunggah.

- `plan_name`: nama paket yang ditampilkan.
- `price_idr`: harga paket dalam rupiah. Nilai `0` berarti harga belum ditetapkan dan tombol pembayaran belum ditampilkan.
- `duration_days`: masa akses setelah pembayaran diverifikasi (default 30 hari).
- `checkout_url`: hosted payment link dari penyedia yang dipilih. Pengelola tetap memverifikasi pembayaran sebelum aktivasi.
- `payment_instructions`: instruksi transfer manual jika belum memakai checkout.
- `support_url`: tautan kontak pengelola, misalnya tautan WhatsApp bisnis.

Pilih penyedia pembayaran, biaya layanan, aturan pembatalan/refund, dan harga setelah memvalidasi ke UMKM. Jangan mengisi nominal contoh sebagai harga final tanpa keputusan pengelola.

## Aktifkan langganan secara manual

Sesudah pembayaran benar-benar diterima dan diverifikasi di dashboard penyedia/bank, jalankan dari PowerShell pada folder `C:\pangan`:

```powershell
.\.venv\Scripts\python.exe .\scripts\activate_subscription.py email-pengguna@gmail.com --days 30
```

Perintah memperpanjang akses akun yang pernah login. Jangan menjalankannya hanya karena pengguna mengirim bukti yang belum diverifikasi. Prototipe ini belum memproses webhook pembayaran, aktivasi otomatis, pengembalian dana, atau perpanjangan otomatis.

## Jalankan preview lokal

```powershell
cd C:\pangan
.\scripts\run_local.ps1
```

Buka `http://localhost:8502`. Mode preview hanya untuk pengembangan lokal; preview tidak menjalankan pendaftaran/trial pelanggan atau pembayaran.

## Batas sebelum dipakai pelanggan sungguhan

Aplikasi memakai SQLite lokal untuk purwarupa satu server. Sebelum dibuka untuk pelanggan melalui internet, siapkan hosting HTTPS, penyimpanan akun persisten, backup, kebijakan privasi, prosedur dukungan dan refund, serta integrasi pembayaran yang diverifikasi server-side. Login email/password mandiri belum dibuat; untuk purwarupa ini autentikasi ditangani Google agar aplikasi tidak menyimpan password.
