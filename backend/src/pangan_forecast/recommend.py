from math import isfinite

import pandas as pd


def make_recommendation(last_price: float, forecast_prices, threshold: float = 0.05) -> dict:
    """Give a simple recommendation from a reference price and forecast prices."""
    try:
        reference = float(last_price)
        limit = float(threshold)
        values = [float(value) for value in forecast_prices]
    except (TypeError, ValueError) as exc:
        raise ValueError("Harga, batas perubahan, dan prakiraan harus berupa angka.") from exc

    if not isfinite(reference) or reference <= 0:
        raise ValueError("Harga acuan harus berupa angka positif yang valid.")
    if not isfinite(limit) or not 0 <= limit < 1:
        raise ValueError("Batas perubahan harus bernilai minimal 0 dan kurang dari 1 (100%).")
    if not values or any(not isfinite(value) for value in values):
        raise ValueError("Prakiraan harus berisi minimal satu angka yang valid.")

    # A neural model can occasionally predict a negative price; floor it at Rp0.
    values = [max(0.0, value) for value in values]
    forecast_mean = sum(values) / len(values)
    change = forecast_mean / reference - 1
    if change >= limit:
        advice = "Beli sekarang"
    elif change <= -limit:
        advice = "Tunda dulu"
    else:
        advice = "Beli sesuai kebutuhan"
    return {"recommendation": advice, "expected_change_pct": change * 100,
            "last_price": reference, "forecast_mean": forecast_mean}


def simulate_purchase_policy(forecasts, quantity_kg=1.0, threshold=0.05,
                             max_wait_days=2, cycle_days=7,
                             decision_horizon_days=None):
    """Compare fixed-interval buying with a forecast-guided, bounded-delay policy.

    Decisions use the first `decision_horizon_days` forecasts at each origin.
    Realized costs use the observed reference price on the chosen purchase date.
    One fixed-volume purchase is assumed per non-overlapping cycle.
    """
    required = {"origin_date", "step", "reference_price", "predicted"}
    missing = required - set(forecasts.columns)
    if missing:
        raise ValueError(f"Kolom simulasi tidak lengkap: {', '.join(sorted(missing))}")
    if decision_horizon_days is None:
        decision_horizon_days = cycle_days
    try:
        quantity_kg = float(quantity_kg)
        threshold = float(threshold)
        cycle_days = int(cycle_days)
        max_wait_days = int(max_wait_days)
        decision_horizon_days = int(decision_horizon_days)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Volume harus numerik dan jumlah hari harus bilangan bulat.") from exc
    if not isfinite(quantity_kg) or quantity_kg <= 0:
        raise ValueError("Volume dan panjang siklus harus positif; penundaan tidak boleh negatif.")
    if not isfinite(threshold) or not 0 <= threshold < 1:
        raise ValueError("Batas perubahan harus bernilai minimal 0 dan kurang dari 1 (100%).")
    if cycle_days <= 0 or decision_horizon_days <= 0 or max_wait_days < 0:
        raise ValueError("Volume dan panjang siklus harus positif; penundaan tidak boleh negatif.")

    data = forecasts.copy()
    data["origin_date"] = pd.to_datetime(data["origin_date"], errors="coerce")
    data["step"] = pd.to_numeric(data["step"], errors="coerce")
    data["reference_price"] = pd.to_numeric(data["reference_price"], errors="coerce")
    data["predicted"] = pd.to_numeric(data["predicted"], errors="coerce")
    data = data.dropna(subset=["origin_date", "step", "reference_price", "predicted"])
    data = data[(data["step"] >= 1) & (data["step"] <= decision_horizon_days)]
    if data.empty:
        return pd.DataFrame()

    daily = (data.groupby("origin_date", as_index=False)
             .agg(reference_price=("reference_price", "first"),
                  forecast_mean=("predicted", "mean"))
             .sort_values("origin_date").reset_index(drop=True))
    records = []
    cycle_number = 0
    start = 0
    while start + cycle_days <= len(daily):
        block = daily.iloc[start:start + cycle_days].reset_index(drop=True)
        dates = block["origin_date"]
        if not dates.diff().dropna().eq(pd.Timedelta(days=1)).all():
            start += cycle_days
            continue

        cycle_number += 1
        delay = 0
        for offset in range(min(max_wait_days, cycle_days - 1) + 1):
            current = block.iloc[offset]
            advice = make_recommendation(
                current["reference_price"], [current["forecast_mean"]], threshold
            )["recommendation"]
            delay = offset
            if advice != "Tunda dulu" or offset == min(max_wait_days, cycle_days - 1):
                break

        baseline_price = float(block.iloc[0]["reference_price"])
        policy_price = float(block.iloc[delay]["reference_price"])
        records.append({
            "cycle": cycle_number,
            "baseline_buy_date": block.iloc[0]["origin_date"].date().isoformat(),
            "policy_buy_date": block.iloc[delay]["origin_date"].date().isoformat(),
            "wait_days": delay,
            "baseline_unit_price_rp_per_kg": baseline_price,
            "policy_unit_price_rp_per_kg": policy_price,
            "quantity_kg": float(quantity_kg),
            "baseline_cost_rp": baseline_price * quantity_kg,
            "policy_cost_rp": policy_price * quantity_kg,
            "savings_rp": (baseline_price - policy_price) * quantity_kg,
            "advice_on_purchase_day": advice,
        })
        start += cycle_days

    return pd.DataFrame(records)
