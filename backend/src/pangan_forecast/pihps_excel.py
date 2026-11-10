from datetime import date, datetime
from io import BytesIO
import re
import pandas as pd


def _parse_pihps_date(value):
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return pd.Timestamp(value).normalize()
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"\s*(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})\s*", value)
    if not match:
        return None
    day, month, year = map(int, match.groups())
    try:
        return pd.Timestamp(year=year, month=month, day=day)
    except ValueError:
        return None


def _read_sheet(file_bytes):
    try:
        raw = pd.read_excel(BytesIO(file_bytes), sheet_name=0, header=None, engine="openpyxl")
    except Exception as exc:
        raise ValueError(f"File tidak bisa dibaca sebagai Excel PIHPS (.xlsx): {exc}") from exc
    header_index, date_columns, dates = None, None, None
    for row_index in range(min(len(raw), 30)):
        parsed = [(column, _parse_pihps_date(value)) for column, value in enumerate(raw.iloc[row_index].tolist())]
        parsed = [(column, value) for column, value in parsed if value is not None]
        if len(parsed) >= 3:
            header_index = row_index
            date_columns = [column for column, _ in parsed]
            dates = [value for _, value in parsed]
            break
    if header_index is None:
        raise ValueError("Baris tanggal PIHPS tidak ditemukan. Pastikan workbook memakai format laporan harga berdasarkan komoditas.")
    if date_columns[0] < 2:
        raise ValueError("Format workbook tidak sesuai: kolom tanggal seharusnya dimulai setelah kolom lokasi.")
    return raw, header_index, date_columns, dates


def inspect_pihps_excel(file_bytes):
    """Return date coverage and selectable rows from a PIHPS wide Excel report."""
    raw, header_index, date_columns, dates = _read_sheet(file_bytes)
    rows = []
    for row_index in range(header_index + 1, len(raw)):
        label = raw.iat[row_index, 1] if raw.shape[1] > 1 else None
        if pd.isna(label) or not str(label).strip():
            continue
        values = raw.iloc[row_index, date_columns].tolist()
        numeric = [_parse_price(value) for value in values]
        valid = [value for value in numeric if value is not None]
        if valid:
            code = raw.iat[row_index, 0]
            code = "" if pd.isna(code) else str(code).strip()
            label = str(label).strip()
            rows.append({"row_index": row_index, "label": label, "code": code,
                         "display": f"{code} — {label}" if code else label})
    if not rows:
        raise ValueError("Tidak ditemukan baris lokasi dengan nilai harga di workbook.")
    return {"rows": rows, "date_start": min(dates), "date_end": max(dates),
            "n_dates": len(dates), "n_rows": len(raw)}


def _parse_price(value):
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        value = float(value)
        return value if value > 0 else None
    text = str(value).strip()
    if not text or text in {"-", "—", "–"}:
        return None
    text = re.sub(r"(?i)rp\.?\s*", "", text).replace(" ", "")
    # PIHPS formats rupiah as thousands with separators, e.g. 18,200 or 18.200.
    text = text.replace(".", "").replace(",", "")
    try:
        result = float(text)
        return result if result > 0 else None
    except ValueError:
        return None


def extract_pihps_series(file_bytes, row_index, commodity, location):
    """Convert one selected PIHPS location row into date/commodity/price/location rows."""
    raw, header_index, date_columns, dates = _read_sheet(file_bytes)
    if row_index <= header_index or row_index >= len(raw):
        raise ValueError("Baris lokasi yang dipilih tidak ditemukan di file.")
    label = raw.iat[row_index, 1]
    if pd.isna(label):
        raise ValueError("Baris lokasi yang dipilih tidak memiliki nama lokasi.")
    values = [_parse_price(value) for value in raw.iloc[row_index, date_columns].tolist()]
    frame = pd.DataFrame({"date": dates, "commodity": str(commodity).strip(),
                          "price": values, "location": str(location).strip()})
    frame = frame.dropna(subset=["price"])
    if frame.empty:
        raise ValueError(f"Tidak ada harga yang terbaca pada baris {label}.")
    return frame
