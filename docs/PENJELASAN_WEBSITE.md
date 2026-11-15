# Penjelasan Detail Website PanganLaba

Dokumen ini menjelaskan alur kerja website dari data mentah → machine learning → rekomendasi → kalkulator laba UMKM, berdasarkan kode sumber proyek.

## A. Alur Data (dari mentah sampai prediksi)

### 1. Data mentah

| Data | Sumber | Isi |
|---|---|---|
| Harga | PIHPS Kota Depok | date, commodity, price (Rp/kg), location |
| Cuaca | ERA5 (Open-Meteo) | temp_c, temp_max_c, rain_mm, wind, solar |
| Kalender | CSV manual | is_libur_nasional, is_cuti_bersama, is_weekend, is_idul_fitri |

### 2. Ekstraksi fitur (`features.py`)

Fungsi `add_features()` mengubah tiap baris harga menjadi baris berisi fitur turunan.

**Fitur harga (PRICE_FEATURES):**

- `price` — harga hari ini
- `lag_1` — harga kemarin (`shift(1)`)
- `lag_7` — harga 7 hari lalu (`shift(7)`)
- `mean_7` — rata-rata 7 hari terakhir (rolling, `shift(1)` dulu agar tidak bocor)
- `mean_30` — rata-rata 30 hari terakhir

**Fitur siklus (selalu ada):**

- `dow_sin`, `dow_cos` — hari dalam minggu → sinus/kosinus (untuk menangkap pola mingguan)
- `month_sin`, `month_cos` — bulan → sinus/kosinus (pola musiman)

> Alasan sinus/kosinus: hari 6 dan 0 (Sabtu/Minggu) sebenarnya berdekatan secara siklus, tetapi angka 6 dan 0 berjauhan. Sinus/kosinus membuat "jarak siklus" menjadi benar.

**Fitur eksternal (EXTERNAL_FEATURES — hanya pada varian eksternal):**

- Cuaca: `temp_c`, `temp_max_c`, `temp_min_c`, `rain_mm`, `wind_max_kmh`, `solar_mj_m2`
- Kalender: `is_libur_nasional`, `is_cuti_bersama`, `is_weekend`, `is_ramadan`, `is_near_eid`, `is_idul_fitri`

### 3. Bentuk sequence (`models.py` — `build_sequences()`)

Model tidak makan satu baris, melainkan **jendela (window) 30 hari**:

- Data dipotong menjadi window 30 hari bergeser
- Setiap window menjadi target **7 hari berikutnya**
- `window = 30`, `horizon = 7`

### 4. Arsitektur model (`_build_keras()`)

```
Input(shape=(30, jumlah_fitur))
  → LSTM atau GRU (48 unit)
  → Dropout(0.15)
  → Dense(32, activation="relu")
  → Dense(7)   ← output 7 hari
```

- Optimizer: `adam`, loss: `mse`
- Dilatih 4 varian: LSTM×harga saja, LSTM×eksternal, GRU×harga saja, GRU×eksternal

### 5. Pelatihan dan evaluasi (`run_experiments()`)

- **Split 80/20 kronologis** — 80% data awal untuk latih, 20% akhir untuk uji
- **Scaler** StandardScaler — fit **hanya pada data latih** (anti-bocor), lalu diterapkan ke data uji
- **Early stopping** — patience 5, restore best weights
- **Metrik** — MAE, RMSE, MAPE per komoditas, disimpan ke `model_comparison.csv`

### 6. Prediksi live (`forecast_next()`)

1. Ambil 30 hari data terakhir dari database
2. `add_features()` → fitur
3. Standarisasi memakai mean/scale tersimpan (dari file `.json` model)
4. `model.predict()` → 7 nilai (terstandardisasi)
5. Un-standardisasi → balik ke rupiah → `max(0, nilai)` (kalau model memprediksi negatif)

---

## B. Rekomendasi Belanja (`recommend.py`)

`make_recommendation(last_price, forecast_prices)`:

1. Hitung `forecast_mean` = rata-rata prediksi
2. `change = forecast_mean / last_price - 1` → persentase perubahan
3. Aturan:
   - `change >= +5%` → **"Beli sekarang"** (harga diprediksi naik)
   - `change <= -5%` → **"Tunda dulu"** (harga diprediksi turun)
   - selain itu → **"Beli sesuai kebutuhan"**

**Simulasi belanja** (`simulate_purchase_policy`): membandingkan pembelian tiap 7 hari dengan kebijakan boleh menunda maksimal 2 hari bila saran "Tunda dulu". Keluaran: `savings_rp`.

> Catatan jujur: hasil simulasi ~0%, sehingga tidak ada jaminan penghematan.

---

## C. Kalkulator Laba UMKM (`business.py` / `service.py`)

**Input dari pengguna (dashboard):**

- `menu_name` — nama menu
- `recipe` — daftar bahan: {commodity, grams_per_portion, actual_price_rp_per_kg}
- `selling_price` — harga jual per porsi
- `portions_sold` — jumlah porsi terjual
- `other_cost_per_portion` — biaya variabel lain per porsi
- `fixed_cost` — biaya tetap
- `sales_period` — periode
- `model` + `features` + `restock_days` — untuk prediksi harga

**Perhitungan:**

1. **Modal bahan per porsi** = Σ(grams/1000 × harga bahan)
2. **Biaya bahan total** = modal per porsi × porsi
3. **Pendapatan (revenue)** = harga jual × porsi
4. **Laba kotor (gross profit)** = revenue − biaya bahan total
5. **Laba bersih (net profit)** = laba kotor − (biaya variabel × porsi) − biaya tetap
6. **Margin bersih** = laba bersih / revenue × 100%
7. **Titik impas** = biaya tetap / (harga jual − modal per porsi − biaya variabel per porsi)

**Prediksi laba (nilai unik):**

- `predicted_ingredient_cost_per_portion` — modal per porsi menggunakan **harga prediksi** dari ML
- `predicted_net_profit` — laba bersih bila harga bahan berubah sesuai prediksi
- Pengguna dapat melihat: "kalau harga prediksi naik, modal jadi X, laba bersih jadi Y."

**Riwayat:** setiap hitungan tersimpan per akun (SQLite `menu_profit_records`). Dashboard menampilkan total omzet, laba bersih, margin rata-rata, menu paling untung, tabel riwayat, serta unduhan CSV.

---

## D. Bagian yang Saling Terhubung

```
ML prediksi harga
   → rekomendasi beli/tunda (kapan belanja)
   → modal & laba berdasarkan harga prediksi (berapa untung)
   → pengguna bisa memutuskan: belanja sekarang/tunda + harga jual aman
```

ML tidak sekadar "menebak harga" — hasilnya dipakai langsung dalam hitungan laba. Inilah yang menjadikan website ini riset aplikatif: model ML berdampak pada keputusan usaha nyata.

---

## E. Kejujuran & Batas

- Fitur eksternal belum terbukti membantu; harga saja justru lebih akurat. Ini temuan yang diakui.
- Simulasi belanja ~0%, belum terbukti hemat.
- Website memasang disclaimer: prediksi dan saran adalah bahan pertimbangan, bukan jaminan.
