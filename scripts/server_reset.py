import sqlite3, bcrypt

db = sqlite3.connect("/opt/requestbot/server/backend/server.db")
rows = db.execute("SELECT id, username FROM users").fetchall()
print("Kullanicilar:", rows)

new_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
db.execute("UPDATE users SET password_hash=? WHERE username='omerfaruk'", (new_hash,))
db.commit()
db.close()
print("Sifre 'admin123' olarak sifirlandi")
