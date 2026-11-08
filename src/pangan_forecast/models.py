from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from .features import add_features, PRICE_FEATURES, EXTERNAL_FEATURES


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


def _metrics(y_true, y_pred):
    actual, pred = y_true.reshape(-1), y_pred.reshape(-1)
    denominator = np.maximum(np.abs(actual), 1e-8)
    return {"MAE": float(mean_absolute_error(actual, pred)),
            "RMSE": float(np.sqrt(mean_squared_error(actual, pred))),
            "MAPE": float(np.mean(np.abs((actual - pred) / denominator)) * 100)}


def run_experiments(clean: pd.DataFrame, output_dir=".", window=30, horizon=7,
                    epochs=30, batch_size=32, data_source=None):
    """Fit four model variants and return metric and forecast tables."""
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
    for commodity, group in clean.groupby("commodity"):
        featured = add_features(group)
        if len(featured) < window + horizon + 20:
            print(f"Lewati {commodity}: data terlalu pendek ({len(featured)} baris setelah fitur).")
            continue
        cut = featured["date"].iloc[int(len(featured) * 0.8)]
        for kind in ("LSTM", "GRU"):
            for use_external in (False, True):
                external_cols = [col for col in EXTERNAL_FEATURES if col in featured.columns]
                cols = PRICE_FEATURES + (external_cols if use_external else [])
                data = featured.copy()
                for col in cols:
                    if col not in data.columns:
                        data[col] = np.nan
                # Fill only from known past weather; do not backfill from the
                # future when a measurement is missing at the start of a series.
                data[cols] = data[cols].apply(pd.to_numeric, errors="coerce")
                data[cols] = data[cols].ffill().fillna(0)
                x, y, starts, ends, references = build_sequences(data, cols, window, horizon)
                train_mask = pd.to_datetime(ends) < cut
                test_mask = pd.to_datetime(starts) >= cut
                if train_mask.sum() < 20 or test_mask.sum() < 1:
                    print(f"Lewati {commodity}/{kind}/external={use_external}: split tidak cukup.")
                    continue
                x_train, y_train = x[train_mask], y[train_mask]
                x_test, y_test = x[test_mask], y[test_mask]
                x_scaler, y_scaler = StandardScaler(), StandardScaler()
                x_scaler.fit(x_train.reshape(-1, len(cols)))
                y_scaler.fit(y_train.reshape(-1, 1))
                def sx(a):
                    return x_scaler.transform(a.reshape(-1, len(cols))).reshape(a.shape)
                train_x, test_x = sx(x_train), sx(x_test)
                train_y = y_scaler.transform(y_train.reshape(-1, 1)).reshape(y_train.shape)
                tf.keras.utils.set_random_seed(42)
                model = _build_keras(kind, window, len(cols), horizon)
                history = model.fit(train_x, train_y, epochs=epochs, batch_size=batch_size,
                                    validation_split=0.1, shuffle=False, verbose=0,
                                    callbacks=[tf.keras.callbacks.EarlyStopping(
                                        patience=5, restore_best_weights=True)])
                pred_scaled = model.predict(test_x, verbose=0)
                pred = y_scaler.inverse_transform(pred_scaled.reshape(-1, 1)).reshape(pred_scaled.shape)
                score = _metrics(y_test, pred)
                name = f"{str(commodity).strip().lower().replace(' ', '_')}_{kind.lower()}_{'external' if use_external else 'price'}"
                feature_label = "harga + cuaca + kalender + siklus tanggal" if use_external else "harga saja"
                score.update({"commodity": commodity, "model": kind,
                              "features": feature_label,
                              "data_source": data_source,
                              "train_target_end": str(pd.to_datetime(ends[train_mask]).max())[:10],
                              "test_target_start": str(pd.to_datetime(starts[test_mask]).min())[:10],
                              "test_target_end": str(pd.to_datetime(ends[test_mask]).max())[:10],
                              "window_days": window, "forecast_horizon_days": horizon,
                              "configured_epochs": epochs,
                              "epochs_trained": len(history.history.get("loss", [])),
                              "n_train_sequences": len(x_train), "n_test_sequences": len(x_test)})
                metrics.append(score)
                # HDF5 avoids incomplete .keras ZIP archives observed on this
                # native Windows + TensorFlow setup. Keep model and weights
                # together so forecast_next can load the artifact directly.
                model_path = out_dir / "models" / f"{name}.h5"
                model.save(model_path, include_optimizer=False)
                print(f"Tersimpan: {model_path.name}", flush=True)
                (out_dir / "models" / f"{name}.json").write_text(json.dumps({
                    "commodity": commodity, "kind": kind, "feature_cols": cols,
                    "window": window, "horizon": horizon,
                    "x_mean": x_scaler.mean_.tolist(), "x_scale": x_scaler.scale_.tolist(),
                    "y_mean": float(y_scaler.mean_[0]), "y_scale": float(y_scaler.scale_[0]),
                }, ensure_ascii=False, indent=2), encoding="utf-8")
                for j, (start, end, reference) in enumerate(zip(starts[test_mask], ends[test_mask], references[test_mask])):
                    for step, value in enumerate(pred[j], start=1):
                        forecasts.append({"commodity": commodity, "model": kind,
                                          "features": feature_label,
                                          "data_source": data_source,
                                          "origin_date": str(pd.Timestamp(start) - pd.Timedelta(days=1))[:10],
                                          "target_date": str(pd.Timestamp(start) + pd.Timedelta(days=step-1))[:10],
                                          "step": step, "reference_price": float(reference),
                                          "actual": float(y_test[j, step-1]),
                                          "predicted": float(value)})
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
    forecast_df.to_csv(out_dir / "reports" / "forecasts.csv", index=False)
    return metrics_df, forecast_df


def forecast_next(model_path, metadata_path, history: pd.DataFrame):
    """Generate a next-horizon forecast from a saved model and recent feature rows."""
    from tensorflow import keras
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
    scaled = keras.models.load_model(model_path, compile=False).predict(x[None, ...], verbose=0)[0]
    return scaled * meta["y_scale"] + meta["y_mean"]
