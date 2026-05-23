"""Bot engine test — kampanya baslat, 30sn izle, durdur"""
import urllib.request, urllib.error, json, time, sys

PASS = "\033[92m[OK]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
INFO = "\033[94m[..]\033[0m"

def get(url, token):
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(url, headers={"Authorization": "Bearer " + token}), timeout=6)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: body = json.loads(e.read())
        except: body = {}
        return e.code, body
    except Exception as e:
        return 0, {"error": str(e)}

def post(url, data, token):
    h = {"Content-Type": "application/json", "Authorization": "Bearer " + token}
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(url, json.dumps(data).encode(), h, method="POST"), timeout=6)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: body = json.loads(e.read())
        except: body = {}
        return e.code, body
    except Exception as e:
        return 0, {"error": str(e)}

# --- Auth ---
import sys as _sys; _sys.path.insert(0, r"c:\RequestHitBotu\client")
from license_client import get_machine_id

s, d = post("http://localhost:8001/api/auth/login",
            {"username": "testuser1778676422", "password": "admin123"}, "")
srv_token = d.get("access_token", "")

s, d = post("http://localhost:8000/api/auth/sso",
            {"license_token": srv_token,
             "user": {"username": "testuser1778676422", "email": "test@test.com",
                      "plan": "agency", "role": "admin"}}, "")
tok = d.get("access_token", "")
if not tok:
    print(FAIL + " Token alinamadi"); sys.exit(1)

# --- Kampanya detay ---
print("\n========== KAMPANYA ==========")
s, camps = get("http://localhost:8000/api/campaigns", tok)
if not camps or not isinstance(camps, list):
    print(FAIL + " Kampanya yok"); sys.exit(1)

c = camps[0]
cid = c["id"]
print(f"  ID     : {cid}")
print(f"  Hedef  : {c.get('target_url')}")
print(f"  Anahtar: {c.get('keywords')}")
print(f"  Durum  : {c.get('status')}")
print(f"  Ziyaret: {c.get('daily_visits')}/gun")

# --- Proxy durumu ---
print("\n========== PROXY ==========")
s, proxies = get("http://localhost:8000/api/proxies", tok)
active = [p for p in proxies if p.get("is_active")]
print(f"  Toplam : {len(proxies)}  Aktif: {len(active)}")
if active:
    print(f"  Ornek  : {active[0].get('address')}")

# --- Stats oncesi ---
s, before = get("http://localhost:8000/api/stats", tok)
print(f"\nBaşlamadan önce: {before.get('total_visits')} ziyaret, {before.get('successful_visits')} basarili")

# --- Kampanyayı başlat ---
print(f"\n{INFO} Kampanya baslatiliyor (ID={cid})...")
s, d = post(f"http://localhost:8000/api/campaigns/{cid}/start", {}, tok)
print(f"  Start yaniti: HTTP {s} — {d.get('message', d.get('detail', d))}")

if s not in (200, 201):
    print(FAIL + " Kampanya baslatılamadı — bot engine hatası olabilir")
    sys.exit(1)

# --- 20 saniye izle ---
print(f"\n{INFO} 20 saniye bekleniyor, bot çalışıyor mu izleniyor...")
for i in range(4):
    time.sleep(5)
    s, stats = get("http://localhost:8000/api/stats", tok)
    s2, logs = get("http://localhost:8000/api/logs?limit=3", tok)
    log_lines = logs if isinstance(logs, list) else []
    last_log = log_lines[-1].get("message", "") if log_lines else "—"
    print(f"  [{(i+1)*5}s] ziyaret={stats.get('total_visits')} basarili={stats.get('successful_visits')}  | son log: {last_log[:70]}")

# --- Kampanyayı durdur ---
print(f"\n{INFO} Kampanya durduruluyor...")
s, d = post(f"http://localhost:8000/api/campaigns/{cid}/stop", {}, tok)
print(f"  Stop yaniti: HTTP {s} — {d.get('message', d.get('detail', d))}")

# --- Karşılaştır ---
s, after = get("http://localhost:8000/api/stats", tok)
new_visits = after.get("total_visits", 0) - before.get("total_visits", 0)
new_success = after.get("successful_visits", 0) - before.get("successful_visits", 0)

print(f"\n========== SONUÇ ==========")
if new_visits > 0:
    print(f"  \033[92m[OK]\033[0m  Bot calisti! {new_visits} yeni ziyaret, {new_success} basarili")
else:
    print(f"  \033[91m[WARN]\033[0m  20 saniyede yeni ziyaret olusmadı (proxy sorunu veya bekliyor olabilir)")
    print("  Son loglar:")
    s2, logs = get("http://localhost:8000/api/logs?limit=5", tok)
    for l in (logs if isinstance(logs, list) else [])[-5:]:
        print(f"    {l.get('timestamp','')} {l.get('level','').upper()}: {l.get('message','')[:80]}")
