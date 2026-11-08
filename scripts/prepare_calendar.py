from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pangan_forecast.data import normalize_calendar

source = ROOT / "data/raw/kalender_indonesia_2020_2026_source.csv"
destination = ROOT / "data/raw/calendar.csv"
if not source.exists():
    raise SystemExit(f"CSV kalender sumber belum ditemukan: {source}")

normalized = normalize_calendar(pd.read_csv(source))
destination.parent.mkdir(parents=True, exist_ok=True)
normalized.to_csv(destination, index=False, date_format="%Y-%m-%d")
print(f"Tersimpan: {destination} ({len(normalized):,} tanggal)")
print(f"Kolom fitur: {', '.join(normalized.columns.drop('date'))}")
print(f"Rentang: {normalized['date'].min():%Y-%m-%d}–{normalized['date'].max():%Y-%m-%d}")
for column in normalized.columns.drop("date"):
    print(f"{column}: {int(normalized[column].sum()):,} tanggal bernilai 1")
