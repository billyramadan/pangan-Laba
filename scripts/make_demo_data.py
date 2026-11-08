from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
(ROOT / "data/raw").mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(17)
dates = pd.date_range("2021-01-01", "2025-12-31", freq="D")
items = {"Cabai": 38000, "Bawang": 32000, "Telur": 27000,
         "Minyak Goreng": 18000, "Gula": 16000}
rows = []
for name, base in items.items():
    weekly = 0.035 * np.sin(2 * np.pi * np.arange(len(dates)) / 7)
    annual = 0.12 * np.sin(2 * np.pi * np.arange(len(dates)) / 365.25)
    shocks = rng.normal(0, 0.025, len(dates)).cumsum() * 0.03
    noise = rng.normal(0, 0.025, len(dates))
    price = base * (1 + weekly + annual + shocks + noise)
    for date, value in zip(dates, price):
        rows.append({"date": date.date().isoformat(), "commodity": name,
                     "price": round(max(1, value), 2), "location": "DEMO - BUKAN DATA RESMI"})
pd.DataFrame(rows).to_csv(ROOT / "data/raw/prices.csv", index=False)
weather = pd.DataFrame({"date": dates.date.astype(str), "rain_mm": np.maximum(0, rng.normal(8, 10, len(dates))),
                        "temp_c": rng.normal(28, 1.5, len(dates))})
weather.to_csv(ROOT / "data/raw/weather.csv", index=False)
calendar = pd.DataFrame({"date": dates.date.astype(str), "is_holiday": (dates.dayofweek >= 5).astype(int),
                         "is_ramadan": 0, "is_near_eid": 0})
calendar.to_csv(ROOT / "data/raw/calendar.csv", index=False)
print("Data DEMO sintetis dibuat di data/raw. Ganti dengan data resmi untuk penelitian.")
