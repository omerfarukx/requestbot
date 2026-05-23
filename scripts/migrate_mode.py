import sqlite3, os

db_path = os.path.join(os.path.dirname(__file__), "client", "backend", "requestbot.db")
db = sqlite3.connect(db_path)
try:
    db.execute("ALTER TABLE campaigns ADD COLUMN mode VARCHAR(20) DEFAULT 'http'")
    db.commit()
    print("Migration OK — mode kolonu eklendi")
except sqlite3.OperationalError as e:
    print(f"Zaten var veya hata: {e}")
db.close()
