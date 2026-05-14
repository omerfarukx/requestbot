import sqlite3, os
db = sqlite3.connect(os.path.join(os.path.dirname(__file__), "app.db"))
cur = db.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tablolar:", [t[0] for t in cur.fetchall()])
db.close()
