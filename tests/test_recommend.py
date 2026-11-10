import pandas as pd
import pytest

from pangan_forecast.recommend import make_recommendation, simulate_purchase_policy


def test_recommendation_buy_when_increasing():
    result = make_recommendation(10000, [10500])
    assert result["recommendation"] == "Beli sekarang"
    assert result["expected_change_pct"] == pytest.approx(5.0)


def test_recommendation_delay_when_decreasing():
    result = make_recommendation(10000, [9000])
    assert result["recommendation"] == "Tunda dulu"


def test_recommendation_neutral_within_threshold():
    result = make_recommendation(10000, [10200])
    assert result["recommendation"] == "Beli sesuai kebutuhan"


def test_recommendation_negative_forecast_floored_at_zero():
    result = make_recommendation(10000, [-500])
    assert result["forecast_mean"] == 0.0
    assert result["recommendation"] == "Tunda dulu"


@pytest.mark.parametrize("bad", [(0, [10000]), (10000, []), (10000, [float("nan")])])
def test_recommendation_invalid_input(bad):
    with pytest.raises(ValueError):
        make_recommendation(*bad)


def test_simulation_table_basic():
    frame = pd.DataFrame(
        {
            "origin_date": pd.date_range("2025-08-28", periods=7),
            "step": [1] * 7,
            "reference_price": [10000, 9800, 9500, 9700, 9900, 10100, 10300],
            "predicted": [9900, 9600, 9400, 9800, 10000, 10200, 10400],
        }
    )
    result = simulate_purchase_policy(frame, quantity_kg=1, threshold=0.05,
                                      max_wait_days=2, cycle_days=7)
    assert len(result) == 1
    assert result.iloc[0]["cycle"] == 1
    assert (result["policy_cost_rp"] <= result["baseline_cost_rp"]).all()


def test_simulation_missing_column():
    with pytest.raises(ValueError):
        simulate_purchase_policy(pd.DataFrame({"origin_date": ["2025-01-01"]}))
