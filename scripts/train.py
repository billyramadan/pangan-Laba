from pathlib import Path
import argparse
import sys
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))
from pangan_forecast.models import run_experiments, refit_full_history_models

parser = argparse.ArgumentParser()
parser.add_argument("--epochs", type=int, default=30)
parser.add_argument("--window", type=int, default=30)
parser.add_argument("--horizon", type=int, default=7)
args = parser.parse_args()
data_path = ROOT / "data/processed/combined_daily.csv"
if not data_path.exists():
    raise SystemExit("Data olahan belum ada. Jalankan: python scripts/prepare_data.py")
clean = pd.read_csv(data_path, parse_dates=["date"])
is_demo = ("location" in clean.columns and clean["location"].astype(str)
           .str.contains("DEMO", case=False, na=False).any())
source_label = "synthetic_demo" if is_demo else "depok_pihps_era5_daily_weather_calendar"
metrics, _ = run_experiments(clean, ROOT,
                            args.window, args.horizon, args.epochs,
                            data_source=source_label)
final_models = refit_full_history_models(
    clean, ROOT, window=args.window, horizon=args.horizon, epochs=args.epochs,
)
print(f"Model final dilatih ulang dengan histori penuh: {len(final_models)} varian.")
print(metrics.to_string(index=False) if not metrics.empty else "Tidak ada model yang dapat dilatih.")
