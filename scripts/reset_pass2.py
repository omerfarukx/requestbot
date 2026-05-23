import sqlite3, os, bcrypt

new_pass = b"admin123"
hashed = bcrypt.hashpw(new_pass, bcrypt.gensalt()).decode()

db = sqlite3.connect(os.path.join("client", "backend", "requestbot.db"))
db.execute("UPDATE users SET password_hash=? WHERE username='omerfaruk'", (hashed,))
db.commit()
db.close()
print(f"Sifre 'admin123' olarak sifirlandi: {hashed[:20]}...")
