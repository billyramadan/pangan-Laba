from pathlib import Path
import json
import shutil
import tempfile
from functools import lru_cache
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
try:
    from .features import add_features, PRICE_FEATURES, EXTERNAL_FEATURES
except ImportError:  # allow direct execution: python models.py
    import pathlib
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    from features import add_features, PRICE_FEATURES, EXTERNAL_FEATURES


def build_sequences(frame, feature_cols, window=30, horizon=7):
    x, y, starts, ends, references = [], [], [], [], []
    values = frame[feature_cols].to_numpy(dtype=float)
    target = frame["price"].to_numpy(dtype=float)
    dates = frame["date"].to_numpy()
    for end in range(window - 1, len(frame) - horizon):
        x.append(values[end - window + 1:end + 1])
        y.append(target[end + 1:end + 1 + horizon])
        starts.append(dates[end + 1])
        ends.append(dates[end + horizon])
        references.append(target[end])
    return np.asarray(x), np.asarray(y), np.asarray(starts), np.asarray(ends), np.asarray(references)


def _build_keras(kind, window, n_features, horizon):
    from tensorflow import keras
    layer = keras.layers.LSTM if kind == "LSTM" else keras.layers.GRU
    model = keras.Sequential([
        keras.layers.Input(shape=(window, n_features)),
        layer(48), keras.layers.Dropout(0.15),
        keras.layers.Dense(32, activation="relu"),
        keras.layers.Dense(horizon),
    ])
    model.compile(optimizer="adam", loss="mse")
    return model


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, object]:
    actual, pred = y_true.reshape(-1), y_pred.reshape(-1)
    denominator = np.maximum(np.abs(actual), 1e-8)
    return {"MAE": float(mean_absolute_error(actual, pred)),
            "RMSE": float(np.sqrt(mean_squared_error(actual, pred))),
            "MAPE": float(np.mean(np.abs((actual - pred) / denominator)) * 100)}


def run_experiments(clean: pd.DataFrame, output_dir=".", window=30, horizon=7,
                    epochs=30, batch_size=32, data_source=None):
    """Fit model variants per feature set and seed, return metric and forecast tables."""
    try:
        import tensorflow as tf
    except ImportError as exc:
        raise RuntimeError("TensorFlow belum terpasang. Pasang paket dari requirements.txt.") from exc
    out_dir = Path(output_dir)
    (out_dir / "models").mkdir(parents=True, exist_ok=True)
    (out_dir / "reports").mkdir(parents=True, exist_ok=True)
    metrics, forecasts = [], []
    if data_source is None:
        is_demo = ("location" in clean.columns and clean["location"].astype(str)
                   .str.contains("DEMO", case=False, na=False).any())
        data_source = "synthetic_demo" if is_demo else "local_data"

    WEATHER_FEATURES = ["temp_c", "temp_max_c", "temp_min_c", "rain_mm",
                        "wind_max_kmh", "solar_mj_m2"]
    CALENDAR_FEATURES = ["is_libur_nasional", "is_cuti_bersama", "is_weekend",
                         "is_ramadan", "is_near_eid", "is_idul_fitri"]
    CYCLE_FEATURES = ["dow_sin", "dow_cos", "month_sin", "month_cos"]
    FEATURE_LABEL = {
        "harga_saja": "harga saja",
        "harga+cuaca": "harga + cuaca",
        "harga+cuaca+bmkg": "harga + cuaca + bmkg",
        "harga+kalender": "harga + kalender",
        "harga+siklus": "harga + siklus tanggal",
        "harga+semua_eksternal": "harga + cuaca + kalender + siklus tanggal",
    }

    for commodity, group in clean.groupby("commodity"):
        featured = add_features(group)
        if len(featured) < window + horizon + 20:
            print(f"Lewati {commodity}: data terlalu pendek ({len(featured)} baris setelah fitur).")
            continue
        dates = featured["date"].to_numpy()
        cut = pd.to_datetime(featured["date"].iloc[int(len(featured) * 0.8)])

        weather_cols = [c for c in WEATHER_FEATURES if c in featured.columns]
        bmkg_cols = [c for c in featured.columns if c.startswith("bmkg_")]
        cal_cols = [c for c in CALENDAR_FEATURES if c in featured.columns]
        cycle_cols = [c for c in CYCLE_FEATURES if c in featured.columns]
        all_ext_cols = [c for c in EXTERNAL_FEATURES if c in featured.columns]

        variant_sets = [
            ("harga_saja", []),
            ("harga+cuaca", weather_cols),
            ("harga+cuaca+bmkg", weather_cols + bmkg_cols),
            ("harga+kalender", cal_cols),
            ("harga+siklus", cycle_cols),
            ("harga+semua_eksternal", all_ext_cols),
        ]
        seeds = (42, 123, 2026)

        for kind in ("LSTM", "GRU"):
            for seed in seeds:
                tf.keras.utils.set_random_seed(seed)
                for label, ext_cols in variant_sets:
                    cols = PRICE_FEATURES + ext_cols
                    data = featured.copy()
                    for col in cols:
                        if col not in data.columns:
                            data[col] = np.nan
                    data[cols] = data[cols].apply(pd.to_numeric, errors="coerce")
                    data[cols] = data[cols].ffill().fillna(0)
                    x, y, starts, ends, references = build_sequences(data, cols, window, horizon)
                    train_mask = pd.to_datetime(ends) < cut
                    test_mask = ~train_mask
                    if train_mask.sum() < 20 or test_mask.sum() < 1:
                        print(f"Lewati {commodity}/{kind}/seed={seed}/{label}: split tidak cukup.")
                        continue
                    x_train, y_train = x[train_mask], y[train_mask]
                    x_test, y_test = x[test_mask], y[test_mask]
                    x_scaler, y_scaler = StandardScaler(), StandardScaler()
                    x_scaler.fit(x_train.reshape(-1, len(cols)))
                    y_scaler.fit(y_train.reshape(-1, 1))
                    assert x_scaler.mean_ is not None and x_scaler.scale_ is not None
                    assert y_scaler.mean_ is not None and y_scaler.scale_ is not None

                    def sx(a):
                        return x_scaler.transform(a.reshape(-1, len(cols))).reshape(a.shape)

                    train_x, test_x = sx(x_train), sx(x_test)
                    train_y = y_scaler.transform(y_train.reshape(-1, 1)).reshape(y_train.shape)
                    model = _build_keras(kind, window, len(cols), horizon)
                    history = model.fit(train_x, train_y, epochs=epochs, batch_size=batch_size,
                                        validation_split=0.1, shuffle=False, verbose=0,
                                        callbacks=[tf.keras.callbacks.EarlyStopping(
                                            patience=5, restore_best_weights=True)])
                    pred_scaled = model.predict(test_x, verbose=0)
                    pred = y_scaler.inverse_transform(pred_scaled.reshape(-1, 1)).reshape(pred_scaled.shape)
                    score: dict[str, object] = _metrics(y_test, pred)
                    name = f"{str(commodity).strip().lower().replace(' ', '_')}_{kind.lower()}_{label}_seed{seed}"
                    score.update({"commodity": commodity, "model": kind,
                                  "features": FEATURE_LABEL[label],
                                  "seed": seed,
                                  "data_source": data_source,
                                  "train_target_end": str(pd.to_datetime(ends[train_mask]).max())[:10],
                                  "test_target_start": str(pd.to_datetime(starts[test_mask]).min())[:10],
                                  "test_target_end": str(pd.to_datetime(ends[test_mask]).max())[:10],
                                  "window_days": window, "forecast_horizon_days": horizon,
                                  "configured_epochs": epochs,
                                  "epochs_trained": len(history.history.get("loss", [])),
                                  "n_train_sequences": len(x_train), "n_test_sequences": len(x_test)})
                    metrics.append(score)

                    model_path = out_dir / "models" / f"{name}.h5"
                    model.save(model_path, include_optimizer=False)
                    print(f"Tersimpan: {model_path.name}", flush=True)
                    (out_dir / "models" / f"{name}.json").write_text(json.dumps({
                        "commodity": commodity, "kind": kind, "feature_cols": cols,
                        "window": window, "horizon": horizon,
                        "x_mean": x_scaler.mean_.tolist(), "x_scale": x_scaler.scale_.tolist(),
                        "y_mean": float(y_scaler.mean_[0]), "y_scale": float(y_scaler.scale_[0]),
                        "seed": seed,
                    }, ensure_ascii=False, indent=2), encoding="utf-8")
                    for j, (start, end, reference) in enumerate(zip(starts[test_mask], ends[test_mask], references[test_mask])):
                        for step, value in enumerate(pred[j], start=1):
                            forecasts.append({"commodity": commodity, "model": kind,
                                              "features": FEATURE_LABEL[label],
                                              "data_source": data_source,
                                              "seed": seed,
                                              "origin_date": str(pd.Timestamp(start) - pd.Timedelta(days=1))[:10],
                                              "target_date": str(pd.Timestamp(start) + pd.Timedelta(days=step-1))[:10],
                                              "step": step, "reference_price": float(reference),
                                              "actual": float(y_test[j, step-1]),
                                              "predicted": float(value)})

                    # baseline naif dan SMA-7 pada split uji yang sama
                    starts_np = np.asarray(starts)
                    end_idx = np.searchsorted(dates, starts_np[test_mask]) - 1
                    end_idx = np.clip(end_idx, 0, len(featured) - 1)
                    ref_test = references[test_mask]
                    mean7_at_end = featured["mean_7"].iloc[end_idx].to_numpy(dtype=float)

                    for baseline_name, baseline_origin in [("Naive", ref_test), ("SMA_7", mean7_at_end)]:
                        pred_base = np.tile(baseline_origin.reshape(-1, 1), (1, horizon))
                        score_base = _metrics(y_test, pred_base)
                        score_base.update({
                            "commodity": commodity, "model": baseline_name,
                            "features": FEATURE_LABEL[label],
                            "seed": seed,
                            "data_source": data_source,
                            "train_target_end": str(pd.to_datetime(ends[train_mask]).max())[:10],
                            "test_target_start": str(pd.to_datetime(starts[test_mask]).min())[:10],
                            "test_target_end": str(pd.to_datetime(ends[test_mask]).max())[:10],
                            "window_days": window, "forecast_horizon_days": horizon,
                            "configured_epochs": epochs,
                            "epochs_trained": 0,
                            "n_train_sequences": len(x_train), "n_test_sequences": len(x_test)})
                        metrics.append(score_base)

    metrics_df, forecast_df = pd.DataFrame(metrics), pd.DataFrame(forecasts)
    metrics_df.to_csv(out_dir / "reports" / "model_comparison.csv", index=False)
    if not metrics_df.empty:
        summary_df = (metrics_df.groupby(["model", "features"], as_index=False)
                      .agg(jumlah_komoditas=("commodity", "nunique"),
                           median_MAE=("MAE", "median"),
                           median_RMSE=("RMSE", "median"),
                           median_MAPE=("MAPE", "median"),
                           mean_MAE=("MAE", "mean"),
                           mean_RMSE=("RMSE", "mean"),
                           mean_MAPE=("MAPE", "mean")))
    else:
        summary_df = pd.DataFrame(columns=["model", "features", "jumlah_komoditas",
                                           "median_MAE", "median_RMSE", "median_MAPE",
                                           "mean_MAE", "mean_RMSE", "mean_MAPE"])
    summary_df.to_csv(out_dir / "reports" / "model_comparison_summary.csv", index=False)
    # Simpan seed representatif saja + round agar laporan tetap < batas ukuran
    # file GitHub (100 MB). Prediksi eksperimen lain tidak dipakai produksi.
    deployable = forecast_df.copy()
    if "seed" in deployable.columns:
        deployable = deployable[deployable["seed"].astype(str).eq("42")]
    for col in ("reference_price", "actual", "predicted"):
        if col in deployable.columns:
            deployable[col] = pd.to_numeric(deployable[col], errors="coerce").round(2)
    deployable.to_csv(out_dir / "reports" / "forecasts.csv", index=False)
    return metrics_df, forecast_df


def refit_full_history_models(clean: pd.DataFrame, output_dir=".", window=30,
                              horizon=7, epochs=15, batch_size=128):
    """Fit deployable model artifacts on every eligible observed history.

    Keep this separate from ``run_experiments``: the latter's saved models are
    fitted only on the chronological training split for unbiased evaluation.
    This final refit overwrites model/scaler artifacts only; evaluation reports
    remain the held-out results from ``run_experiments``.
    """
    try:
        import tensorflow as tf
    except ImportError as exc:
        raise RuntimeError("TensorFlow belum terpasang. Pasang paket dari requirements.txt.") from exc

    out_dir = Path(output_dir)
    model_dir = out_dir / "models"
    report_dir = out_dir / "reports"
    model_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    manifest = []

    for commodity, group in clean.groupby("commodity"):
        featured = add_features(group)
        if len(featured) < window + horizon + 20:
            print(f"Lewati refit {commodity}: data terlalu pendek ({len(featured)} baris setelah fitur).")
            continue

        weather_cols = [c for c in ["temp_c", "temp_max_c", "temp_min_c", "rain_mm",
                                    "wind_max_kmh", "solar_mj_m2"] if c in featured.columns]
        bmkg_cols = [c for c in featured.columns if c.startswith("bmkg_")]
        external_cols = [col for col in EXTERNAL_FEATURES if col in featured.columns]
        refit_variants = [
            ("price", [], "harga saja"),
            ("external", external_cols, "harga + cuaca + kalender + siklus tanggal"),
            ("external_bmkg", weather_cols + bmkg_cols, "harga + cuaca + bmkg"),
        ]

        for kind in ("LSTM", "GRU"):
            for slug_ext, ext_cols, feature_label in refit_variants:
                cols = PRICE_FEATURES + ext_cols
                data = featured.copy()
                for col in cols:
                    if col not in data.columns:
                        data[col] = np.nan
                data[cols] = data[cols].apply(pd.to_numeric, errors="coerce")
                data[cols] = data[cols].ffill().fillna(0)
                x, y, starts, ends, _ = build_sequences(data, cols, window, horizon)
                if len(x) < 20:
                    print(f"Lewati refit {commodity}/{kind}/external={use_external}: urutan tidak cukup ({len(x)}).")
                    continue

                x_scaler, y_scaler = StandardScaler(), StandardScaler()
                x_scaler.fit(x.reshape(-1, len(cols)))
                y_scaler.fit(y.reshape(-1, 1))
                assert x_scaler.mean_ is not None and x_scaler.scale_ is not None
                assert y_scaler.mean_ is not None and y_scaler.scale_ is not None
                train_x = x_scaler.transform(x.reshape(-1, len(cols))).reshape(x.shape)
                train_y = y_scaler.transform(y.reshape(-1, 1)).reshape(y.shape)
                tf.keras.utils.set_random_seed(42)
                model = _build_keras(kind, window, len(cols), horizon)
                model.fit(train_x, train_y, epochs=epochs, batch_size=batch_size,
                          shuffle=False, verbose=0)

                slug = f"{str(commodity).strip().lower().replace(' ', '_')}_{kind.lower()}_{slug_ext}"
                model.save(model_dir / f"{slug}.h5", include_optimizer=False)
                (model_dir / f"{slug}.json").write_text(json.dumps({
                    "commodity": commodity, "kind": kind, "feature_cols": cols,
                    "window": window, "horizon": horizon,
                    "x_mean": x_scaler.mean_.tolist(), "x_scale": x_scaler.scale_.tolist(),
                    "y_mean": float(y_scaler.mean_[0]), "y_scale": float(y_scaler.scale_[0]),
                    "fit_scope": "all_available_history",
                    "training_start": str(pd.to_datetime(starts).min())[:10],
                    "training_end": str(pd.to_datetime(ends).max())[:10],
                    "training_sequences": int(len(x)), "epochs": int(epochs),
                }, ensure_ascii=False, indent=2), encoding="utf-8")
                manifest.append({"commodity": commodity, "model": kind,
                                 "features": feature_label,
                                 "training_start": str(pd.to_datetime(starts).min())[:10],
                                 "training_end": str(pd.to_datetime(ends).max())[:10],
                                 "training_sequences": int(len(x)), "epochs": int(epochs),
                                 "window_days": int(window), "forecast_horizon_days": int(horizon)})
                print(f"Refit penuh tersimpan: {slug}.h5", flush=True)

    manifest_df = pd.DataFrame(manifest)
    manifest_df.to_csv(report_dir / "final_models_manifest.csv", index=False)
    return manifest_df


@lru_cache(maxsize=64)
def _load_forecast_model(model_path: str, modified_ns: int):
    """Cache models and normalize newer Keras initializer config in H5 files."""
    from tensorflow import keras
    path = Path(model_path)
    if path.suffix.lower() != ".h5":
        return keras.models.load_model(path, compile=False)

    # Keras 3.13+ may serialize optional initializer axis fields that a
    # compatible runtime cannot deserialize. Normalize a temporary copy only.
    import h5py

    with tempfile.TemporaryDirectory(prefix="pangan_model_", dir=path.parent) as temp_dir:
        compatible_path = Path(temp_dir) / path.name
        shutil.copy2(path, compatible_path)
        with h5py.File(compatible_path, "r+") as model_file:
            raw_config = model_file.attrs.get("model_config")
            if raw_config is not None:
                if isinstance(raw_config, bytes):
                    raw_config = raw_config.decode("utf-8")
                config = json.loads(raw_config)

                def normalize(value):
                    if isinstance(value, dict):
                        value.pop("input_axes", None)
                        value.pop("output_axes", None)
                        for child in value.values():
                            normalize(child)
                    elif isinstance(value, list):
                        for child in value:
                            normalize(child)

                normalize(config)
                model_file.attrs["model_config"] = json.dumps(config, separators=(",", ":"))
        return keras.models.load_model(compatible_path, compile=False)


def forecast_next(model_path, metadata_path, history: pd.DataFrame):
    """Generate a next-horizon forecast from a saved model and recent feature rows."""
    meta = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
    featured = add_features(history)
    cols, window = meta["feature_cols"], meta["window"]
    for col in cols:
        if col not in featured.columns:
            featured[col] = np.nan
    featured[cols] = featured[cols].apply(pd.to_numeric, errors="coerce").ffill().bfill().fillna(0)
    recent = featured.tail(window)
    if len(recent) < window:
        raise ValueError(f"Perlu setidaknya {window + 30} hari data untuk membentuk fitur.")
    x = recent[cols].to_numpy(float)
    x = (x - np.array(meta["x_mean"])) / np.array(meta["x_scale"])
    model_path = Path(model_path)
    model = _load_forecast_model(str(model_path.resolve()), model_path.stat().st_mtime_ns)
    pred_out = model.predict(x[None, ...], verbose=0)
    assert pred_out is not None
    scaled = pred_out[0]
    return scaled * meta["y_scale"] + meta["y_mean"]


def _selfcheck() -> None:
    """Runnable sanity check for sequence building and metrics (no TensorFlow)."""
    np.random.seed(0)
    n = 130
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    frame = pd.DataFrame({
        "date": dates,
        "price": 100 + np.cumsum(np.random.randn(n) * 2),
        "temp_c": 27.0,
    })
    window, horizon = 30, 7
    x, y, starts, ends, references = build_sequences(frame, ["price", "temp_c"], window, horizon)
    expected = n - window - horizon + 1
    assert x.shape == (expected, window, 2), f"x shape {x.shape}"
    assert y.shape == (expected, horizon), f"y shape {y.shape}"
    assert len(starts) == len(ends) == len(references) == expected
    assert (pd.to_datetime(starts) < pd.to_datetime(ends)).all(), "start harus sebelum end"
    assert (references == frame["price"].iloc[window - 1:n - horizon]).all(), "reference salah"

    m = _metrics(np.arange(1.0, 6.0), np.arange(1.0, 6.0) + 0.5)
    assert set(m) == {"MAE", "RMSE", "MAPE"}
    mae, rmse = m["MAE"], m["RMSE"]
    assert isinstance(mae, float) and isinstance(rmse, float)
    assert abs(mae - 0.5) < 1e-9
    assert abs(rmse - 0.5) < 1e-9
    print("models.py self-check OK")


if __name__ == "__main__":
    _selfcheck()
