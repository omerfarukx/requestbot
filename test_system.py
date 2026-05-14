"""Sistem entegrasyon testi — tum servisleri test eder"""
import urllib.request, urllib.error, json, uuid, sys

PASS = "\033[92m[OK]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
errors = []

def get(url, token=None, raw=False):
    h = {}
    if token: h['Authorization'] = 'Bearer ' + token
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=5)
        if raw: return r.status, {}
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: body = json.loads(e.read())
        except: body = {}
        return e.code, body
    except Exception as e:
        return 0, {"error": str(e)}

def post(url, data, token=None):
    h = {'Content-Type': 'application/json'}
    if token: h['Authorization'] = 'Bearer ' + token
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(url, json.dumps(data).encode(), h, method='POST'), timeout=5)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: body = json.loads(e.read())
        except: body = {}
        return e.code, body
    except Exception as e:
        return 0, {"error": str(e)}

def check(name, cond, detail=""):
    if cond:
        print(f"  {PASS}  {name}" + (f"  ({detail})" if detail else ""))
    else:
        print(f"  {FAIL}  {name}" + (f"  → {detail}" if detail else ""))
        errors.append(name)

import sys as _sys; _sys.path.insert(0, r'c:\RequestHitBotu\client')
try:
    from license_client import get_machine_id
    MACHINE_ID = get_machine_id()
except Exception:
    MACHINE_ID = str(uuid.uuid4())

print("\n========== 1. LICENSE SERVER (8001) ==========")

s, d = post('http://localhost:8001/api/auth/login',
            {'username': 'testuser1778676422', 'password': 'admin123'})
check("Login", s == 200 and 'access_token' in d, f"HTTP {s}")
srv_token = d.get('access_token', '')

s, d = post('http://localhost:8001/api/license/validate',
            {'machine_id': MACHINE_ID}, srv_token)
check("License validate", s == 200 and d.get('valid') == True, f"valid={d.get('valid')} plan={d.get('plan')}")

s, d = get('http://localhost:8001/api/auth/me', srv_token)
check("Auth /me", s == 200 and 'username' in d, f"user={d.get('username')}")

s, d = get('http://localhost:8001/api/download/info', srv_token)
check("Download info endpoint", s in (200, 404), f"HTTP {s} — {d.get('message','')}")

print("\n========== 2. CLIENT BACKEND (8000) ==========")

s, d = post('http://localhost:8000/api/auth/sso',
            {'license_token': srv_token,
             'user': {'username': 'testuser1778676422', 'email': 'test@example.com',
                      'plan': 'agency', 'role': 'admin'}})
check("SSO bridge", s == 200 and 'access_token' in d, f"HTTP {s}")
sso_token = d.get('access_token', '')

s, d = get('http://localhost:8000/api/auth/me', sso_token)
check("Client /me", s == 200 and 'username' in d, f"user={d.get('username')} plan={d.get('plan')}")

s, d = get('http://localhost:8000/api/stats', sso_token)
check("Stats endpoint", s == 200, f"HTTP {s} — {d}")

s, d = get('http://localhost:8000/api/campaigns', sso_token)
check("Campaigns list", s == 200, f"HTTP {s} — count={len(d) if isinstance(d, list) else d}")

s, d = get('http://localhost:8000/api/proxies', sso_token)
check("Proxies list", s == 200, f"HTTP {s} — count={len(d) if isinstance(d, list) else d}")

print("\n========== 3. CLIENT FRONTEND (3000) ==========")

s, d = get('http://localhost:3000/', raw=True)
check("Frontend anasayfa", s == 200, f"HTTP {s}")

s, d = get('http://localhost:3000/api/stats', sso_token)
check("Vite proxy → backend", s == 200, f"HTTP {s}")

print("\n========== 4. SERVER FRONTEND (3001) ==========")

s, d = get('http://localhost:3001/', raw=True)
check("Server frontend", s == 200, f"HTTP {s}")

print("\n" + "="*50)
if errors:
    print(f"\033[91m  {len(errors)} HATA:\033[0m " + ", ".join(errors))
    sys.exit(1)
else:
    print(f"\033[92m  Tum testler gecti! Sistem hazir.\033[0m")
print("="*50 + "\n")
