"""
Telegram Standalone Bot
- Launcher başladığında ayrı thread'de çalışır
- Backend açık/kapalı fark etmez, her zaman aktif
- Komutları backend REST API üzerinden iletir (localhost:8000)
"""
import json
import os
import threading
import time
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional

BACKEND_URL = "http://localhost:8000"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "config.json")

_stop_event = threading.Event()
_thread: Optional[threading.Thread] = None


# ── Yardımcı: config ────────────────────────────────────────────────────────

def _load_cfg() -> dict:
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ── Yardımcı: Telegram API ──────────────────────────────────────────────────

def _tg_get(token: str, method: str, params: dict) -> dict:
    qs = urllib.parse.urlencode(params)
    url = f"https://api.telegram.org/bot{token}/{method}?{qs}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.loads(r.read())
    except Exception:
        return {}


def _send(token: str, chat_id: str, text: str):
    params = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }
    _tg_get(token, "sendMessage", params)


# ── Yardımcı: Backend API ───────────────────────────────────────────────────

def _backend_get(path: str) -> Optional[dict]:
    try:
        with urllib.request.urlopen(f"{BACKEND_URL}{path}", timeout=5) as r:
            return json.loads(r.read())
    except Exception:
        return None


def _backend_post(path: str, body: dict = None) -> Optional[dict]:
    try:
        data = json.dumps(body or {}).encode()
        req = urllib.request.Request(
            f"{BACKEND_URL}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except Exception:
        return None


def _backend_up() -> bool:
    return _backend_get("/api/stats") is not None


# ── Komut işleyici ──────────────────────────────────────────────────────────

def _handle(text: str) -> str:
    parts = text.strip().split()
    cmd = parts[0].lower().split("@")[0]
    args = parts[1:]

    if cmd in ("/start", "/help"):
        return _help_text()

    # Backend gerektiren komutlar
    if not _backend_up():
        return (
            "⚠️ <b>Backend şu an kapalı.</b>\n\n"
            "Launcher'dan sistemi başlatın, ardından komutu tekrar deneyin.\n\n"
            + _help_text()
        )

    if cmd == "/stats":
        return _cmd_stats()
    elif cmd == "/campaigns":
        return _cmd_campaigns()
    elif cmd == "/rank":
        return _cmd_rank()
    elif cmd == "/report":
        return _cmd_report()
    elif cmd == "/start_bot":
        return _cmd_start(args)
    elif cmd == "/stop_bot":
        return _cmd_stop(args)
    else:
        return f"❓ Bilinmeyen komut: <code>{cmd}</code>\n\n{_help_text()}"


def _help_text() -> str:
    return (
        "<b>🤖 RequestHitBot Komutları</b>\n\n"
        "/stats — Anlık istatistikler\n"
        "/campaigns — Kampanya listesi\n"
        "/rank — Keyword sıralamaları\n"
        "/report — 24 saatlik özet\n"
        "/start_bot ID — Kampanya başlat\n"
        "/stop_bot ID — Kampanya durdur\n"
        "/help — Bu mesaj\n\n"
        "<i>Her sabah 09:00'da otomatik rapor gönderilir.</i>"
    )


def _cmd_stats() -> str:
    d = _backend_get("/api/stats")
    if not d:
        return "❌ İstatistik alınamadı"
    total = d.get("total_visits", 0)
    success = d.get("successful_visits", 0)
    rate = (success / total * 100) if total else 0
    return (
        "<b>📊 Sistem İstatistikleri</b>\n\n"
        f"🎯 Toplam ziyaret: <b>{total}</b>\n"
        f"✅ Başarılı: <b>{success}</b> (%{rate:.1f})\n"
        f"📈 Kampanya: <b>{d.get('total_campaigns', 0)}</b> ({d.get('running_campaigns', 0)} aktif)\n"
        f"🌐 Proxy: <b>{d.get('active_proxies', 0)}</b> aktif"
    )


def _cmd_campaigns() -> str:
    campaigns = _backend_get("/api/campaigns")
    if campaigns is None:
        return "❌ Kampanya listesi alınamadı"
    if not campaigns:
        return "Henüz kampanya yok"
    lines = ["<b>📋 Kampanyalar</b>\n"]
    for c in campaigns:
        st = c.get("status", "stopped")
        dot = "🟢" if st == "running" else "⚫"
        lines.append(
            f"\n<b>#{c['id']} {c['name']}</b>\n"
            f"  {dot} {st}\n"
            f"  🌐 {c.get('target_url','')}\n"
            f"  🎯 {c.get('daily_target',0)} ziyaret/gün"
        )
    return "\n".join(lines)


def _cmd_rank() -> str:
    campaigns = _backend_get("/api/campaigns")
    if not campaigns:
        return "Kampanya bulunamadı"
    lines = ["<b>📈 Anahtar Kelime Sıralamaları</b>"]
    for c in campaigns:
        ranks = _backend_get(f"/api/campaigns/{c['id']}/ranks")
        if not ranks:
            continue
        lines.append(f"\n<b>{c['name']}</b>")
        seen = {}
        for r in ranks:
            kw = r.get("keyword", "")
            if kw not in seen:
                seen[kw] = r
        for kw, r in seen.items():
            rank = r.get("rank")
            if rank:
                em = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "📍"
                lines.append(f"  {em} <i>{kw}</i> → <b>{rank}. sıra</b>")
            else:
                lines.append(f"  ❓ <i>{kw}</i> → bulunamadı")
    return "\n".join(lines) if len(lines) > 1 else "Henüz sıralama verisi yok"


def _cmd_report() -> str:
    d = _backend_get("/api/analytics/hourly?hours=24")
    stats = _backend_get("/api/stats")
    if not stats:
        return "❌ Rapor alınamadı"
    total = stats.get("total_visits", 0)
    success = stats.get("successful_visits", 0)
    rate = (success / total * 100) if total else 0

    lines = ["<b>📋 Anlık Sistem Raporu</b>\n"]
    lines.append(f"🎯 Toplam ziyaret: <b>{total}</b>")
    lines.append(f"✅ Başarılı: <b>{success}</b> (%{rate:.1f})")
    lines.append(f"📈 Çalışan kampanya: <b>{stats.get('running_campaigns', 0)}</b>")
    lines.append(f"🌐 Aktif proxy: <b>{stats.get('active_proxies', 0)}</b>")

    if d:
        peak = max(d, key=lambda x: x.get("visits", 0), default=None)
        if peak:
            lines.append(f"\n⚡ En yoğun saat: <b>{peak.get('hour', '?')}:00</b> ({peak.get('visits', 0)} ziyaret)")

    return "\n".join(lines)


def _cmd_start(args) -> str:
    if not args:
        return "Kullanım: <code>/start_bot ID</code>"
    try:
        cid = int(args[0])
    except ValueError:
        return "ID sayı olmalı"
    r = _backend_post(f"/api/campaigns/{cid}/start")
    if r is None:
        return f"❌ Kampanya #{cid} başlatılamadı"
    return f"🚀 Kampanya <b>#{cid}</b> başlatıldı"


def _cmd_stop(args) -> str:
    if not args:
        return "Kullanım: <code>/stop_bot ID</code>"
    try:
        cid = int(args[0])
    except ValueError:
        return "ID sayı olmalı"
    r = _backend_post(f"/api/campaigns/{cid}/stop")
    if r is None:
        return f"❌ Kampanya #{cid} durdurulamadı"
    return f"⏹ Kampanya <b>#{cid}</b> durduruldu"


# ── Günlük rapor ─────────────────────────────────────────────────────────────

def _daily_report_thread(token: str, chat_id: str):
    """Her gün 09:00 TR saatinde rapor gönderir."""
    import datetime
    TR_OFFSET = 3 * 3600  # UTC+3

    while not _stop_event.is_set():
        try:
            now_utc = time.time()
            now_tr = now_utc + TR_OFFSET
            struct = time.gmtime(now_tr)
            # Bir sonraki 09:00 TR
            target_today = now_tr - (struct.tm_hour * 3600 + struct.tm_min * 60 + struct.tm_sec) + 9 * 3600
            if now_tr >= target_today:
                target_today += 86400  # yarın
            wait_sec = target_today - now_tr
            print(f"[TelegramStandalone] Günlük rapor: {wait_sec/3600:.1f} saat sonra")

            # Bekleme — 60 saniyelik parçalara böl (stop_event'i kontrol etmek için)
            waited = 0
            while waited < wait_sec:
                if _stop_event.is_set():
                    return
                chunk = min(60, wait_sec - waited)
                time.sleep(chunk)
                waited += chunk

            if _stop_event.is_set():
                return

            report = _cmd_report()
            header = "<b>☀️ Günaydın! Sabah Raporu</b>\n\n"
            _send(token, chat_id, header + report)

        except Exception as e:
            print(f"[TelegramStandalone] daily report error: {e}")
            time.sleep(3600)


# ── Ana polling döngüsü ──────────────────────────────────────────────────────

def _bot_loop():
    cfg = _load_cfg()
    token = cfg.get("telegram_token", "")
    chat_id = str(cfg.get("telegram_chat_id", ""))

    if not token or not chat_id:
        print("[TelegramStandalone] Token veya chat_id eksik — bot pasif")
        return

    print("[TelegramStandalone] Bot başlatıldı, Telegram dinleniyor…")

    # Günlük rapor thread'i başlat
    dr_thread = threading.Thread(target=_daily_report_thread, args=(token, chat_id), daemon=True)
    dr_thread.start()

    offset = 0
    while not _stop_event.is_set():
        try:
            params = {"offset": offset, "timeout": 25, "allowed_updates": '["message"]'}
            data = _tg_get(token, "getUpdates", params)
            updates = data.get("result", []) if data.get("ok") else []

            for upd in updates:
                offset = upd["update_id"] + 1
                msg = upd.get("message", {})
                from_chat = str(msg.get("chat", {}).get("id", ""))
                text = (msg.get("text") or "").strip()

                if not text or not text.startswith("/"):
                    continue
                if from_chat != chat_id:
                    _send(token, from_chat, "⛔ Yetkisiz erişim")
                    continue

                reply = _handle(text)
                if reply:
                    _send(token, chat_id, reply)

        except Exception as e:
            print(f"[TelegramStandalone] poll error: {e}")
            if not _stop_event.is_set():
                time.sleep(5)


# ── Public API ───────────────────────────────────────────────────────────────

def start():
    """Launcher'dan çağrılır — arka planda thread başlatır."""
    global _thread
    _stop_event.clear()
    _thread = threading.Thread(target=_bot_loop, daemon=True, name="TelegramStandalone")
    _thread.start()


def stop():
    """Launcher kapanırken çağrılır."""
    _stop_event.set()
