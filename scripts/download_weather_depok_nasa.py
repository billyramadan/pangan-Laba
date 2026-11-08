"""Download NASA POWER daily weather near the geographic centre of Kota Depok."""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
NASA_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
# Midpoint of Kota Depok's published latitude/longitude bounds (BPS Depok).
LATITUDE = -6.3917
LONGITUDE = 106.8167


def make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=5, connect=5, read=5, backoff_factor=2,
                  status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=frozenset({"GET"}))
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session


def download(start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    frames = []
    chunk_start = start
    session = make_session()
    while chunk_start <= end:
        chunk_end = min(chunk_start + timedelta(days=364), end)
        params = {
            "parameters": "T2M,PRECTOTCORR", "community": "RE",
            "longitude": LONGITUDE, "latitude": LATITUDE,
            "start": chunk_start.strftime("%Y%m%d"),
            "end": chunk_end.strftime("%Y%m%d"),
            "format": "JSON", "time-standard": "LST",
        }
        response = session.get(NASA_URL, params=params, timeout=180)
        response.raise_for_status()
        payload = response.json()
        values = payload.get("properties", {}).get("parameter", {})
        if not {"T2M", "PRECTOTCORR"}.issubset(values):
            raise RuntimeError(f"Parameter cuaca NASA POWER tidak lengkap: {list(values)}")
        frame = pd.DataFrame({
            "date": pd.to_datetime(list(values["T2M"]), format="%Y%m%d"),
            "temp_c": list(values["T2M"].values()),
            "rain_mm": list(values["PRECTOTCORR"].values()),
        })
        for col in ("temp_c", "rain_mm"):
            frame[col] = pd.to_numeric(frame[col], errors="coerce").replace(-999, pd.NA)
        frames.append(frame)
        chunk_start = chunk_end + timedelta(days=1)
    return pd.concat(frames, ignore_index=True).drop_duplicates("date", keep="last").sort_values("date")


if __name__ == "__main__":
    prices = pd.read_csv(ROOT / "data/raw/prices.csv", parse_dates=["date"])
    start, end = prices.date.min().normalize(), prices.date.max().normalize()
    weather = download(start, end).set_index("date")
    expected = pd.date_range(start, end, freq="D")
    weather = weather.reindex(expected)
    weather.index.name = "date"
    missing = weather["temp_c"].isna() | weather["rain_mm"].isna()
    if missing.any():
        dates = weather.index[missing].strftime("%Y-%m-%d").tolist()
        raise RuntimeError(f"Cuaca NASA POWER kosong pada {len(dates)} hari. Contoh: {dates[:5]}")
    output = ROOT / "data/processed/weather_depok_candidate.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    weather.reset_index().to_csv(output, index=False, date_format="%Y-%m-%d", float_format="%.3f")
    print(f"Saved {output}; {len(weather):,} days; {start.date()} to {end.date()}")
    print(f"Query point near Depok centre: lat={LATITUDE}, lon={LONGITUDE}; NASA POWER snaps to a data grid point.")
    print(f"Mean temperature {weather.temp_c.mean():.2f} C; mean rainfall {weather.rain_mm.mean():.2f} mm/day")
