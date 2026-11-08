"""Download daily NASA POWER weather and average grid cells inside Jawa Barat."""
from __future__ import annotations

import argparse
import json
from io import StringIO
from pathlib import Path
from datetime import timedelta
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NASA_URL = "https://power.larc.nasa.gov/api/temporal/daily/regional"
BOUNDARY_API = "https://www.geoboundaries.org/api/current/gbOpen/IDN/ADM1/"


def get_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "PanganInsight/1.0 (research data preparation)"})
    with urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    inside = False
    j = len(ring) - 1
    for i, (xi, yi, *_) in enumerate(ring):
        xj, yj = ring[j][:2]
        if (yi > lat) != (yj > lat):
            crossing = (xj - xi) * (lat - yi) / (yj - yi) + xi
            if lon < crossing:
                inside = not inside
        j = i
    return inside


def point_in_geometry(lon: float, lat: float, geometry: dict) -> bool:
    kind, coordinates = geometry["type"], geometry["coordinates"]
    polygons = [coordinates] if kind == "Polygon" else coordinates
    for polygon in polygons:
        if point_in_ring(lon, lat, polygon[0]) and not any(
            point_in_ring(lon, lat, hole) for hole in polygon[1:]
        ):
            return True
    return False


def fetch_parameter(parameter: str, start: str, end: str,
                    lat_min: float, lat_max: float,
                    lon_min: float, lon_max: float) -> pd.DataFrame:
    frames = []
    chunk_start = pd.Timestamp(start)
    final_date = pd.Timestamp(end)
    while chunk_start <= final_date:
        chunk_end = min(chunk_start + timedelta(days=365), final_date)
        query = urlencode({
            "latitude-min": lat_min, "latitude-max": lat_max,
            "longitude-min": lon_min, "longitude-max": lon_max,
            "parameters": parameter, "community": "RE",
            "start": chunk_start.strftime("%Y%m%d"), "end": chunk_end.strftime("%Y%m%d"),
            "format": "CSV",
        })
        request = Request(f"{NASA_URL}?{query}", headers={"User-Agent": "PanganInsight/1.0 (research data preparation)"})
        try:
            with urlopen(request, timeout=180) as response:
                payload = response.read().decode("utf-8-sig")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise RuntimeError(f"NASA POWER menolak {parameter} ({exc.code}): {detail}") from exc
        lines = payload.splitlines()
        try:
            header_end = lines.index("-END HEADER-")
        except ValueError as exc:
            raise RuntimeError(f"Format jawaban NASA POWER untuk {parameter} berubah: {payload[:500]}") from exc
        data = pd.read_csv(StringIO("\n".join(lines[header_end + 1:])))
        required = {"LAT", "LON", "YEAR", "MO", "DY", parameter}
        if not required.issubset(data.columns):
            raise RuntimeError(f"Kolom {parameter} tidak lengkap pada jawaban NASA POWER: {list(data.columns)}")
        data[parameter] = pd.to_numeric(data[parameter], errors="coerce").replace(-999, pd.NA)
        data = data.dropna(subset=[parameter])
        data["date"] = pd.to_datetime(dict(year=data.YEAR, month=data.MO, day=data.DY))
        frames.append(data)
        chunk_start = chunk_end + timedelta(days=1)
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prices", type=Path, default=ROOT / "data/raw/prices.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "data/raw/weather.csv")
    parser.add_argument("--start", help="YYYY-MM-DD; defaults to the earliest date in prices.csv")
    parser.add_argument("--end", help="YYYY-MM-DD; defaults to the latest date in prices.csv")
    args = parser.parse_args()

    prices = pd.read_csv(args.prices, usecols=["date"], parse_dates=["date"]).dropna()
    if prices.empty:
        raise ValueError(f"Tidak ada tanggal valid pada {args.prices}")
    start = pd.Timestamp(args.start) if args.start else prices.date.min()
    end = pd.Timestamp(args.end) if args.end else prices.date.max()
    if end < start:
        raise ValueError("Tanggal akhir harus setelah tanggal mulai.")

    metadata = get_json(BOUNDARY_API)
    boundary = get_json(metadata["gjDownloadURL"])
    feature = next((item for item in boundary["features"]
                    if item.get("properties", {}).get("shapeISO") == "ID-JB"
                    or item.get("properties", {}).get("shapeName") == "West Java"), None)
    if feature is None:
        raise RuntimeError("Batas administrasi Jawa Barat tidak ditemukan pada geoBoundaries.")
    geometry = feature["geometry"]

    def walk(coords):
        if isinstance(coords[0], (int, float)):
            yield coords
        else:
            for child in coords:
                yield from walk(child)

    vertices = list(walk(geometry["coordinates"]))
    lon_min, lon_max = min(p[0] for p in vertices), max(p[0] for p in vertices)
    lat_min, lat_max = min(p[1] for p in vertices), max(p[1] for p in vertices)
    # POWER's regional endpoint needs >=2 degrees of latitude. Expand the request
    # box, then keep only grid-cell centres that fall inside the Jawa Barat polygon.
    if lat_max - lat_min < 2:
        midpoint = (lat_min + lat_max) / 2
        lat_min, lat_max = midpoint - 1.01, midpoint + 1.01

    outputs = {}
    included_cells = None
    for parameter in ("T2M", "PRECTOTCORR"):
        grid = fetch_parameter(parameter, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"),
                               lat_min, lat_max, lon_min, lon_max)
        cells = sorted({(float(row.LON), float(row.LAT)) for row in grid.itertuples()
                        if point_in_geometry(float(row.LON), float(row.LAT), geometry)})
        if not cells:
            raise RuntimeError("Tidak ada titik grid NASA POWER di dalam batas Jawa Barat.")
        included_cells = cells if included_cells is None else sorted(set(included_cells) & set(cells))
        lon_lat = pd.MultiIndex.from_tuples(cells, names=["LON", "LAT"])
        grid = grid.set_index(["LON", "LAT"]).loc[lon_lat].reset_index()
        outputs[parameter] = grid.groupby("date")[parameter].mean()

    weather = pd.concat(outputs, axis=1).rename(columns={"T2M": "temp_c", "PRECTOTCORR": "rain_mm"})
    weather = weather[["rain_mm", "temp_c"]]
    weather = weather.reindex(pd.date_range(start.normalize(), end.normalize(), freq="D"))
    weather.index.name = "date"
    if weather.isna().any().any():
        missing = weather[weather.isna().any(axis=1)].index.strftime("%Y-%m-%d").tolist()
        raise RuntimeError(f"Ada cuaca hilang pada {len(missing)} tanggal; file tidak ditulis. Contoh: {missing[:5]}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    weather.reset_index()[["date", "rain_mm", "temp_c"]].assign(
        rain_mm=lambda frame: frame.rain_mm.round(3),
        temp_c=lambda frame: frame.temp_c.round(3),
    ).to_csv(args.output, index=False, date_format="%Y-%m-%d")
    print(f"Tersimpan: {args.output}")
    print(f"Rentang: {start:%Y-%m-%d} sampai {end:%Y-%m-%d}; {len(weather):,} hari")
    print(f"Titik grid di dalam batas Jawa Barat: {len(included_cells or [])}")
    print(f"Suhu rata-rata rentang: {weather.temp_c.mean():.2f} °C")
    print(f"Curah hujan rata-rata rentang: {weather.rain_mm.mean():.2f} mm/hari")


if __name__ == "__main__":
    main()
