# Login Google, trial, dan pembayaran

## Alur akun

- Halaman HTML memakai login Google OpenID Connect lewat `GET /auth/login`; aplikasi tidak menyimpan password Google.
- Login Google pertama membuat akun dan trial 7 hari untuk email Google yang terverifikasi.
- Setelah login berhasil, server mengarahkan pengguna kembali ke dashboard. Tombol **Coba demo** tetap tersedia tanpa akun, tetapi demo tidak boleh membuat transaksi atau langganan pelanggan.

## Callback Google lokal

1. Di `.streamlit/secrets.toml`, isi kredensial Google OAuth pada bagian `[auth.google]` dan gunakan callback `http://127.0.0.1:8000/auth/callback`.
2. Tambahkan URI yang sama persis di Google Cloud Console → OAuth Client → Authorized redirect URIs. Untuk domain produksi, pakai URL HTTPS domain tersebut dan samakan dengan `auth.redirect_uri`.
3. Jalankan `python -m backend.server` dari folder `C:\pangan`, lalu buka `http://127.0.0.1:8000`. Jangan memakai `localhost` kalau OAuth Client hanya mendaftarkan `127.0.0.1` (dan sebaliknya). Host dan port harus sama dengan callback.

## Konfigurasi hosting

Jangan commit `.streamlit/secrets.toml`. Di dashboard hosting, masukkan variabel lingkungan berikut; variabel lingkungan mengesampingkan nilai lokal pada file TOML:

- `PANGAN_HOST=0.0.0.0` agar aplikasi menerima koneksi dari reverse proxy hosting.
- `PANGAN_PORT` atau variabel standar hosting `PORT` untuk port server.
- `PANGAN_DB_PATH` ke file database pada persistent disk/volume, misalnya `/var/data/pangan-app.sqlite3`.
- `PANGAN_OAUTH_REDIRECT_URI=https://domain-aplikasi/auth/callback`.
- `PANGAN_GOOGLE_CLIENT_ID`, `PANGAN_GOOGLE_CLIENT_SECRET`, dan `PANGAN_COOKIE_SECRET` (acak, minimal 32 karakter).
- `PANGAN_ADMIN_EMAILS` berisi email admin yang dipisahkan koma.

Callback OAuth produksi harus HTTPS. Jika rahasia OAuth belum lengkap atau callback publik memakai HTTP, server menolak sesi login; sesi development fallback tidak diterima sebagai akun admin. Setelah mengubah variabel lingkungan, restart aplikasi. Tambahkan callback HTTPS yang sama persis di Google Cloud Console.

## Pembayaran paket

Tombol **Pilih paket ini** mengirim permintaan ke `POST /api/subscription/request`. Permintaan dan transaksi dicatat pada database aplikasi. Untuk uji transfer manual, isi `[billing]` dengan `provider = "manual"`, detail rekening yang benar, dan instruksi pembayaran. Admin dapat membuka **Pembayaran & langganan** di dashboard, mencocokkan transfer dengan mutasi rekening, lalu menekan **Konfirmasi**. Tombol hanya menerima transaksi manual yang masih pending; konfirmasi memperbarui status transaksi dan masa akses akun.

Untuk menagih dengan transfer manual, isi variabel hosting `PANGAN_BILLING_PROVIDER=manual`, `PANGAN_BANK_NAME`, `PANGAN_BANK_NUMBER`, `PANGAN_BANK_ACCOUNT_NAME`, dan `PANGAN_PAYMENT_INSTRUCTIONS` dengan informasi usaha yang benar. Jika rekening dan instruksi kosong, permintaan paket berbayar dinonaktifkan. Akses trial gratis dapat dipakai untuk pilot UMKM tanpa mengaktifkan pembayaran.

Untuk Xendit, isi `provider = "xendit"`, `xendit_api_key`, dan `xendit_webhook_token` dengan nilai akun pengelola. Atur URL webhook invoice menjadi `https://domain-aplikasi/api/webhook/xendit` di dashboard Xendit, lalu gunakan token callback yang sama pada konfigurasi. Token wajib; webhook tanpa token atau dengan token salah ditolak. Pemberitahuan `PAID` dicocokkan ke referensi dan nominal invoice tersimpan sebelum transaksi ditandai berhasil dan paket diaktifkan. Status pembayaran dan riwayatnya dapat dilihat admin pada bagian **Pembayaran & langganan**.

Jangan menaruh API key atau token callback di GitHub. Saat deploy, pastikan `data/app_users.sqlite3` berada di penyimpanan persisten/volume yang dibackup. Hosting dengan filesystem sementara dapat menghapus akun dan transaksi saat redeploy. Pembayaran nyata belum diverifikasi sampai kredensial milik pengelola dipasang dan alur sandbox diuji dari pembuatan invoice sampai aktivasi.

## Batas purwarupa

Dashboard admin mencatat pembayaran sukses dan pending, tetapi pengembalian dana harus dikelola melalui penyedia pembayaran. Integrasi Xendit yang tersedia adalah invoice per transaksi; pembayaran satu paket tidak otomatis memperpanjang langganan bulan berikutnya. Google login hanya memverifikasi identitas, bukan pembayaran. Sebelum menerima pengguna berbayar, siapkan hosting HTTPS, penyimpanan persisten dan backup, kebijakan privasi, layanan bantuan, serta uji sandbox gateway.
