import sqlite3, os
db = sqlite3.connect(os.path.join(os.environ["APPDATA"], "RequestBot", "requestbot.db"))
rows = db.execute("SELECT level, message, created_at FROM logs WHERE campaign_id=3 ORDER BY id DESC LIMIT 15").fetchall()
for r in rows:
    print(f"[{r[0]}] {r[2]} | {r[1]}")
