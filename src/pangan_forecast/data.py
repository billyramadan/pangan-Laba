from pathlib import Path
import pandas as pd


def read_optional(path: str | Path, required: list[str]) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(columns=required)
    frame = pd.read_csv(path)
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f"Kolom {sorted(missing)} tidak ditemukan pada {path}")
    return frame

def normalize_calendar(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize user calendar CSVs while preserving only usable binary flags."""
    calendar = frame.copy()
    calendar.columns = [str(column).strip().lower().replace(" ", "_") for column in calendar.columns]
    if "date" not in calendar.columns and "tanggal" in calendar.columns:
        calendar = calendar.rename(columns={"tanggal": "date"})
    if "date" not in calendar.columns:
        raise ValueError("Data kalender harus memiliki kolom date atau tanggal.")

    aliases = {
        "is_libur_nasional": ("is_libur_nasional", "is_holiday"),
        "is_cuti_bersama": ("is_cuti_bersama",),
        "is_weekend": ("is_weekend", "is_akhir_pekan"),
        "is_ramadan": ("is_ramadan",),
        "is_near_eid": ("is_near_eid",),
        "is_idul_fitri": ("is_idul_fitri", "is_idulfitri"),
    }
    normalized = pd.DataFrame({
        "date": pd.to_datetime(calendar["date"], errors="coerce").dt.normalize()
    })
    for target, candidates in aliases.items():
        source = next((name for name in candidates if name in calendar.columns), None)
        if source is None:
            continue
        values = pd.to_numeric(calendar[source], errors="coerce")
        invalid = values.notna() & ~values.isin([0, 1])
        if values.isna().any() or invalid.any():
            raise ValueError(f"Kolom kalender {source} harus berisi nilai 0/1 tanpa kosong.")
        normalized[target] = values.astype(int)

    # The user's source calendar stores event names in `keterangan`, not as a
    # dedicated binary column. Keep a separate event indicator so Idulfitri
    # isn't collapsed into the generic holiday/collective-leave flags.
    if "is_idul_fitri" not in normalized.columns and "keterangan" in calendar.columns:
        description = calendar["keterangan"].fillna("").astype(str)
        normalized["is_idul_fitri"] = description.str.contains(
            r"idul\s*fitri|lebaran", case=False, regex=True
        ).astype(int)

    if len(normalized.columns) == 1:
        raise ValueError("Data kalender perlu memuat penanda libur, cuti, akhir pekan, Ramadan, atau Idulfitri.")
    if normalized["date"].isna().any():
        raise ValueError("Data kalender memiliki tanggal yang tidak valid.")
    if normalized["date"].duplicated().any():
        raise ValueError("Data kalender memiliki tanggal duplikat.")
    return normalized.sort_values("date").reset_index(drop=True)


def load_and_merge(prices_path: str | Path = "data/raw/prices.csv",
                   weather_path: str | Path = "data/raw/weather.csv",
                   calendar_path: str | Path = "data/raw/calendar.csv") -> pd.DataFrame:
    prices = read_optional(prices_path, ["date", "commodity", "price"])
    if prices.empty:
        raise FileNotFoundError(f"Data harga belum ada: {prices_path}. Lihat README.md")
    prices["date"] = pd.to_datetime(prices["date"], errors="coerce").dt.normalize()
    prices["price"] = pd.to_numeric(prices["price"], errors="coerce")
    prices["commodity"] = prices["commodity"].fillna("").astype(str).str.strip()
    prices = prices.dropna(subset=["date", "price"])
    prices = prices[prices["commodity"].ne("")]
    prices = prices[prices["price"] > 0]
    if prices.empty:
        raise ValueError("Tidak ada baris harga positif dengan tanggal valid.")
    keys = ["date", "commodity"] + (["location"] if "location" in prices else [])
    prices = prices.groupby(keys, as_index=False)["price"].mean()

    weather = read_optional(weather_path, ["date", "rain_mm", "temp_c"])
    if not weather.empty:
        weather["date"] = pd.to_datetime(weather["date"], errors="coerce").dt.normalize()
        for col in weather.columns.difference(["date"]):
            weather[col] = pd.to_numeric(weather[col], errors="coerce")
        weather = weather.dropna(subset=["date"]).groupby("date", as_index=False).mean(numeric_only=True)

    # Read the whole calendar first because user supplied files may use either
    # `date` or the Indonesian `tanggal` header. normalize_calendar validates
    # the date column and maps flags (including Idulfitri text) to model names.
    calendar = read_optional(calendar_path, [])
    if not calendar.empty:
        calendar = normalize_calendar(calendar)
    calendar_features = [col for col in ["is_libur_nasional", "is_cuti_bersama", "is_weekend",
                                         "is_ramadan", "is_near_eid", "is_idul_fitri"] if col in calendar.columns]
    calendar_by_date = (calendar.set_index("date")[calendar_features]
                        if not calendar.empty else pd.DataFrame())

    result = []
    grouping = ["commodity"] + (["location"] if "location" in prices else [])
    for _, group in prices.groupby(grouping, dropna=False):
        # Be tolerant if a caller passes dates as the index instead of a
        # regular column. The normal pipeline has a `date` column here.
        if "date" not in group.columns:
            if group.index.name == "date":
                group = group.reset_index()
            else:
                raise ValueError(
                    "Kolom tanggal 'date' tidak ditemukan sebelum pengisian kalender harian. "
                    f"Kolom tersedia: {list(group.columns)}"
                )
        elif group.index.name == "date":
            # Avoid ambiguous `date` references when it exists as both an
            # index name and a column; the column is the canonical source.
            group = group.reset_index(drop=True)
        group["date"] = pd.to_datetime(group["date"], errors="coerce").dt.normalize()
        group = group.dropna(subset=["date"])
        if group.empty:
            continue
        # Collapse duplicate observations on the same day before reindexing.
        aggregations = {column: "first" for column in grouping}
        aggregations["price"] = "mean"
        group = group.groupby("date", as_index=False, sort=True).agg(aggregations)
        group = group.sort_values("date").set_index("date")
        full_index = pd.date_range(group.index.min(), group.index.max(), freq="D")
        group = group.reindex(full_index)
        group.index.name = "date"
        # Join climate to the complete daily calendar, not just dates with a
        # price observation, so monthly-aligned weather remains exact.
        if not weather.empty:
            weather_columns = [col for col in weather.columns if col != "date"]
            weather_by_date = weather.set_index("date")[weather_columns]
            group = group.join(weather_by_date, how="left")
        else:
            group["rain_mm"] = float("nan")
            group["temp_c"] = float("nan")
        if not calendar_by_date.empty:
            group = group.join(calendar_by_date, how="left")
        for col in grouping:
            group[col] = group[col].ffill().bfill()
        # Interpolasi hanya mengisi sela dalam seri; tidak mengisi sebelum/sesudah observasi.
        group["price"] = group["price"].interpolate(limit_area="inside")
        for col in ["rain_mm", "temp_c"]:
            group[col] = group[col].interpolate(limit_area="inside")
        for col in calendar_features:
            group[col] = group[col].fillna(0)
        result.append(group.reset_index())
    clean = pd.concat(result, ignore_index=True).dropna(subset=["price"])
    return clean.sort_values(grouping + ["date"]).reset_index(drop=True)
