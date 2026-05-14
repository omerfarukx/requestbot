"""Proxy gercek field adlarini goster"""
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

proxies = get("http://localhost:8000/api/proxies", sso)
print("Proxy[0] tum alanlar:")
if proxies:
    for k, v in proxies[0].items():
        print(f"  {k}: {v}")
else:
    print("  Proxy listesi bos!")
