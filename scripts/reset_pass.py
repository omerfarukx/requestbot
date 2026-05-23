import sqlite3, os, sys
sys.path.insert(0, os.path.join("client", "backend"))
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
new_pass = "admin123"
hashed = pwd_ctx.hash(new_pass)

db = sqlite3.connect(os.path.join("client", "backend", "requestbot.db"))
db.execute("UPDATE users SET password_hash=? WHERE username='omerfaruk'", (hashed,))
db.commit()
db.close()
print(f"Şifre 'admin123' olarak sıfırlandı")
