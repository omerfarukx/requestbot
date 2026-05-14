import sys
sys.path.insert(0, ".")
from curl_cffi.requests import Session as CurlSession

proxies_list = [
    "31.59.20.176:6754:cgulqggc:mi0wraoa2idx",
    "31.56.127.193:7684:cgulqggc:mi0wraoa2idx",
    "45.38.107.97:6014:cgulqggc:mi0wraoa2idx",
    "107.172.163.27:6543:cgulqggc:mi0wraoa2idx",
    "198.23.243.226:6361:cgulqggc:mi0wraoa2idx",
    "216.10.27.159:6837:cgulqggc:mi0wraoa2idx",
    "142.111.67.146:5611:cgulqggc:mi0wraoa2idx",
    "191.96.254.138:6185:cgulqggc:mi0wraoa2idx",
    "31.58.9.4:6077:cgulqggc:mi0wraoa2idx",
    "23.229.19.94:8689:cgulqggc:mi0wraoa2idx",
]

active = 0
for p in proxies_list:
    ip, port, user, pw = p.split(":")
    proxy_url = f"http://{user}:{pw}@{ip}:{port}"
    try:
        with CurlSession(impersonate="chrome124") as s:
            r = s.get("https://httpbin.org/ip", proxies={"http": proxy_url, "https": proxy_url}, timeout=8)
            if r.status_code == 200:
                origin = r.json().get("origin", "?")
                print(f"  AKTIF  {ip}:{port}  ->  {origin}")
                active += 1
            else:
                print(f"  HATA   {ip}:{port}  HTTP {r.status_code}")
    except Exception:
        print(f"  DEAD   {ip}:{port}")

print(f"\nToplam aktif: {active}/10")
