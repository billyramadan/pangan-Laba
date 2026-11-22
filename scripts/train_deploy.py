"""Retrain full deploy artifacts to project root (reports/ + models/).

Mirrors run_training() so the deployed site (root/reports + root/models)
gets the bmkg variant on every eligible commodity.
"""
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))
from pangan_forecast.models import run_experiments, refit_full_history_models

clean = pd.read_csv(ROOT / "data/processed/combined_daily.csv", parse_dates=["date"])
metrics, _ = run_experiments(
    clean, ROOT, window=30, horizon=7, epochs=15, batch_size=128,
    data_source="depok_pihps",
)
print(f"Eksperimen selesai: {len(metrics)} baris evaluasi.")
if metrics.empty:
    raise SystemExit("Data tidak cukup untuk evaluasi.")
final = refit_full_history_models(
    clean, ROOT, window=30, horizon=7, epochs=15, batch_size=128,
)
print(f"Refit deploy selesai: {len(final)} varian.")
bmkg = final[final["features"] == "harga + cuaca + bmkg"]
print(f"Varian bmkg: {len(bmkg)} komoditas×model.")
