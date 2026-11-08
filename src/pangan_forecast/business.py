"""Per-user menu profit and sales records for the thesis prototype."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


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
                break_even_portions INTEGER,
                reference_date TEXT NOT NULL,
                model_name TEXT NOT NULL,
                feature_name TEXT NOT NULL,
                recipe_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        cursor = connection.execute(
            """INSERT INTO menu_profit_records (
                email, menu_name, period_label, portions_sold, selling_price, revenue,
                ingredient_cost_per_portion, total_ingredient_cost, other_cost_per_portion,
                fixed_cost, gross_profit, net_profit, predicted_ingredient_cost_per_portion,
                predicted_net_profit, net_margin_pct, break_even_portions, reference_date,
                model_name, feature_name, recipe_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                normalized_email,
                record["menu_name"], record["period_label"], int(record["portions_sold"]),
                float(record["selling_price"]), float(record["revenue"]),
                float(record["ingredient_cost_per_portion"]), float(record["total_ingredient_cost"]),
                float(record["other_cost_per_portion"]), float(record["fixed_cost"]),
                float(record["gross_profit"]), float(record["net_profit"]),
                float(record["predicted_ingredient_cost_per_portion"]),
                float(record["predicted_net_profit"]), float(record["net_margin_pct"]),
                record["break_even_portions"], record["reference_date"], record["model_name"],
                record["feature_name"], json.dumps(record["recipe"], ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        return int(cursor.lastrowid)


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
                      predicted_ingredient_cost_per_portion, predicted_net_profit,
                      net_margin_pct, break_even_portions, reference_date,
                      model_name, feature_name, recipe_json, created_at
               FROM menu_profit_records WHERE email = ? COLLATE NOCASE
               ORDER BY created_at DESC, id DESC LIMIT ?""",
            (normalized_email, max(1, min(int(limit), 500))),
        ).fetchall()
    return [dict(row) for row in rows]
