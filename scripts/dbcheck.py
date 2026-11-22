import sqlite3, sys
con = sqlite3.connect(sys.argv[1])
for t in ("accounts", "subscriptions", "payments", "menu_profit_records"):
    try:
        cols = [r[1] for r in con.execute(f"PRAGMA table_info({t})")]
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(t, "rows=", n, "cols=", cols)
        for row in con.execute(f"SELECT * FROM {t} LIMIT 3"):
            print("   ", row)
    except Exception as e:
        print(t, "ERR", e)
