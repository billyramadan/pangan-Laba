from pathlib import Path
import json
import re

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

metrics = pd.read_csv(REPORTS / "model_comparison.csv")
forecasts = pd.read_csv(REPORTS / "forecasts.csv",
                        parse_dates=["origin_date", "target_date"])
prices = pd.read_csv(ROOT / "data/raw/prices.csv", parse_dates=["date"])
weather = pd.read_csv(ROOT / "data/raw/weather.csv", parse_dates=["date"])
metadata_path = ROOT / "data/processed/weather_openmeteo_era5_metadata.json"
weather_metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
simulation_path = REPORTS / "purchase_simulation_summary.csv"
simulations = pd.read_csv(simulation_path) if simulation_path.exists() else pd.DataFrame()
final_manifest_path = REPORTS / "final_models_manifest.csv"
final_manifest = pd.read_csv(final_manifest_path) if final_manifest_path.exists() else pd.DataFrame()

if metrics.empty or forecasts.empty:
    raise SystemExit("Laporan evaluasi/prediksi kosong. Latih model terlebih dahulu.")
grid = weather_metadata.get("returned_coordinates", {})
grid_text = (f"lat {grid['latitude']}, lon {grid['longitude']}, "
             f"elevasi {weather_metadata.get('elevation_m')} m") if grid else "tidak tercatat"

# Thesis-friendly, explicit metric columns and units.
table = metrics.rename(columns={
    "MAE": "MAE_Rp_per_kg", "RMSE": "RMSE_Rp_per_kg",
    "MAPE": "MAPE_persen", "commodity": "komoditas",
    "model": "model", "features": "fitur", "train_target_end": "akhir_target_latih",
    "test_target_start": "awal_target_uji", "test_target_end": "akhir_target_uji",
    "n_train_sequences": "jumlah_urutan_latih", "n_test_sequences": "jumlah_urutan_uji",
    "epochs_trained": "epoch_aktual", "window_days": "jendela_hari",
    "forecast_horizon_days": "horizon_hari",
})
keep = ["komoditas", "model", "fitur", "MAE_Rp_per_kg", "RMSE_Rp_per_kg",
        "MAPE_persen", "akhir_target_latih", "awal_target_uji", "akhir_target_uji",
        "jendela_hari", "horizon_hari", "epoch_aktual",
        "jumlah_urutan_latih", "jumlah_urutan_uji"]
table[keep].sort_values(["komoditas", "model", "fitur"]).to_csv(
    REPORTS / "tabel_evaluasi_skripsi.csv", index=False, float_format="%.4f",
    encoding="utf-8-sig")

# One-step-ahead rolling test plots: avoids mixing 1- to 7-day horizons in one line.
step_one = forecasts[forecasts["step"] == 1].copy()
variant_names = {
    ("LSTM", "harga saja"): "LSTM · harga saja",
    ("LSTM", "harga + cuaca + kalender + siklus tanggal"): "LSTM · eksternal",
    ("GRU", "harga saja"): "GRU · harga saja",
    ("GRU", "harga + cuaca + kalender + siklus tanggal"): "GRU · eksternal",
}
colors = {
    "Aktual": "#1b5a41", "LSTM · harga saja": "#dd8452",
    "LSTM · eksternal": "#c44e52", "GRU · harga saja": "#4c72b0",
    "GRU · eksternal": "#8172b2",
}
index_rows = []
for commodity, group in step_one.groupby("commodity"):
    actual_by_date = group.groupby("target_date")["actual"].nunique()
    if (actual_by_date > 1).any():
        raise ValueError(f"Nilai aktual tidak konsisten antarvarian untuk {commodity}.")
    actual = (group.sort_values("target_date").drop_duplicates("target_date")
              .set_index("target_date")["actual"])
    fig, ax = plt.subplots(figsize=(12, 5.2))
    ax.plot(actual.index, actual.values, label="Aktual", color=colors["Aktual"],
            linewidth=2.4, zorder=5)
    for (model, features), variant in group.groupby(["model", "features"]):
        label = variant_names.get((model, features), f"{model} · {features}")
        series = variant.sort_values("target_date").drop_duplicates("target_date")
        ax.plot(series["target_date"], series["predicted"], label=label,
                color=colors.get(label, "#888888"), linewidth=1.25, alpha=.86)
    ax.set_title(f"{commodity}: aktual vs prediksi satu hari ke depan", loc="left",
                 fontsize=14, fontweight="bold", color="#1e3328")
    ax.set_ylabel("Harga (Rp/kg)")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"Rp{value:,.0f}"))
    ax.set_xlabel("Tanggal target pada bagian uji")
    ax.grid(axis="y", color="#e4e9dc", linewidth=.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, ncol=2, loc="upper left")
    fig.autofmt_xdate()
    fig.tight_layout()
    slug = re.sub(r"[^a-z0-9]+", "_", commodity.lower()).strip("_")
    filename = f"aktual_vs_prediksi_{slug}_h1.png"
    fig.savefig(FIGURES / filename, dpi=170, bbox_inches="tight")
    plt.close(fig)
    index_rows.append((commodity, filename, len(actual)))

summary = (metrics.groupby(["model", "features"], as_index=False)
           .agg(jumlah_komoditas=("commodity", "nunique"),
                median_MAE=("MAE", "median"), median_RMSE=("RMSE", "median"),
                median_MAPE=("MAPE", "median"), mean_MAE=("MAE", "mean"),
                mean_RMSE=("RMSE", "mean"), mean_MAPE=("MAPE", "mean")))
summary.to_csv(REPORTS / "model_comparison_summary.csv", index=False, float_format="%.4f")

fig, axes = plt.subplots(1, 3, figsize=(14, 4.8))
order = [("GRU", "harga saja"), ("GRU", "harga + cuaca + kalender + siklus tanggal"),
         ("LSTM", "harga saja"), ("LSTM", "harga + cuaca + kalender + siklus tanggal")]
labels = ["GRU\nharga", "GRU\neksternal", "LSTM\nharga", "LSTM\neksternal"]
for ax, metric, title in zip(axes, ["MAE", "RMSE", "MAPE"],
                             ["Median MAE", "Median RMSE", "Median MAPE"]):
    vals = [float(summary.loc[(summary["model"] == model) &
                              (summary["features"] == features), f"median_{metric}"].iloc[0])
            for model, features in order]
    bars = ax.bar(labels, vals, color=["#4c72b0", "#8172b2", "#dd8452", "#c44e52"])
    ax.set_title(title, color="#1e3328", fontweight="bold")
    ax.grid(axis="y", color="#e4e9dc", linewidth=.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for bar, value in zip(bars, vals):
        suffix = "%" if metric == "MAPE" else ""
        ax.annotate(f"{value:,.3f}{suffix}",
                    (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xytext=(0, 4), textcoords="offset points", ha="center", fontsize=8)
fig.suptitle("Perbandingan median metrik pada 13 komoditas", fontweight="bold", color="#1e3328")
fig.tight_layout()
fig.savefig(FIGURES / "ringkasan_metrik_model.png", dpi=170, bbox_inches="tight")
plt.close(fig)

mae_pivot = metrics.pivot_table(index=["commodity", "model"], columns="features", values="MAE")
weather_wins = {}
for model in ("LSTM", "GRU"):
    paired = mae_pivot.xs(model, level="model").dropna()
    weather_wins[model] = int((paired["harga + cuaca + kalender + siklus tanggal"] < paired["harga saja"]).sum())

report_lines = [
    "# Bahan hasil dan evaluasi model untuk skripsi", "",
    "> Draf kerja untuk ditinjau dan diselaraskan dengan arahan dosen pembimbing. Jangan menyalin tanpa memeriksa metode, satuan, dan provenance sumber data.", "",
    "## Ringkasan data", "",
    f"- Harga PIHPS Kota Depok: {len(prices):,} observasi, {prices['commodity'].nunique()} komoditas, {prices['date'].min():%Y-%m-%d}–{prices['date'].max():%Y-%m-%d}.",
    f"- Cuaca harian aktif: {len(weather):,} tanggal, {weather['date'].min():%Y-%m-%d}–{weather['date'].max():%Y-%m-%d}; grid ERA5 {grid_text}.",
    f"- Evaluasi: {len(metrics)} kombinasi (13 komoditas × 2 model × 2 set fitur). Rentang target-uji antar-komoditas: {metrics['test_target_start'].min()}–{metrics['test_target_end'].max()}.",
    f"- Harga PIHPS Kota Depok bersatuan rupiah per kilogram (Rp/kg), sesuai konfirmasi pengguna. Cuaca aktif diunduh langsung dari Open-Meteo Historical Weather API dengan model ERA5 eksplisit dan timezone Asia/Jakarta; pengambilan terakhir {weather_metadata.get('retrieved_at_utc', 'tanggal belum tercatat')} UTC. Satuan cuaca: suhu °C, presipitasi mm, angin km/h, dan radiasi MJ/m².",
    "", "## Metode evaluasi", "",
    "Data setiap komoditas diurutkan berdasarkan tanggal dan dibagi kronologis 80% pelatihan / 20% pengujian. Semua varian model pada komoditas yang sama menggunakan batas waktu dan urutan uji yang sama. Model menerima jendela 30 hari untuk memprediksi tujuh hari berikutnya. LSTM dan GRU masing-masing diuji memakai fitur harga (harga, lag 1, lag 7, rerata 7 dan 30 hari) serta paket eksternal yang menambahkan enam variabel cuaca ERA5, indikator libur nasional/cuti bersama/akhir pekan, penanda tanggal dengan keterangan Idulfitri, dan empat fitur siklus hari/bulan. Indikator kalender yang masuk ke model berasal dari jendela historis 30 hari; kalender masa depan tidak diberikan sebagai input decoder terpisah. CSV tidak menandai periode Ramadan atau rentang hari menjelang Idulfitri.",
    "", "Pelatihan memakai maksimum 30 epoch, validasi 10% dari bagian pelatihan yang paling akhir, dan early stopping dengan patience 5. Jumlah epoch aktual pada run ini: "
    f"{metrics['epochs_trained'].min()}–{metrics['epochs_trained'].max()} (median {metrics['epochs_trained'].median():.1f}). Scaler dipasang pada data latih saja.",
    "", (f"Setelah evaluasi, {len(final_manifest)} model operasional di-fit ulang memakai seluruh urutan historis yang tersedia per komoditas. Model final ini untuk prediksi dashboard dan tidak digunakan untuk menghitung metrik holdout. Rincian rentang fit ada di `final_models_manifest.csv`." if not final_manifest.empty else "Model yang disimpan saat evaluasi masih memakai bagian latih kronologis; jalankan refit model penuh untuk menghasilkan model operasional dashboard."),
    "", "MAE dan RMSE dilaporkan dalam rupiah per kilogram (Rp/kg); MAPE dalam persen. Tabel laporan menggabungkan error dari tujuh horizon dan semua origin harian pada bagian uji. Origin/horizon tumpang tindih sehingga error antarbaris berkorelasi. Grafik H+1 di bawah mengambil prediksi satu hari ke depan pada setiap origin uji agar seri aktual/prediksi bisa dibaca tanpa mencampur horizon.",
    "", "## Ringkasan metrik lintas komoditas", "",
    "Median antarkomoditas lebih layak untuk ringkasan karena nominal harga dan skala error berbeda antar-komoditas. Nilai mean tetap tersedia dalam file ringkasan.", "",
    "| Model | Fitur | Median MAE (Rp/kg) | Median RMSE (Rp/kg) | Median MAPE (%) |",
    "|---|---|---:|---:|---:|",
]
for _, row in summary.sort_values(["model", "features"]).iterrows():
    report_lines.append(f"| {row['model']} | {row['features']} | {row['median_MAE']:,.3f} | {row['median_RMSE']:,.3f} | {row['median_MAPE']:.3f} |")
report_lines += [
    "", f"Paket eksternal (cuaca, kalender, dan siklus tanggal) menghasilkan MAE lebih rendah dibanding fitur harga saja pada {weather_wins['LSTM']} dari 13 komoditas untuk LSTM dan {weather_wins['GRU']} dari 13 untuk GRU. Karena paket menggabungkan tiga kelompok fitur sekaligus, hasil ini tidak mengisolasi pengaruh cuaca atau kalender secara terpisah.",
    "", "## Sumber data", "",
    "Harga menggunakan workbook PIHPS yang diolah untuk baris Kota Depok. Cuaca aktif diambil langsung dari Open-Meteo Historical Weather API menggunakan model ERA5 dan parameter lokasi/waktu yang tersimpan di `data/processed/weather_openmeteo_era5_metadata.json`. Koordinat permintaan (-6.3917, 106.8167) dipetakan API ke grid ERA5 (-6.5, 106.75), elevasi 84 m. Ini data reanalisis grid untuk satu titik representatif, bukan pengukuran stasiun BMKG atau rata-rata seluruh Kota Depok. Variabel yang digunakan: suhu rata-rata/maksimum/minimum, presipitasi harian, angin maksimum, dan radiasi gelombang pendek. Rujukan Databoks membedakan prakiraan BMKG dari rekam historis ERA5/Open-Meteo; seri aktif proyek sekarang berasal langsung dari API Open-Meteo.",
    "", "## Keterbatasan", "",
    "- Ini satu pembagian holdout kronologis per komoditas, bukan beberapa fold rolling-origin atau uji pada wilayah lain.",
    "- Cakupan tanggal harga berbeda antar-komoditas; karena itu, tanggal uji tidak sama antar-komoditas, meskipun sama antarvarian dalam komoditas yang sama.",
    "- Satuan harga aktif dikonfirmasi sebagai Rp/kg; pastikan workbook komoditas yang ditambahkan tetap menggunakan satuan yang sama.",
    "- ERA5 merupakan reanalisis grid pada satu titik, bukan pembacaan stasiun atau representasi seragam seluruh Kota Depok.",
    "- CSV kalender diberikan pengguna dan memuat libur nasional, cuti bersama, akhir pekan, serta keterangan tanggal Idulfitri. Penanda Ramadan dan rentang hari menjelang Idulfitri tidak tersedia. Pada model saat ini kalender masa depan juga tidak diberikan langsung kepada decoder.",
    "- Simulasi beli/tunda memakai siklus dan volume tetap; lihat `SIMULASI_REKOMENDASI.md`. Hasilnya bukan penghematan aktual.",
    "- Hasil angka bergantung pada konfigurasi training dan satu random seed; lakukan pengujian stabilitas tambahan bila diminta pembimbing.",
    "", "## Referensi sumber", "",
    "- Open-Meteo. [Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api). Parameter unduhan yang dipakai tersimpan di `data/processed/weather_openmeteo_era5_metadata.json`.",
    "- Bank Indonesia. [Pusat Informasi Harga Pangan Strategis Nasional](https://www.bi.go.id/hargapangan/Website). Workbook harga PIHPS wilayah Kota Depok diberikan pengguna.",
    "- Katadata Databoks. [BMKG: Kota Depok Hujan Ringan Malam Ini](https://databoks.katadata.co.id/layanan-konsumen-kesehatan/statistik/a90d7884c8c49df/bmkg-kota-depok-hujan-ringan-malam-ini). Rujukan konteks yang membedakan prakiraan BMKG dan seri historis ERA5/Open-Meteo.",
    "", "## Berkas tabel dan gambar", "",
    "- Tabel lengkap per komoditas/model/fitur: `tabel_evaluasi_skripsi.csv` (52 baris).",
    "- Ringkasan metrik: `model_comparison_summary.csv`.",
    "- Grafik median metrik: `figures/ringkasan_metrik_model.png`.",
    "- Grafik aktual vs prediksi H+1 per komoditas: `FIGURES_INDEX.md`.",
]
if not simulations.empty:
    simulation_summary = (simulations.groupby(["model", "features"], as_index=False)
                          .agg(komoditas=("commodity", "nunique"),
                               median_selisih_pct=("savings_pct", "median"),
                               rerata_selisih_pct=("savings_pct", "mean")))
    report_lines += ["", "## Ringkasan simulasi beli/tunda", "",
                     "Parameter standar: siklus 7 hari, volume 1 kg per transaksi, harga Rp/kg, ambang penundaan 5%, maksimal tunda 2 hari. Median/rerata dihitung lintas-komoditas; hasil ini simulasi retrospektif, bukan penghematan aktual.", "",
                     "| Model | Fitur | Median selisih (%) | Rerata selisih (%) |",
                     "|---|---|---:|---:|"]
    for _, row in simulation_summary.sort_values(["model", "features"]).iterrows():
        median_pct = float(f"{row['median_selisih_pct']:.2f}")
        mean_pct = float(f"{row['rerata_selisih_pct']:.2f}")
        report_lines.append(f"| {row['model']} | {row['features']} | {median_pct:.2f} | {mean_pct:.2f} |")
(REPORTS / "BAHAN_SKRIPSI_HASIL.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

figure_lines = ["# Grafik aktual vs prediksi", "",
                "Semua grafik membandingkan aktual dengan empat varian model untuk prediksi satu hari ke depan (H+1), menggunakan origin harian pada bagian uji. Satuan harga mengikuti data PIHPS untuk komoditas tersebut.", "",
                "## Ringkasan metrik", "",
                "![Ringkasan median MAE, RMSE, dan MAPE](figures/ringkasan_metrik_model.png)", ""]
for commodity, filename, points in index_rows:
    figure_lines += [f"## {commodity}", "", f"Titik uji H+1: {points}.", "",
                     f"![{commodity}: aktual vs prediksi H+1](figures/{filename})", ""]
(REPORTS / "FIGURES_INDEX.md").write_text("\n".join(figure_lines), encoding="utf-8")
print(f"Dibuat: tabel_evaluasi_skripsi.csv ({len(table)} baris), {len(index_rows)} grafik komoditas, grafik ringkasan, dan bahan skripsi.")
