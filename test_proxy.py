"""Proxy ve kampanya detay testi"""
import urllib.request, urllib.error, json, sys
sys.path.insert(0, r"c:\RequestHitBotu\client")

def post(url, data, token=""):
    h = {"Content-Type": "application/json"}
    if token: h["Authorization"] = "Bearer " + token
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(url, json.dumps(data).encode(), h, method="POST"), timeout=5)
        return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def get(url, token):
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(url, headers={"Authorization": "Bearer " + token}), timeout=5)
        return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

srv = post("http://localhost:8001/api/auth/login",
           {"username": "testuser1778676422", "password": "admin123"})["access_token"]
sso = post("http://localhost:8000/api/auth/sso",
           {"license_token": srv, "user": {"username": "testuser1778676422",
            "email": "t@t.com", "plan": "agency", "role": "admin"}})["access_token"]

print("=== KAMPANYA DETAY ===")
camps = get("http://localhost:8000/api/campaigns", sso)
c = camps[0]
for k, v in c.items():
    print(f"  {k}: {v}")

print("\n=== PROXY DETAY (ilk 5) ===")
proxies = get("http://localhost:8000/api/proxies", sso)
for p in proxies[:5]:
    print(f"  [{p.get('id')}] {p.get('address')} | aktif={p.get('is_active')} | tip={p.get('proxy_type')}")

print(f"\n  Toplam: {len(proxies)} proxy, {sum(1 for p in proxies if p.get('is_active'))} aktif")
