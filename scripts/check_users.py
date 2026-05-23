import sqlite3
db = sqlite3.connect("/opt/requestbot/server/backend/server.db")
rows = db.execute("SELECT id, username, role, plan, is_active FROM users ORDER BY id").fetchall()
print(f"Toplam: {len(rows)}")
for r in rows:
    print(r)
