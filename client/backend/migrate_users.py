"""Users tablosu + campaigns/proxies için user_id sütunları."""
import os
import sqlite3

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requestbot.db")
print(f"DB: {DB}")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# users tablosu
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    plan VARCHAR(20) DEFAULT 'free',
    is_active BOOLEAN DEFAULT 1,
    license_expires_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
print("✅ users tablosu hazır")

# campaigns.user_id
try:
    cur.execute("ALTER TABLE campaigns ADD COLUMN user_id INTEGER REFERENCES users(id)")
    print("✅ campaigns.user_id eklendi")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e).lower():
        print("ℹ️  campaigns.user_id zaten var")
    else:
        raise

# proxies.user_id
try:
    cur.execute("ALTER TABLE proxies ADD COLUMN user_id INTEGER REFERENCES users(id)")
    print("✅ proxies.user_id eklendi")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e).lower():
        print("ℹ️  proxies.user_id zaten var")
    else:
        raise

conn.commit()
conn.close()
print("\n🎉 Migration tamamlandı")
print("\nİlk kayıt olan kullanıcı otomatik admin olacak.")
print("Frontend'de /register sayfasından bir hesap oluşturun.")
