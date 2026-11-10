"""Lapisan layanan (backend) PanganLaba — bebas Streamlit.

Satu-satunya modul yang menghubungkan UI (app.py) dengan logika bisnis.
Semua fungsi murni: menerima data, mengembalikan struktur/data; tidak ada
render, widget, atau session_state.
"""

from __future__ import annotations

import math
import os
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

# --------------------------------------------------------------------------
# Path proyek & hasil model
# --------------------------------------------------------------------------

def project_paths(root: Path) -> dict[str, Path]:
    """Path penting proyek, dipusatkan di satu tempat."""
    configured_db = os.environ.get("PANGAN_DB_PATH", "").strip()
    db_path = Path(configured_db).expanduser() if configured_db else root / "data/app_users.sqlite3"
    if configured_db and not db_path.is_absolute():
        db_path = root / db_path
    return {
        "prices": root / "data/raw/prices.csv",
        "weather": root / "data/raw/weather.csv",
        "calendar": root / "data/raw/calendar.csv",
        "metrics": root / "reports/model_comparison.csv",
        "forecast": root / "reports/forecasts.csv",
        "db": db_path,
        "clean_dir": root / "data/processed",
        "upload_dir": root / "data/uploads",
        "feedback_csv": root / "data/umkm_user_tests/feedback.csv",
    }


def has_model_results(paths: dict[str, Path]) -> bool:
    """Model dianggap ada bila file laporan + seluruh data input tersedia."""
    inputs = [paths["prices"]]
    for key in ("weather", "calendar"):
        if paths[key].exists():
            inputs.append(paths[key])
    return (
        paths["metrics"].exists()
        and paths["forecast"].exists()
        and all(p.exists() for p in inputs)
    )


def compute_overview(prices_path: Path) -> tuple[pd.DataFrame, str, str, str]:
    """Ringkasan domain data harga: wilayah, periode, jumlah komoditas."""
    if not prices_path.exists():
        return pd.DataFrame(), "Belum tersedia", "-", "-"
    overview = pd.read_csv(prices_path, parse_dates=["date"])
    locations = overview["location"].dropna().astype(str).unique() if "location" in overview else []
    region = locations[0] if len(locations) == 1 else "Beberapa wilayah"
    date_start = overview["date"].min().strftime("%d %b %Y")
    date_end = overview["date"].max().strftime("%d %b %Y")
    return overview, region, date_start, date_end


def load_metrics_forecast(paths: dict[str, Path]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Baca hasil evaluasi model (metrics) dan prakiraan (forecast)."""
    metrics = pd.read_csv(paths["metrics"])
    forecast = pd.read_csv(paths["forecast"], parse_dates=["target_date", "origin_date"])
    return metrics, forecast


def build_current_forecasts(
    root: Path,
    model_name: str,
    feature_name: str,
    *,
    commodities: list[str] | None = None,
    restock_days: int = 7,
    stale_after_days: int = 7,
) -> dict:
    """Create current forecasts from latest PIHPS observations and saved models."""
    if model_name not in {"LSTM", "GRU"}:
        raise ValueError("Pilih model LSTM atau GRU.")
    feature_suffix = {
        "harga saja": "price",
        "harga + cuaca + kalender + siklus tanggal": "external",
    }.get(feature_name)
    if feature_suffix is None:
        raise ValueError("Paket fitur model tidak dikenali.")

    paths = project_paths(root)
    price_path = paths["prices"]
    clean_path = paths["clean_dir"] / "combined_daily.csv"
    if not price_path.exists() or not clean_path.exists():
        raise FileNotFoundError("Data harga bersih belum tersedia. Impor dan siapkan data PIHPS terlebih dahulu.")
    prices = pd.read_csv(price_path, parse_dates=["date"])
    clean = pd.read_csv(clean_path, parse_dates=["date"])
    if prices.empty or clean.empty:
        raise ValueError("Data harga belum berisi observasi.")
    prices["price"] = pd.to_numeric(prices["price"], errors="coerce")
    clean["price"] = pd.to_numeric(clean["price"], errors="coerce")
    prices = prices.dropna(subset=["date", "price"])
    clean = clean.dropna(subset=["date", "price"])

    requested = {str(x).strip().casefold() for x in commodities or [] if str(x).strip()}
    if "location" in prices:
        depok_mask = prices["location"].astype(str).str.contains("depok", case=False, na=False)
        if depok_mask.any():
            prices = prices[depok_mask]
    if "location" in clean:
        clean = clean[clean["location"].astype(str).str.contains("depok", case=False, na=False)]
    if "commodity" not in prices or "commodity" not in clean:
        raise ValueError("Kolom komoditas tidak ditemukan pada data harga.")

    available = sorted(prices["commodity"].dropna().astype(str).unique())
    if requested:
        by_key = {name.strip().casefold(): name for name in available}
        missing = sorted(requested - set(by_key))
        if missing:
            raise ValueError("Komoditas tidak ditemukan pada data PIHPS: " + ", ".join(missing))
        wanted_order = [str(x).strip() for x in (commodities or []) if str(x).strip()]
        selected = list(dict.fromkeys(by_key[name.casefold()] for name in wanted_order))
    else:
        selected = available

    today = datetime.now(ZoneInfo("Asia/Jakarta")).date()
    slug_base = lambda value: re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")
    quote_map: dict[str, dict] = {}
    selected_payload = None
    from pangan_forecast.models import forecast_next
    from pangan_forecast.recommend import make_recommendation

    for commodity in selected:
        observed = prices[prices["commodity"].astype(str).str.casefold() == commodity.casefold()]
        if observed.empty:
            continue
        observed = observed.sort_values("date")
        latest = observed.iloc[-1]
        last_date = pd.Timestamp(latest["date"]).normalize()
        age_days = max(0, (today - last_date.date()).days)
        group = clean[clean["commodity"].astype(str).str.casefold() == commodity.casefold()]
        group = group[group["date"] <= last_date].sort_values("date")

        model_slug = f"{slug_base(commodity)}_{model_name.lower()}_{feature_suffix}"
        model_path = root / "models" / f"{model_slug}.h5"
        metadata_path = root / "models" / f"{model_slug}.json"
        base = {
            "current_price": float(latest["price"]),
            "price_date": last_date.strftime("%Y-%m-%d"),
            "age_days": age_days,
            "stale": age_days > stale_after_days,
            "model": model_name,
            "features": feature_name,
        }
        if not model_path.is_file() or not metadata_path.is_file():
            quote_map[commodity] = {**base, "status": "unavailable",
                                    "error": "Model untuk komoditas ini belum dilatih."}
            if commodities and commodity.casefold() == str(commodities[0]).casefold():
                selected_payload = {**quote_map[commodity], "commodity": commodity,
                                    "history": [{"date": pd.Timestamp(row.date).strftime("%Y-%m-%d"),
                                                 "price": float(row.price)} for row in clean[
                                                     clean["commodity"].astype(str).str.casefold() == commodity.casefold()
                                                 ].sort_values("date").tail(14).itertuples()]}
            continue
        if group.empty or group["date"].max().normalize() < last_date:
            quote_map[commodity] = {**base, "status": "unavailable",
                                    "error": "Riwayat fitur belum mencakup tanggal harga terakhir."}
            continue
        try:
            predicted = forecast_next(model_path, metadata_path, group)
        except Exception as exc:
            quote_map[commodity] = {**base, "status": "unavailable",
                                    "error": f"Model belum dapat membuat prediksi ({type(exc).__name__})."}
            continue

        forecast = [
            {"step": step,
             "target_date": (last_date + pd.Timedelta(days=step)).strftime("%Y-%m-%d"),
             "predicted": max(0.0, float(value))}
            for step, value in enumerate(predicted[:7], start=1)
        ]
        if len(forecast) < 7:
            quote_map[commodity] = {**base, "status": "unavailable",
                                    "error": "Model belum menghasilkan prediksi lengkap 7 hari."}
            continue
        decision = [item["predicted"] for item in forecast[:max(1, min(7, int(restock_days)))]]
        current_price = float(latest["price"])
        stale = age_days > stale_after_days
        quote = {
            **base,
            "status": "stale" if stale else "ready",
            "stale": stale,
            "forecast": forecast,
            "forecast_mean": sum(decision) / len(decision) if decision else None,
            "expected_change_pct": ((sum(decision) / len(decision) / current_price - 1) * 100)
                if decision and current_price > 0 else None,
            "recommendation": None if stale else make_recommendation(current_price, decision),
        }
        quote_map[commodity] = quote
        if commodities and commodity.casefold() == str(commodities[0]).casefold():
            selected_payload = {
                **quote,
                "commodity": commodity,
                "history": [{"date": pd.Timestamp(row.date).strftime("%Y-%m-%d"),
                             "price": float(row.price)} for row in group.tail(14).itertuples()],
            }

    return {
        "model": model_name,
        "features": feature_name,
        "as_of_date": today.strftime("%Y-%m-%d"),
        "stale_after_days": stale_after_days,
        "quotes": quote_map,
        "selected": selected_payload,
    }


# --------------------------------------------------------------------------
# Skenario belanja: pilih komoditas/model/tanggal, rekomendasi
# --------------------------------------------------------------------------

def build_scenario(
    pred: pd.DataFrame,
    commodity: str,
    model_name: str,
    feature_name: str,
    origin: str,
    restock_days: int,
):
    """Bangun potongan data untuk satu pilihan komoditas+model+tanggal.

    Mengembalikan (forecast, last_price, decision_prices, recommendation).
    """
    from pangan_forecast.recommend import make_recommendation

    view = pred[(pred["model"] == model_name) & (pred["features"] == feature_name)]
    forecast = view[view["origin_date"].dt.strftime("%Y-%m-%d") == origin].sort_values("step")
    if forecast.empty:
        return forecast, None, [], None
    last = float(forecast.iloc[0]["reference_price"])
    decision = forecast["predicted"].head(restock_days).tolist()
    return forecast, last, decision, make_recommendation(last, decision)


# --------------------------------------------------------------------------
# Kalkulator laba menu
# --------------------------------------------------------------------------

def build_price_lookup(pred, model_name, feature_name, scenario_date, restock_days) -> dict:
    """Harga acuan + prediksi per komoditas pada tanggal skenario."""
    rows = pred[
        (pred["model"] == model_name)
        & (pred["features"] == feature_name)
        & (pred["origin_date"] == scenario_date)
        & (pd.to_numeric(pred["step"], errors="coerce") <= restock_days)
    ]
    if rows.empty:
        return {}
    return (
        rows.groupby("commodity", as_index=True)
        .agg(reference_price=("reference_price", "first"),
             predicted_price=("predicted", "mean"))
        .to_dict("index")
    )


def compute_profit_report(
    recipe_rows: pd.DataFrame,
    pred: pd.DataFrame,
    *,
    menu_name: str,
    model_name: str,
    feature_name: str,
    origin: str,
    restock_days: int,
    selling_price: float,
    portions_sold: int,
    other_cost_per_portion: float,
    fixed_cost: float,
    sales_period: str,
) -> tuple[dict, list[str], list[str]]:
    """Hitung laba menu dari resep + harga acuan/prediksi. Murni, tanpa st.

    Mengembalikan (report, missing_price, fallback_forecast).
    """
    scenario_date = pd.to_datetime(origin)
    price_lookup = build_price_lookup(pred, model_name, feature_name, scenario_date, restock_days)

    current_ingredient_cost = 0.0
    predicted_ingredient_cost = 0.0
    missing_price: list[str] = []
    fallback_forecast: list[str] = []
    ingredient_details: list[dict] = []

    for _, ingredient in recipe_rows.iterrows():
        name = ingredient["commodity"]
        grams = float(ingredient["grams_per_portion"])
        actual = ingredient["actual_price_rp_per_kg"]
        prices_for_item = price_lookup.get(name, {})
        reference = prices_for_item.get("reference_price")
        predicted_price = prices_for_item.get("predicted_price")
        current_unit_price = float(actual) if pd.notna(actual) and float(actual) > 0 else reference
        if current_unit_price is None or pd.isna(current_unit_price) or float(current_unit_price) <= 0:
            missing_price.append(name)
            continue
        if predicted_price is None or pd.isna(predicted_price):
            predicted_price = current_unit_price
            fallback_forecast.append(name)
        predicted_price = max(0.0, float(predicted_price))
        current_ingredient_cost += grams / 1000 * float(current_unit_price)
        predicted_ingredient_cost += grams / 1000 * predicted_price
        ingredient_details.append({
            "bahan": name,
            "takaran_gram_per_porsi": grams,
            "harga_acuan_rp_per_kg": float(current_unit_price),
            "harga_prediksi_rp_per_kg": predicted_price,
        })

    if missing_price:
        return {}, sorted(set(missing_price)), sorted(set(fallback_forecast))

    revenue = float(selling_price * portions_sold)
    variable_cost = float(other_cost_per_portion * portions_sold)
    current_gross_profit = revenue - current_ingredient_cost * portions_sold
    current_net_profit = current_gross_profit - variable_cost - fixed_cost
    predicted_net_profit = (
        revenue - predicted_ingredient_cost * portions_sold - variable_cost - fixed_cost
    )
    current_contribution = selling_price - current_ingredient_cost - other_cost_per_portion
    if current_contribution > 0:
        break_even = math.ceil(fixed_cost / current_contribution) if fixed_cost else 0
    else:
        break_even = None

    report = {
        "menu_name": menu_name.strip(),
        "period_label": sales_period,
        "portions_sold": int(portions_sold),
        "selling_price": float(selling_price),
        "revenue": revenue,
        "ingredient_cost_per_portion": current_ingredient_cost,
        "total_ingredient_cost": current_ingredient_cost * portions_sold,
        "other_cost_per_portion": float(other_cost_per_portion),
        "fixed_cost": float(fixed_cost),
        "gross_profit": current_gross_profit,
        "net_profit": current_net_profit,
        "predicted_ingredient_cost_per_portion": predicted_ingredient_cost,
        "predicted_net_profit": predicted_net_profit,
        "net_margin_pct": current_net_profit / revenue * 100 if revenue else 0.0,
        "break_even_portions": int(break_even) if break_even is not None else None,
        "reference_date": str(origin),
        "model_name": model_name,
        "feature_name": feature_name,
        "recipe": ingredient_details,
    }
    return report, [], sorted(set(fallback_forecast))


# --------------------------------------------------------------------------
# Pelatihan & impor data
# --------------------------------------------------------------------------

def run_training(
    clean: pd.DataFrame,
    root: Path,
    source_label: str,
    *,
    epochs: int = 15,
    batch_size: int = 128,
) -> pd.DataFrame:
    """Simpan data bersih lalu latih semua kombinasi model. Murni, tanpa st."""
    from pangan_forecast.models import run_experiments, refit_full_history_models

    paths = project_paths(root)
    paths["clean_dir"].mkdir(parents=True, exist_ok=True)
    clean.to_csv(paths["clean_dir"] / "combined_daily.csv", index=False)
    clean.to_csv(paths["clean_dir"] / "uploaded_daily.csv", index=False)
    metrics_new, _ = run_experiments(
        clean, root, window=30, horizon=7,
        epochs=epochs, batch_size=batch_size, data_source=source_label,
    )
    if metrics_new.empty:
        raise ValueError("Data belum cukup untuk mengevaluasi LSTM/GRU.")
    refit_full_history_models(clean, root, window=30, horizon=7,
                              epochs=epochs, batch_size=batch_size)
    return metrics_new


# --------------------------------------------------------------------------
# Agregasi hasil evaluasi model (tab penelitian)
# --------------------------------------------------------------------------

EXTERNAL_FEATURE = "harga + cuaca + kalender + siklus tanggal"
PRICE_ONLY_FEATURE = "harga saja"


def evaluate_model_results(metrics: pd.DataFrame) -> dict:
    """Rekap lintas model: median skor, model terbaik, kemenangan fitur eksternal."""
    median_scores = (metrics.groupby(["model", "features"], as_index=False)
                     [["MAE", "RMSE", "MAPE"]].median().sort_values("MAE"))
    best_score = median_scores.iloc[0]
    mae_pairs = metrics.pivot_table(index=["commodity", "model"], columns="features", values="MAE")
    paired = mae_pairs.dropna(subset=[PRICE_ONLY_FEATURE, EXTERNAL_FEATURE])
    external_wins = int((paired[EXTERNAL_FEATURE] < paired[PRICE_ONLY_FEATURE]).sum())
    return {
        "median_scores": median_scores,
        "best_score": best_score,
        "external_wins": external_wins,
        "paired_count": len(paired),
        "commodity_count": int(metrics["commodity"].nunique()),
    }


def model_comparison_for(metrics: pd.DataFrame, commodity: str):
    """Data perbandingan MAE satu komoditas: tabel rapi + seri grafik."""
    cm = metrics[metrics["commodity"] == commodity].sort_values("MAE")
    chart = (cm.pivot_table(index="model", columns="features", values="MAE")
             .reindex(["LSTM", "GRU"]))
    series = [
        chart.get(PRICE_ONLY_FEATURE, pd.Series(dtype=float)),
        chart.get(EXTERNAL_FEATURE, pd.Series(dtype=float)),
    ]
    return cm, series


def cross_commodity_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    """Ringkasan median lintas komoditas, per model+paket fitur."""
    return (metrics.groupby(["model", "features"], as_index=False)
            .agg(jumlah_komoditas=("commodity", "nunique"),
                 median_MAE=("MAE", "median"), median_RMSE=("RMSE", "median"),
                 median_MAPE=("MAPE", "median"))
            .rename(columns={"model": "Model", "features": "Paket fitur",
                             "jumlah_komoditas": "Jumlah komoditas",
                             "median_MAE": "Median MAE (Rp/kg)",
                             "median_RMSE": "Median RMSE (Rp/kg)",
                             "median_MAPE": "Median MAPE (%)"}))


# --------------------------------------------------------------------------
# Umpan balik uji coba UMKM
# --------------------------------------------------------------------------

def append_umkm_feedback(path: Path, record: dict) -> None:
    """Tambahkan satu catatan umpan balik anonim ke CSV lokal."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([record]).to_csv(
        path, mode="a", header=not path.exists(), index=False, encoding="utf-8"
    )
