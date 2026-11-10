import pandas as pd

PRICE_FEATURES = ["price", "lag_1", "lag_7", "mean_7", "mean_30"]
# Daily weather, holiday flags and calendar cycles.
EXTERNAL_FEATURES = ["temp_c", "temp_max_c", "temp_min_c", "rain_mm",
                     "wind_max_kmh", "solar_mj_m2",
                     "is_libur_nasional", "is_cuti_bersama", "is_weekend",
                     "is_ramadan", "is_near_eid", "is_idul_fitri",
                     "dow_sin", "dow_cos", "month_sin", "month_cos"]


def add_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.sort_values("date").copy()
    out["lag_1"] = out["price"].shift(1)
    out["lag_7"] = out["price"].shift(7)
    out["mean_7"] = out["price"].shift(1).rolling(7, min_periods=7).mean()
    out["mean_30"] = out["price"].shift(1).rolling(30, min_periods=30).mean()
    dow = out["date"].dt.dayofweek
    month = out["date"].dt.month
    out["dow_sin"] = __import__("numpy").sin(2 * __import__("numpy").pi * dow / 7)
    out["dow_cos"] = __import__("numpy").cos(2 * __import__("numpy").pi * dow / 7)
    out["month_sin"] = __import__("numpy").sin(2 * __import__("numpy").pi * month / 12)
    out["month_cos"] = __import__("numpy").cos(2 * __import__("numpy").pi * month / 12)
    return out.dropna(subset=PRICE_FEATURES).reset_index(drop=True)
