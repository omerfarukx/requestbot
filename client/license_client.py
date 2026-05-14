"""
Lisans sunucusu istemcisi.
- Machine ID üret (donanim parmak izi)
- Login → JWT token al
- Validate → cihaz kilidi + lisans kontrolü
- Heartbeat → 5 dakikada bir validate
"""
import hashlib
import json
import os
import platform
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
import uuid
from typing import Callable, Optional

# ── Config ────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "backend", "config.json")
TOKEN_PATH = os.path.join(os.environ.get("APPDATA", BASE_DIR), "RequestBot", "session.json")

DEFAULT_SERVER = "http://localhost:8001"


def _load_cfg() -> dict:
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def server_url() -> str:
    return _load_cfg().get("license_server") or os.environ.get("LICENSE_SERVER") or DEFAULT_SERVER


# ── Machine ID ────────────────────────────────────────────────────────────────

_cached_id: Optional[str] = None


def get_machine_id() -> str:
    """Donanim parmak izi: CPU + disk seri + MAC."""
    global _cached_id
    if _cached_id:
        return _cached_id

    parts = []

    # CPU + makine adi
    try:
        parts.append(platform.processor() or "")
        parts.append(platform.machine() or "")
    except Exception:
        pass

    # Windows: WMI ile disk seri + UUID
    if platform.system() == "Windows":
        try:
            r = subprocess.run(
                ["wmic", "csproduct", "get", "uuid"],
                capture_output=True, text=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
            )
            for line in r.stdout.splitlines():
                line = line.strip()
                if line and "UUID" not in line.upper():
                    parts.append(line)
                    break
        except Exception:
            pass

    # MAC adresi (uuid.getnode)
    try:
        mac = uuid.getnode()
        parts.append(f"{mac:012x}")
    except Exception:
        pass

    raw = "|".join(parts) or "fallback-no-hw"
    _cached_id = hashlib.sha256(raw.encode()).hexdigest()[:32]
    return _cached_id


def get_hostname() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"


def get_os_info() -> str:
    try:
        return f"{platform.system()} {platform.release()}"
    except Exception:
        return "unknown"


# ── HTTP yardımcılar ──────────────────────────────────────────────────────────

class LicenseError(Exception):
    pass


def _post(path: str, body: dict, token: Optional[str] = None, timeout: int = 10) -> dict:
    url = server_url() + path
    data = json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read()).get("detail", str(e))
        except Exception:
            err = str(e)
        raise LicenseError(err)
    except Exception as e:
        raise LicenseError(f"Sunucuya ulaşılamıyor: {e}")


# ── API ───────────────────────────────────────────────────────────────────────

def login(username: str, password: str) -> dict:
    """Returns { access_token, user }."""
    return _post("/api/auth/login", {"username": username, "password": password})


def register(email: str, username: str, password: str) -> dict:
    return _post("/api/auth/register", {"email": email, "username": username, "password": password})


def validate(token: str) -> dict:
    """Returns { valid, reason?, plan?, expires_at? }."""
    body = {
        "machine_id": get_machine_id(),
        "hostname": get_hostname(),
        "os_info": get_os_info(),
    }
    return _post("/api/license/validate", body, token=token)


# ── Token cache ──────────────────────────────────────────────────────────────

def save_session(token: str, user: dict):
    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump({"token": token, "user": user}, f)


def load_session() -> Optional[dict]:
    try:
        with open(TOKEN_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def clear_session():
    try:
        if os.path.exists(TOKEN_PATH):
            os.remove(TOKEN_PATH)
    except Exception:
        pass


# ── Heartbeat ────────────────────────────────────────────────────────────────

class HeartbeatManager:
    """5 dakikada bir validate — fail olursa callback çağır."""

    def __init__(self, token: str, on_invalid: Callable[[str], None], interval_seconds: int = 300):
        self.token = token
        self.on_invalid = on_invalid
        self.interval = interval_seconds
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="LicenseHeartbeat")
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        while not self._stop.is_set():
            # Bekleme — 10sn parçalara böl, çabuk çıkabilelim
            for _ in range(self.interval // 10):
                if self._stop.is_set():
                    return
                time.sleep(10)
            if self._stop.is_set():
                return
            try:
                r = validate(self.token)
                if not r.get("valid"):
                    reason = r.get("reason") or "Lisans gecersiz"
                    self.on_invalid(reason)
                    return
            except LicenseError as e:
                # Online-only mod: server'a ulasilamadi → kapat
                self.on_invalid(f"Sunucu bağlantısı yok: {e}")
                return
