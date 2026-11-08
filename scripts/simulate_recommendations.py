from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pangan_forecast.recommend import simulate_purchase_policy

forecast_path = ROOT / "reports/forecasts.csv"
if not forecast_path.exists():
    raise SystemExit("Hasil prediksi belum ada. Jalankan scripts/train.py terlebih dahulu.")

forecasts = pd.read_csv(forecast_path, parse_dates=["origin_date", "target_date"])
keys = ["commodity", "model", "features", "data_source"]
details, summaries = [], []
for identity, group in forecasts.groupby(keys, dropna=False):
    result = simulate_purchase_policy(group, quantity_kg=1.0,
                                     threshold=0.05, max_wait_days=2)
    if result.empty:
        continue
    for key, value in zip(keys, identity):
        result[key] = value
    details.append(result)
    baseline = float(result["baseline_cost_rp"].sum())
    strategy = float(result["policy_cost_rp"].sum())
    summaries.append({
        **dict(zip(keys, identity)),
        "cycles": len(result),
        "deferred_cycles": int((result["wait_days"] > 0).sum()),
        "total_wait_days": int(result["wait_days"].sum()),
        "baseline_cost_1kg_rp": baseline,
        "strategy_cost_1kg_rp": strategy,
        "savings_1kg_rp": baseline - strategy,
        "savings_pct": (baseline - strategy) / baseline * 100 if baseline else 0.0,
    })

report_dir = ROOT / "reports"
pd.concat(details, ignore_index=True).to_csv(report_dir / "purchase_simulation_detail.csv", index=False)
pd.DataFrame(summaries).to_csv(report_dir / "purchase_simulation_summary.csv", index=False)
print(f"Siklus simulasi: {sum(item['cycles'] for item in summaries)}; harga Rp/kg; volume asumsi 1 kg/transaksi")
print(pd.DataFrame(summaries).groupby(["model", "features"], as_index=False)
      .agg(komoditas=("commodity", "nunique"), median_savings_pct=("savings_pct", "median"),
           mean_savings_pct=("savings_pct", "mean"))
      .round(2).to_string(index=False))
