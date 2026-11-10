"""Per-user menu profit and sales records for the thesis prototype."""

from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def _connect(database: str | Path) -> sqlite3.Connection:
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def save_profit_record(database: str | Path, email: str, record: dict) -> int:
    """Persist one submitted sales period and its recipe cost assumptions."""
    normalized_email = email.strip().casefold()
    if not normalized_email:
        raise ValueError("Akun pengguna tidak ditemukan.")
    with _connect(database) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS menu_profit_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL COLLATE NOCASE,
                menu_name TEXT NOT NULL,
                period_label TEXT NOT NULL,
                portions_sold INTEGER NOT NULL,
                selling_price REAL NOT NULL,
                revenue REAL NOT NULL,
                ingredient_cost_per_portion REAL NOT NULL,
                total_ingredient_cost REAL NOT NULL,
                other_cost_per_portion REAL NOT NULL,
                fixed_cost REAL NOT NULL,
                gross_profit REAL NOT NULL,
                net_profit REAL NOT NULL,
                predicted_ingredient_cost_per_portion REAL NOT NULL,
                predicted_net_profit REAL NOT NULL,
                net_margin_pct REAL NOT NULL,
                forecast_available INTEGER NOT NULL DEFAULT 1,
                break_even_portions INTEGER,
                reference_date TEXT NOT NULL,
                model_name TEXT NOT NULL,
                feature_name TEXT NOT NULL,
                recipe_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        columns = {row[1] for row in connection.execute("PRAGMA table_info(menu_profit_records)")}
        if "forecast_available" not in columns:
            connection.execute(
                "ALTER TABLE menu_profit_records ADD COLUMN forecast_available INTEGER NOT NULL DEFAULT 1"
            )
        cursor = connection.execute(
            """INSERT INTO menu_profit_records (
                email, menu_name, period_label, portions_sold, selling_price, revenue,
                ingredient_cost_per_portion, total_ingredient_cost, other_cost_per_portion,
                fixed_cost, gross_profit, net_profit, predicted_ingredient_cost_per_portion,
                predicted_net_profit, net_margin_pct, forecast_available, break_even_portions, reference_date,
                model_name, feature_name, recipe_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                normalized_email,
                record["menu_name"], record["period_label"], int(record["portions_sold"]),
                float(record["selling_price"]), float(record["revenue"]),
                float(record["ingredient_cost_per_portion"]), float(record["total_ingredient_cost"]),
                float(record["other_cost_per_portion"]), float(record["fixed_cost"]),
                float(record["gross_profit"]), float(record["net_profit"]),
                float(record["predicted_ingredient_cost_per_portion"]),
                float(record["predicted_net_profit"]), float(record["net_margin_pct"]),
                int(bool(record.get("forecast_available", True))),
                record["break_even_portions"], record["reference_date"], record["model_name"],
                record["feature_name"], json.dumps(record["recipe"], ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        return int(cursor.lastrowid)


def compute_current_profit_report(
    recipe_rows,
    quotes: dict,
    *,
    menu_name: str,
    model_name: str,
    feature_name: str,
    selling_price: float,
    portions_sold: int,
    other_cost_per_portion: float,
    fixed_cost: float,
    sales_period: str,
) -> tuple[dict, list[str]]:
    """Calculate menu costs using latest PIHPS quotes and only fresh forecasts."""
    current_cost = 0.0
    predicted_cost = 0.0
    missing: list[str] = []
    forecast_available = True
    ingredient_details: list[dict] = []

    for _, ingredient in recipe_rows.iterrows():
        name = str(ingredient["commodity"]).strip()
        grams = float(ingredient["grams_per_portion"])
        actual = ingredient["actual_price_rp_per_kg"]
        quote = quotes.get(name, {})
        supplied_price = float(actual) if pd.notna(actual) and float(actual) > 0 else None
        reference = supplied_price or quote.get("current_price")
        if reference is None or float(reference) <= 0:
            missing.append(name)
            forecast_available = False
            continue

        is_fresh = bool(
            quote.get("status") == "ready"
            and quote.get("forecast_mean") is not None
            and not quote.get("stale")
        )
        predicted_price = float(quote["forecast_mean"]) if is_fresh else None
        forecast_available = forecast_available and is_fresh
        current_cost += grams / 1000 * float(reference)
        predicted_cost += grams / 1000 * (predicted_price if predicted_price is not None else float(reference))
        ingredient_details.append({
            "bahan": name,
            "takaran_gram_per_porsi": grams,
            "harga_acuan_rp_per_kg": float(reference),
            "harga_prediksi_rp_per_kg": predicted_price,
            "tanggal_harga_acuan": quote.get("price_date") if not supplied_price else "Harga pemasok yang dimasukkan",
            "forecast_available": is_fresh,
        })

    if missing:
        return {}, sorted(set(missing))

    revenue = float(selling_price * portions_sold)
    other_variable_cost = float(other_cost_per_portion * portions_sold)
    gross_profit = revenue - current_cost * portions_sold
    net_profit = gross_profit - other_variable_cost - fixed_cost
    predicted_net_profit = (
        revenue - predicted_cost * portions_sold - other_variable_cost - fixed_cost
        if forecast_available else net_profit
    )
    contribution = selling_price - current_cost - other_cost_per_portion
    break_even = (math.ceil(fixed_cost / contribution) if fixed_cost else 0) if contribution > 0 else None
    dates = [x.get("tanggal_harga_acuan") for x in ingredient_details
             if x.get("tanggal_harga_acuan") and x.get("tanggal_harga_acuan") != "Harga pemasok yang dimasukkan"]
    report = {
        "menu_name": menu_name.strip(),
        "period_label": sales_period,
        "portions_sold": int(portions_sold),
        "selling_price": float(selling_price),
        "revenue": revenue,
        "ingredient_cost_per_portion": current_cost,
        "total_ingredient_cost": current_cost * portions_sold,
        "other_cost_per_portion": float(other_cost_per_portion),
        "fixed_cost": float(fixed_cost),
        "gross_profit": gross_profit,
        "net_profit": net_profit,
        "predicted_ingredient_cost_per_portion": predicted_cost,
        "predicted_net_profit": predicted_net_profit,
        "net_margin_pct": net_profit / revenue * 100 if revenue else 0.0,
        "forecast_available": forecast_available,
        "break_even_portions": int(break_even) if break_even is not None else None,
        "reference_date": max(dates) if dates else "Harga pemasok yang dimasukkan",
        "model_name": model_name,
        "feature_name": feature_name,
        "recipe": ingredient_details,
    }
    return report, []


def get_profit_history(database: str | Path, email: str, limit: int = 100) -> list[dict]:
    """Return the newest saved reports belonging to the signed-in user."""
    normalized_email = email.strip().casefold()
    if not normalized_email:
        return []
    with _connect(database) as connection:
        table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='menu_profit_records'"
        ).fetchone()
        if table is None:
            return []
        rows = connection.execute(
            """SELECT id, menu_name, period_label, portions_sold, selling_price,
                      revenue, ingredient_cost_per_portion, total_ingredient_cost,
                      other_cost_per_portion, fixed_cost, gross_profit, net_profit,
                      predicted_ingredient_cost_per_portion, predicted_net_profit, forecast_available,
                      net_margin_pct, break_even_portions, reference_date,
                      model_name, feature_name, recipe_json, created_at
               FROM menu_profit_records WHERE email = ? COLLATE NOCASE
               ORDER BY created_at DESC, id DESC LIMIT ?""",
            (normalized_email, max(1, min(int(limit), 500))),
        ).fetchall()
    return [dict(row) for row in rows]
