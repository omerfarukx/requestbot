import sqlite3, os
db = sqlite3.connect(os.path.join("client", "backend", "requestbot.db"))
rows = db.execute("SELECT id, username, email, role, plan FROM users").fetchall()
print(f"Kullanıcı sayısı: {len(rows)}")
for r in rows:
    print(r)
