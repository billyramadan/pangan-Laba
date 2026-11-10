import pandas as pd
import pytest

from pangan_forecast.service import (
    build_scenario,
    compute_overview,
    compute_profit_report,
    cross_commodity_summary,
    evaluate_model_results,
    has_model_results,
    project_paths,
)


def _forecast():
    return pd.DataFrame(
        {
            "commodity": ["Beras", "Beras", "Beras", "Telur Ayam"],
            "model": ["LSTM", "LSTM", "GRU", "LSTM"],
            "features": ["harga saja", "harga saja", "harga saja", "harga saja"],
            "origin_date": pd.to_datetime(["2025-08-28"] * 4),
            "step": [1, 2, 1, 1],
            "reference_price": [10000.0, 10000.0, 10000.0, 20000.0],
            "actual": [10100.0, 10200.0, 10100.0, 20000.0],
            "predicted": [10100.0, 10300.0, 10150.0, 20500.0],
        }
    )


def _metrics():
    rows = []
    for model in ("LSTM", "GRU"):
        for features in ("harga saja", "harga + cuaca + kalender + siklus tanggal"):
            for commodity in ("Beras", "Telur Ayam"):
                rows.append({"commodity": commodity, "model": model, "features": features,
                             "MAE": 1000.0, "RMSE": 1400.0, "MAPE": 5.0})
    return pd.DataFrame(rows)


def test_project_paths(tmp_path):
    paths = project_paths(tmp_path)
    assert paths["prices"].name == "prices.csv"
    assert paths["metrics"].name == "model_comparison.csv"


def test_has_model_results_detects_present(tmp_path):
    paths = project_paths(tmp_path)
    paths["prices"].touch()
    paths["metrics"].touch()
    paths["forecast"].touch()
    assert has_model_results(paths) is True


def test_compute_overview(tmp_path):
    csv = tmp_path / "prices.csv"
    csv.write_text("date,commodity,price,location\n2025-01-01,Beras,10000,Kota Depok\n2025-01-02,Beras,10100,Kota Depok\n", encoding="utf-8")
    _, region, start, end = compute_overview(csv)
    assert region == "Kota Depok"
    assert "2025" in start and "2025" in end


def test_build_scenario_returns_empty_for_unknown():
    forecast, last, decision, recommendation = build_scenario(_forecast(), "Beras", "LSTM", "harga saja", "2099-01-01", 7)
    assert forecast.empty
    assert last is None
    assert recommendation is None


def test_compute_profit_report_full_recipe():
    pred = _forecast()
    recipe = pd.DataFrame(
        [
            {"commodity": "Beras", "grams_per_portion": 500, "actual_price_rp_per_kg": 10000},
            {"commodity": "Telur Ayam", "grams_per_portion": 250, "actual_price_rp_per_kg": 20000},
        ]
    )
    report, missing, fallback = compute_profit_report(
        recipe, pred, menu_name="Nasi Telur", model_name="LSTM", feature_name="harga saja",
        origin="2025-08-28", restock_days=7, selling_price=15000, portions_sold=2,
        other_cost_per_portion=0, fixed_cost=0, sales_period="Harian")
    assert not missing
    assert report["revenue"] == 30000
    assert report["total_ingredient_cost"] == 20000
    assert report["net_profit"] == 10000
    assert report["net_margin_pct"] == pytest.approx(10000 / 30000 * 100)
    assert len(report["recipe"]) == 2


def test_compute_profit_report_missing_price_returns_empty():
    pred = _forecast()
    recipe = pd.DataFrame([{"commodity": "Gula Pasir", "grams_per_portion": 100, "actual_price_rp_per_kg": 0}])
    report, missing, fallback = compute_profit_report(
        recipe, pred, menu_name="X", model_name="LSTM", feature_name="harga saja",
        origin="2025-08-28", restock_days=7, selling_price=10000, portions_sold=1,
        other_cost_per_portion=0, fixed_cost=0, sales_period="Harian")
    assert report == {}
    assert missing == ["Gula Pasir"]


def test_evaluate_model_results():
    result = evaluate_model_results(_metrics())
    assert result["commodity_count"] == 2
    assert result["external_wins"] == 0
    assert result["paired_count"] == 2


def test_cross_commodity_summary_columns():
    summary = cross_commodity_summary(_metrics())
    assert "Median MAE (Rp/kg)" in summary.columns
    assert len(summary) == 4
