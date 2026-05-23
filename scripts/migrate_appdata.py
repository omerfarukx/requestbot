import sqlite3, os

db_path = os.path.join(os.environ["APPDATA"], "RequestBot", "requestbot.db")
db = sqlite3.connect(db_path)
try:
    db.execute("ALTER TABLE campaigns ADD COLUMN mode VARCHAR(20) DEFAULT 'http'")
    db.commit()
    print("mode kolonu eklendi")
except sqlite3.OperationalError as e:
    print(f"Zaten var: {e}")
db.close()
