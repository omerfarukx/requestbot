import sqlite3, os
db_path = os.path.join(os.path.dirname(__file__), "requestbot.db")
db = sqlite3.connect(db_path)
cur = db.cursor()
new_cols = [
    ("hourly_limit", "INTEGER"),
    ("active_hours_start", "INTEGER DEFAULT 0"),
    ("active_hours_end", "INTEGER DEFAULT 24"),
    ("bounce_rate_pct", "INTEGER DEFAULT 30"),
    ("referrer_mix", "TEXT DEFAULT 'google:70,direct:20,social:10'"),
    ("mobile_ratio_pct", "INTEGER DEFAULT 65"),
]
for col, typ in new_cols:
    try:
        cur.execute(f"ALTER TABLE campaigns ADD COLUMN {col} {typ}")
        print(f"  + {col}")
    except sqlite3.OperationalError as e:
        print(f"  - {col}: {e}")
db.commit()
db.close()
print("Migration OK")
