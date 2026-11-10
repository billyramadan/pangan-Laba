from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "source_pihps"
OUT = ROOT / "data" / "processed" / "prices_depok_candidate.csv"
sys.path.insert(0, str(ROOT / "backend" / "src"))
from pangan_forecast.pihps_excel import inspect_pihps_excel, extract_pihps_series

candidates: dict[tuple[str, int], list[tuple[Path, pd.DataFrame, bool]]] = defaultdict(list)
errors: list[str] = []
for folder in sorted(path for path in SOURCE.iterdir() if path.is_dir()):
    commodity = re.sub(r"^Harga\s+Komoditas\s+", "", folder.name, flags=re.IGNORECASE)
    commodity = re.sub(r"\s+2020-2026$", "", commodity).strip()
    for workbook in sorted(folder.glob("*.xlsx")):
        try:
            content = workbook.read_bytes()
            info = inspect_pihps_excel(content)
            depok = next((row for row in info["rows"]
                          if row["label"].strip().casefold() in {"kota depok", "depok"}), None)
            if depok is None:
                errors.append(f"{workbook.name}: baris Kota Depok tidak ditemukan")
                continue
            series = extract_pihps_series(content, depok["row_index"], commodity, "Kota Depok")
            years_in_name = set(re.findall(r"(?<!\d)(20\d{2})(?!\d)", workbook.stem))
            for year, group in series.groupby(series["date"].dt.year):
                candidates[(commodity, int(year))].append(
                    (workbook, group.copy(), str(year) in years_in_name)
                )
        except Exception as exc:
            errors.append(f"{workbook.name}: {exc}")

chosen: list[pd.DataFrame] = []
for key, options in sorted(candidates.items()):
    commodity, year = key
    # Prefer the workbook named for the dates it actually contains; if names are wrong,
    # use the fullest extract for that year.
    path, frame, _ = max(options, key=lambda item: (item[2], len(item[1]), item[0].name))
    chosen.append(frame)
    if len(options) > 1:
        print(f"Pilih {commodity} {year}: {path.name} ({len(frame)} observasi; {len(options)} file berisi tahun ini)")

if errors:
    raise SystemExit("Ada workbook yang gagal dibaca:\n" + "\n".join(errors))
if not chosen:
    raise SystemExit("Tidak ada data Kota Depok yang berhasil diekstrak.")

prices = pd.concat(chosen, ignore_index=True)
prices = prices.dropna(subset=["date", "price"])
prices["price"] = pd.to_numeric(prices["price"], errors="coerce")
prices = prices[prices["price"] > 0]
prices = prices.sort_values(["commodity", "date"]).drop_duplicates(
    ["date", "commodity", "location"], keep="last"
).reset_index(drop=True)
OUT.parent.mkdir(parents=True, exist_ok=True)
prices.to_csv(OUT, index=False, date_format="%Y-%m-%d")
print(f"Preview tersimpan: {OUT}")
print(f"Baris: {len(prices):,}; komoditas: {prices['commodity'].nunique()}; lokasi: {prices['location'].unique().tolist()}")
print(prices.groupby("commodity")["date"].agg(["min", "max", "count"]).to_string())
