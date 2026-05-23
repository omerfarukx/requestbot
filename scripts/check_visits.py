import sqlite3, os

db = sqlite3.connect(os.path.join(os.environ["APPDATA"], "RequestBot", "requestbot.db"))

print("=== Campaign #3 mode ===")
row = db.execute("SELECT mode, status, total_visits, failed_visits FROM campaigns WHERE id=3").fetchone()
print(row)

print("\n=== Son 10 visit (campaign #3) ===")
rows = db.execute("""
    SELECT id, duration_seconds, status, error_message, ended_at
    FROM visits WHERE campaign_id=3 ORDER BY id DESC LIMIT 10
""").fetchall()
for r in rows:
    print(r)

print("\n=== Son 10 log (campaign #3) ===")
rows = db.execute("""
    SELECT level, message, created_at FROM logs
    WHERE campaign_id=3 ORDER BY id DESC LIMIT 10
""").fetchall()
for r in rows:
    print(f"[{r[0]}] {r[2]} | {r[1]}")

db.close()
