"""
Telegram Bot — gelen komutları işler:
  /stats         — anlık istatistikler
  /rank          — tüm keyword sıralamaları
  /campaigns     — kampanya listesi ve durumları
  /start_bot ID  — kampanyayı başlat
  /stop_bot ID   — kampanyayı durdur
  /help          — komut listesi
"""
import asyncio
import json
import os
from typing import Optional
from urllib.parse import urlencode

from curl_cffi.requests import Session as CurlSession
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def _load_config() -> dict:
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _send_message(token: str, chat_id: str, text: str):
    try:
        params = urlencode({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        })
        url = f"https://api.telegram.org/bot{token}/sendMessage?{params}"
        with CurlSession(impersonate="chrome124") as s:
            s.get(url, timeout=10)
    except Exception as e:
        print(f"[Telegram] send error: {e}")


async def _get_updates_async(token: str, offset: int) -> list:
    """Long polling — yeni mesajları çeker."""
    loop = asyncio.get_event_loop()

    def _sync_call():
        try:
            params = urlencode({"offset": offset, "timeout": 25})
            url = f"https://api.telegram.org/bot{token}/getUpdates?{params}"
            with CurlSession(impersonate="chrome124") as s:
                r = s.get(url, timeout=30)
                data = r.json()
                return data.get("result", []) if data.get("ok") else []
        except Exception as e:
            print(f"[Telegram] getUpdates error: {e}")
            return []

    return await loop.run_in_executor(None, _sync_call)


class TelegramBot:
    def __init__(self, bot_engine, db_factory):
        self.bot_engine = bot_engine
        self.db_factory = db_factory
        self.task: Optional[asyncio.Task] = None
        self.report_task: Optional[asyncio.Task] = None
        self._running = False

    def start(self):
        if self.task and not self.task.done():
            return
        self._running = True
        self.task = asyncio.create_task(self._poll_loop())
        self.report_task = asyncio.create_task(self._daily_report_loop())
        print("[Telegram] Bot dinleme + günlük rapor başlatıldı")

    def stop(self):
        self._running = False
        if self.task:
            self.task.cancel()
        if self.report_task:
            self.report_task.cancel()

    async def _daily_report_loop(self):
        """Her gün TR saatiyle 09:00'da günlük rapor gönderir."""
        from datetime import datetime, timedelta, timezone
        TR = timezone(timedelta(hours=3))
        cfg = _load_config()
        token = cfg.get("telegram_token", "")
        chat_id = str(cfg.get("telegram_chat_id", ""))
        if not token or not chat_id:
            return

        while self._running:
            try:
                now = datetime.now(TR)
                # Bir sonraki 09:00'ı hesapla
                target = now.replace(hour=9, minute=0, second=0, microsecond=0)
                if now >= target:
                    target += timedelta(days=1)
                wait_seconds = (target - now).total_seconds()
                print(f"[Telegram] Günlük rapor: {wait_seconds/3600:.1f} saat sonra")
                await asyncio.sleep(wait_seconds)
                if not self._running:
                    break
                report = await self._build_daily_report()
                _send_message(token, chat_id, report)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Telegram] Daily report error: {e}")
                await asyncio.sleep(3600)

    async def _build_daily_report(self) -> str:
        """Son 24 saatin özetini hazırlar."""
        from datetime import datetime, timedelta, timezone
        from models import Visit, Campaign, RankCheck
        from sqlalchemy import func

        async with self.db_factory() as db:
            cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)

            total_24h = await db.scalar(
                select(func.count(Visit.id)).where(Visit.started_at >= cutoff)
            ) or 0
            success_24h = await db.scalar(
                select(func.count(Visit.id)).where(
                    Visit.started_at >= cutoff,
                    Visit.status == "success",
                )
            ) or 0

            # Kampanyalar
            camps_res = await db.execute(select(Campaign))
            campaigns = camps_res.scalars().all()

            lines = ["<b>☀️ Günaydın! 24 Saatlik Rapor</b>\n"]
            lines.append(f"📊 Toplam ziyaret: <b>{total_24h}</b>")
            lines.append(f"✅ Başarılı: <b>{success_24h}</b>")
            rate = (success_24h / total_24h * 100) if total_24h else 0
            lines.append(f"📈 Başarı oranı: <b>%{rate:.1f}</b>\n")

            # Her kampanya için sıralama özeti
            for c in campaigns:
                keywords = [k.strip() for k in (c.keyword or "").split(",") if k.strip()]
                if not keywords:
                    continue
                lines.append(f"<b>{c.name}</b>")
                for kw in keywords:
                    # Bugünkü en son sıra
                    today_r = await db.execute(
                        select(RankCheck).where(
                            RankCheck.campaign_id == c.id,
                            RankCheck.keyword == kw,
                            RankCheck.checked_at >= cutoff,
                        ).order_by(RankCheck.checked_at.desc()).limit(1)
                    )
                    today = today_r.scalar_one_or_none()
                    # 24 saat öncesi
                    yesterday_r = await db.execute(
                        select(RankCheck).where(
                            RankCheck.campaign_id == c.id,
                            RankCheck.keyword == kw,
                            RankCheck.checked_at < cutoff,
                        ).order_by(RankCheck.checked_at.desc()).limit(1)
                    )
                    yesterday = yesterday_r.scalar_one_or_none()

                    if today and today.rank:
                        if yesterday and yesterday.rank:
                            diff = yesterday.rank - today.rank
                            if diff > 0:
                                arrow = f" 🔺+{diff}"
                            elif diff < 0:
                                arrow = f" 🔻{diff}"
                            else:
                                arrow = " ➖"
                        else:
                            arrow = " ✨yeni"
                        lines.append(f"  📍 <i>{kw}</i> → <b>{today.rank}.</b>{arrow}")
                    else:
                        lines.append(f"  ❓ <i>{kw}</i> → veri yok")
                lines.append("")

            return "\n".join(lines)

    async def _poll_loop(self):
        cfg = _load_config()
        token = cfg.get("telegram_token", "")
        authorized_chat = str(cfg.get("telegram_chat_id", ""))
        if not token or not authorized_chat:
            print("[Telegram] Token/chat_id eksik, bot pasif")
            return

        offset = 0
        while self._running:
            try:
                updates = await _get_updates_async(token, offset)
                for upd in updates:
                    offset = upd["update_id"] + 1
                    msg = upd.get("message", {})
                    chat_id = str(msg.get("chat", {}).get("id", ""))
                    text = (msg.get("text") or "").strip()

                    if not text or not text.startswith("/"):
                        continue
                    if chat_id != authorized_chat:
                        _send_message(token, chat_id, "⛔ Yetkisiz erişim")
                        continue

                    response = await self._handle_command(text)
                    if response:
                        _send_message(token, chat_id, response)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Telegram] poll error: {e}")
                await asyncio.sleep(5)

    async def _handle_command(self, text: str) -> str:
        parts = text.split()
        cmd = parts[0].lower().split("@")[0]
        args = parts[1:]

        if cmd == "/start" or cmd == "/help":
            return self._help_text()
        elif cmd == "/stats":
            return await self._stats()
        elif cmd == "/rank":
            return await self._ranks()
        elif cmd == "/campaigns":
            return await self._campaigns()
        elif cmd == "/report":
            return await self._build_daily_report()
        elif cmd == "/start_bot":
            return await self._start_campaign(args)
        elif cmd == "/stop_bot":
            return await self._stop_campaign(args)
        else:
            return f"❓ Bilinmeyen komut: {cmd}\n\n{self._help_text()}"

    def _help_text(self) -> str:
        return (
            "<b>🤖 RequestHitBot Komutları</b>\n\n"
            "/stats — Anlık istatistikler\n"
            "/rank — Tüm keyword sıralamaları\n"
            "/campaigns — Kampanya listesi\n"
            "/report — 24 saatlik özet rapor\n"
            "/start_bot ID — Kampanyayı başlat\n"
            "/stop_bot ID — Kampanyayı durdur\n"
            "/help — Bu mesaj\n\n"
            "<i>Her sabah 09:00'da otomatik rapor gönderilir.</i>"
        )

    async def _stats(self) -> str:
        from models import Campaign, Visit, Proxy

        async with self.db_factory() as db:
            total = await db.scalar(select(func.count(Visit.id)))
            success = await db.scalar(select(func.count(Visit.id)).where(Visit.status == "success"))
            campaigns_count = await db.scalar(select(func.count(Campaign.id)))
            active_proxies = await db.scalar(
                select(func.count(Proxy.id)).where(Proxy.status == "active")
            )
            dead_proxies = await db.scalar(
                select(func.count(Proxy.id)).where(Proxy.status == "dead")
            )

        running = len(self.bot_engine.running_campaigns)
        success_rate = (success / total * 100) if total else 0
        return (
            f"<b>📊 Sistem İstatistikleri</b>\n\n"
            f"🎯 Toplam ziyaret: <b>{total}</b>\n"
            f"✅ Başarılı: <b>{success}</b> (%{success_rate:.1f})\n"
            f"📈 Kampanya: <b>{campaigns_count}</b> ({running} aktif)\n"
            f"🌐 Proxy: <b>{active_proxies}</b> aktif, {dead_proxies} dead"
        )

    async def _ranks(self) -> str:
        from models import Campaign, RankCheck

        async with self.db_factory() as db:
            campaigns_res = await db.execute(select(Campaign))
            campaigns = campaigns_res.scalars().all()
            if not campaigns:
                return "Henüz kampanya yok"

            out = ["<b>📈 Anahtar Kelime Sıralamaları</b>\n"]
            for c in campaigns:
                out.append(f"\n<b>{c.name}</b>")
                # Her keyword icin en son sirayi al
                keywords = [k.strip() for k in (c.keyword or "").split(",") if k.strip()]
                for kw in keywords:
                    r = await db.execute(
                        select(RankCheck).where(
                            RankCheck.campaign_id == c.id,
                            RankCheck.keyword == kw,
                        ).order_by(RankCheck.checked_at.desc()).limit(1)
                    )
                    rc = r.scalar_one_or_none()
                    if rc and rc.rank:
                        emoji = "🥇" if rc.rank == 1 else "🥈" if rc.rank == 2 else "🥉" if rc.rank == 3 else "📍"
                        out.append(f"  {emoji} <i>{kw}</i> → <b>{rc.rank}. sıra</b>")
                    else:
                        out.append(f"  ❓ <i>{kw}</i> → henüz kontrol edilmedi")
            return "\n".join(out)

    async def _campaigns(self) -> str:
        from models import Campaign

        async with self.db_factory() as db:
            res = await db.execute(select(Campaign))
            campaigns = res.scalars().all()
            if not campaigns:
                return "Henüz kampanya yok"

            out = ["<b>📋 Kampanyalar</b>\n"]
            for c in campaigns:
                is_running = self.bot_engine.is_running(c.id)
                status = "🟢 Çalışıyor" if is_running else "⚫ Duruyor"
                out.append(
                    f"\n<b>#{c.id} {c.name}</b>\n"
                    f"  {status}\n"
                    f"  🌐 {c.target_url}\n"
                    f"  🎯 {c.daily_target} ziyaret/gün"
                )
            return "\n".join(out)

    async def _start_campaign(self, args) -> str:
        if not args:
            return "Kullanım: <code>/start_bot ID</code>\n\nÖr: /start_bot 1"
        try:
            cid = int(args[0])
        except ValueError:
            return "ID sayı olmalı"

        from models import Campaign
        async with self.db_factory() as db:
            c = await db.get(Campaign, cid)
            if not c:
                return f"❌ Kampanya #{cid} bulunamadı"
            if self.bot_engine.is_running(cid):
                return f"⚠️ Kampanya #{cid} zaten çalışıyor"

            c.status = "running"
            await db.commit()
        # bot_engine kendisi DB'den çekiyor
        await self.bot_engine.start_campaign(cid)
        return f"🚀 Kampanya #{cid} başlatıldı"

    async def _stop_campaign(self, args) -> str:
        if not args:
            return "Kullanım: <code>/stop_bot ID</code>"
        try:
            cid = int(args[0])
        except ValueError:
            return "ID sayı olmalı"

        if not self.bot_engine.is_running(cid):
            return f"⚠️ Kampanya #{cid} zaten duruyor"
        await self.bot_engine.stop_campaign(cid)

        from models import Campaign
        async with self.db_factory() as db:
            c = await db.get(Campaign, cid)
            if c:
                c.status = "stopped"
                await db.commit()
        return f"⏹ Kampanya #{cid} durduruldu"
