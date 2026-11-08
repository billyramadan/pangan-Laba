"""Download a reproducible daily ERA5 series for the Depok study area."""
from pathlib import Path
import json
from datetime import datetime, timezone

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]

LATITUDE = -6.3917
LONGITUDE = 106.8167
TIMEZONE = "Asia/Jakarta"
START_DATE = "2020-01-01"
END_DATE = "2026-10-26"
URL = "https://archive-api.open-meteo.com/v1/archive"
DAILY_FIELDS = [
    "temperature_2m_mean", "temperature_2m_max", "temperature_2m_min",
    "precipitation_sum", "wind_speed_10m_max", "shortwave_radiation_sum",
]

params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": START_DATE,
    "end_date": END_DATE,
    "daily": ",".join(DAILY_FIELDS),
    "timezone": TIMEZONE,
    "models": "era5",
}
response = requests.get(URL, params=params, timeout=240)
response.raise_for_status()
payload = response.json()
daily = payload.get("daily", {})
if not daily or any(field not in daily for field in ["time", *DAILY_FIELDS]):
    raise SystemExit("Respons Open-Meteo tidak memuat semua variabel harian yang diminta.")

frame = pd.DataFrame({
    "date": daily["time"],
    "temp_c": daily["temperature_2m_mean"],
    "temp_max_c": daily["temperature_2m_max"],
    "temp_min_c": daily["temperature_2m_min"],
    "rain_mm": daily["precipitation_sum"],
    "wind_max_kmh": daily["wind_speed_10m_max"],
    "solar_mj_m2": daily["shortwave_radiation_sum"],
})
frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
for col in frame.columns.drop("date"):
    frame[col] = pd.to_numeric(frame[col], errors="coerce")
if frame.empty or frame.isna().any().any() or frame["date"].duplicated().any():
    raise SystemExit("Seri Open-Meteo kosong, memiliki tanggal ganda, atau memiliki nilai kosong.")

candidate = ROOT / "data/processed/weather_openmeteo_era5_candidate.csv"
candidate.parent.mkdir(parents=True, exist_ok=True)
frame.to_csv(candidate, index=False, date_format="%Y-%m-%d", float_format="%.3f")
metadata = {
    "provider": "Open-Meteo Historical Weather API",
    "model": "ERA5",
    "retrieved_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "url": response.url,
    "requested_coordinates": {"latitude": LATITUDE, "longitude": LONGITUDE},
    "returned_coordinates": {"latitude": payload.get("latitude"),
                              "longitude": payload.get("longitude")},
    "elevation_m": payload.get("elevation"),
    "timezone": payload.get("timezone"),
    "requested_period": {"start": START_DATE, "end": END_DATE},
    "returned_period": {"start": str(frame["date"].min().date()),
                         "end": str(frame["date"].max().date())},
    "daily_fields": DAILY_FIELDS,
    "units": payload.get("daily_units", {}),
}
(ROOT / "data/processed/weather_openmeteo_era5_metadata.json").write_text(
    json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Candidate tersimpan: {candidate}")
print(f"Tanggal: {metadata['returned_period']['start']}–{metadata['returned_period']['end']} ({len(frame):,} baris)")
print(f"Titik grid hasil Open-Meteo: {metadata['returned_coordinates']}, elevasi {metadata['elevation_m']} m")

active_path = ROOT / "data/raw/weather.csv"
if active_path.exists():
    active = pd.read_csv(active_path, parse_dates=["date"])
    compared = active.merge(frame, on="date", suffixes=("_active", "_era5"))
    common_fields = ["temp_c", "temp_max_c", "temp_min_c", "rain_mm",
                     "wind_max_kmh", "solar_mj_m2"]
    if len(compared):
        for field in common_fields:
            delta = (compared[f"{field}_active"] - compared[f"{field}_era5"]).abs()
            print(f"{field}: median |selisih|={delta.median():.3f}; maksimum={delta.max():.3f}")
        print(f"Tanggal dibandingkan: {len(compared):,}")
