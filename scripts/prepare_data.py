from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))
from pangan_forecast.data import load_and_merge

clean = load_and_merge(ROOT / "data/raw/prices.csv", ROOT / "data/raw/weather.csv",
                       ROOT / "data/raw/calendar.csv")
dest = ROOT / "data/processed/combined_daily.csv"
dest.parent.mkdir(parents=True, exist_ok=True)
clean.to_csv(dest, index=False)
print(f"Tersimpan: {dest} ({len(clean)} baris)")
