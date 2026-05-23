import sqlite3, os, bcrypt

db_path = os.path.join(os.environ["APPDATA"], "RequestBot", "requestbot.db")
print(f"DB: {db_path}")

new_pass = b"admin123"
hashed = bcrypt.hashpw(new_pass, bcrypt.gensalt()).decode()

db = sqlite3.connect(db_path)
rows = db.execute("SELECT id, username FROM users").fetchall()
print(f"Kullanicilar: {rows}")

db.execute("UPDATE users SET password_hash=? WHERE username='omerfaruk'", (hashed,))
db.commit()
db.close()
print("Sifre 'admin123' olarak sifirlandi")
