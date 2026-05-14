import urllib.request, urllib.error, json, sys
sys.path.insert(0, r"c:\RequestHitBotu\client")

def post(url, data, token=""):
    h = {"Content-Type": "application/json"}
    if token: h["Authorization"] = "Bearer " + token
    r = urllib.request.urlopen(
        urllib.request.Request(url, json.dumps(data).encode(), h, method="POST"), timeout=5)
    return json.loads(r.read())

def get(url, token):
    r = urllib.request.urlopen(
        urllib.request.Request(url, headers={"Authorization": "Bearer " + token}), timeout=5)
    return json.loads(r.read())

srv = post("http://localhost:8001/api/auth/login",
           {"username": "testuser1778676422", "password": "admin123"})["access_token"]
sso = post("http://localhost:8000/api/auth/sso",
           {"license_token": srv, "user": {"username": "testuser1778676422",
            "email": "t@t.com", "plan": "agency", "role": "admin"}})["access_token"]

logs = get("http://localhost:8000/api/logs?limit=30", sso)
print(f"Son {len(logs)} log:\n")

# Hatalara odaklan
errors = [l for l in logs if "hata" in l.get("message","").lower() 
          or "error" in l.get("message","").lower()
          or "fail" in l.get("message","").lower()
          or "❌" in l.get("message","")
          or "✗" in l.get("message","")]

print(f"HATALAR ({len(errors)} adet):")
for l in errors[-10:]:
    print(f"  {l.get('timestamp','')[:19]}  {l.get('message','')[:100]}")

print(f"\nSON 15 LOG:")
for l in logs[-15:]:
    msg = l.get("message","")
    ts = l.get("timestamp","")[:19]
    print(f"  {ts}  {msg[:100]}")
