from pathlib import Path
import argparse
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pangan_forecast.models import run_experiments

parser = argparse.ArgumentParser(description="Train LSTM/GRU variants for Kota Depok PIHPS data.")
parser.add_argument("--epochs", type=int, default=15)
parser.add_argument("--batch-size", type=int, default=128)
parser.add_argument("--window", type=int, default=30)
parser.add_argument("--horizon", type=int, default=7)
args = parser.parse_args()

clean_path = ROOT / "data/processed/combined_daily.csv"
if not clean_path.exists():
    raise SystemExit("Data olahan belum ada. Jalankan scripts/prepare_data.py terlebih dahulu.")
clean = pd.read_csv(clean_path, parse_dates=["date"])
staging = ROOT / "training_staging/depok"
metrics, forecasts = run_experiments(
    clean, staging, window=args.window, horizon=args.horizon,
    epochs=args.epochs, batch_size=args.batch_size, data_source="depok_pihps",
)
print(f"Training selesai. Model: {len(metrics)}; ramalan: {len(forecasts)}")
print(f"Hasil sementara: {staging / 'reports'}")
print(metrics.to_string(index=False) if not metrics.empty else "Tidak ada model yang dapat dilatih.")
