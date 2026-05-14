import asyncio
import random
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Callable, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote_plus, parse_qs
from curl_cffi.requests import Session as CurlSession

TURKEY_TZ = timezone(timedelta(hours=3))

_executor = ThreadPoolExecutor(max_workers=30)


def _sync_get(url: str, headers: dict, proxy_url: str | None) -> tuple[int, str]:
    """Sync curl_cffi request — thread pool içinde çalışır."""
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
    with CurlSession(impersonate="chrome124") as s:
        r = s.get(url, headers=headers, proxies=proxies, timeout=30, allow_redirects=True)
        return r.status_code, r.text


def _sync_google_search(keyword: str, target_domain: str, ua: str, proxy_url: str | None) -> tuple[bool, str, int]:
    """
    DuckDuckGo HTML API ile arama yapar (Google CAPTCHA engelini bypass eder).
    Hedef domain bulunursa (True, url, rank) döner.
    SerpAPI anahtarı config.json'da varsa Google sonuçlarını kullanır.
    """
    import json as _json
    clean_domain = target_domain.replace("www.", "")
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

    # SerpAPI varsa Google sonuçlarını kullan
    try:
        import os as _os
        cfg_path = _os.path.join(_os.path.dirname(__file__), "config.json")
        with open(cfg_path, encoding="utf-8") as f:
            cfg = _json.load(f)
        serpapi_key = cfg.get("serpapi_key", "")
        if serpapi_key:
            serp_url = (f"https://serpapi.com/search.json?q={quote_plus(keyword)}"
                        f"&hl=tr&gl=tr&num=100&api_key={serpapi_key}")
            with CurlSession(impersonate="chrome124") as s:
                r = s.get(serp_url, proxies=proxies, timeout=20)
                data = r.json()
                organic = data.get("organic_results", [])
                for i, result in enumerate(organic, 1):
                    link = result.get("link", "")
                    if clean_domain in link:
                        return True, link, i
                return False, "", 0
    except Exception:
        pass

    # DuckDuckGo HTML — ücretsiz, CAPTCHA yok, 10'ar sayfa
    try:
        rank = 0
        for page_start in [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]:
            ddg_url = (f"https://html.duckduckgo.com/html/?q={quote_plus(keyword)}"
                       f"&kl=tr-tr&s={page_start}")
            with CurlSession(impersonate="chrome124") as s:
                r = s.get(ddg_url, headers={
                    "User-Agent": ua,
                    "Accept-Language": "tr-TR,tr;q=0.9",
                    "Referer": "https://duckduckgo.com/",
                }, proxies=proxies, timeout=20)
            soup = BeautifulSoup(r.text, "html.parser")
            results = soup.select(".result__url")
            if not results:
                break
            for res in results:
                rank += 1
                url_text = res.get_text(strip=True)
                if clean_domain in url_text or clean_domain.replace("www.", "") in url_text:
                    # Gerçek URL'yi bul
                    parent = res.find_parent("a") or res.find_parent(".result__title")
                    href = ""
                    if parent and parent.name == "a":
                        href = parent.get("href", "")
                    full_url = href if href.startswith("http") else f"https://{url_text}"
                    return True, full_url, rank
            time.sleep(random.uniform(1.5, 3.0))
        return False, "", 0
    except Exception:
        return False, "", 0


def _get_batch_sleep() -> float:
    """Türkiye saatine (UTC+3) göre batch arası bekleme süresi."""
    hour = datetime.now(TURKEY_TZ).hour
    if 9 <= hour < 12 or 13 <= hour < 18:
        return random.uniform(2, 6)        # Yoğun mesai saatleri
    elif 12 <= hour < 13 or 18 <= hour < 22:
        return random.uniform(20, 45)      # Öğle + akşam
    else:
        return random.uniform(180, 360)    # Gece — çok yavaş

DESKTOP_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 OPR/110.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

MOBILE_UAS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S921B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Android 14; Mobile; rv:124.0) Gecko/124.0 Firefox/124.0",
]

COMMON_USER_AGENTS = DESKTOP_UAS + MOBILE_UAS  # backward compat


def get_random_ua(mobile_pct: int = 50) -> str:
    """mobile_pct oranında mobil UA döndürür."""
    if random.randint(1, 100) <= mobile_pct:
        return random.choice(MOBILE_UAS)
    return random.choice(DESKTOP_UAS)


SOCIAL_REFERRERS = [
    "https://l.facebook.com/",
    "https://m.facebook.com/",
    "https://t.co/",
    "https://www.instagram.com/",
    "https://www.linkedin.com/",
    "https://www.youtube.com/",
]

DIRECT_REFERRERS = ["", "https://www.bing.com/", "https://duckduckgo.com/"]


def _pick_referrer_source(referrer_mix: str) -> str:
    """'google:70,direct:20,social:10' -> ağırlıklı seçim."""
    try:
        items = []
        for pair in referrer_mix.split(","):
            name, weight = pair.split(":")
            items.append((name.strip(), int(weight)))
        total = sum(w for _, w in items)
        r = random.randint(1, total)
        cum = 0
        for name, w in items:
            cum += w
            if r <= cum:
                return name
    except Exception:
        pass
    return "google"


def build_referrer(keyword: str, search_engine: str, referrer_mix: str = "") -> str:
    """
    referrer_mix verilirse karışık referrer döner (google/direct/social).
    Verilmezse search_engine'e göre tek tip döner.
    """
    if referrer_mix:
        source = _pick_referrer_source(referrer_mix)
        if source == "direct":
            return random.choice(DIRECT_REFERRERS)
        elif source == "social":
            return random.choice(SOCIAL_REFERRERS)
        # google için aşağıya devam

    if not keyword:
        return "https://www.google.com/"
    kw = quote_plus(keyword)
    if search_engine == "yandex":
        return f"https://yandex.com.tr/search/?text={kw}"
    elif search_engine == "bing":
        return f"https://www.bing.com/search?q={kw}"
    elif search_engine == "direct":
        return ""
    else:
        return f"https://www.google.com/search?q={kw}&hl=tr"


def parse_proxy_string(proxy_str: str) -> Optional[Dict]:
    """Supports formats:
    host:port
    host:port:user:pass
    user:pass@host:port
    protocol://host:port
    protocol://user:pass@host:port
    """
    proxy_str = proxy_str.strip()
    if not proxy_str or proxy_str.startswith("#"):
        return None

    protocol = "http"
    username = None
    password = None

    if "://" in proxy_str:
        protocol, proxy_str = proxy_str.split("://", 1)

    if "@" in proxy_str:
        creds, proxy_str = proxy_str.rsplit("@", 1)
        if ":" in creds:
            username, password = creds.split(":", 1)
        else:
            username = creds

    parts = proxy_str.split(":")
    if len(parts) == 2:
        host, port_str = parts
    elif len(parts) == 4 and not username:
        host, port_str, username, password = parts
    elif len(parts) == 1:
        host = parts[0]
        port_str = "80"
    else:
        return None

    try:
        port = int(port_str)
    except ValueError:
        return None

    if not host:
        return None

    return {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "protocol": protocol,
    }


def _load_telegram_config() -> tuple[str, str]:
    import json, os
    cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(cfg_path, encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg.get("telegram_token", ""), cfg.get("telegram_chat_id", "")
    except Exception:
        return "", ""


def _send_telegram(message: str):
    token, chat_id = _load_telegram_config()
    if not token or not chat_id:
        return
    try:
        from urllib.parse import urlencode
        params = urlencode({"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
        url = f"https://api.telegram.org/bot{token}/sendMessage?{params}"
        with CurlSession(impersonate="chrome124") as s:
            s.get(url, timeout=10)
    except Exception:
        pass


def _get_keywords_list(keyword_str: Optional[str]) -> List[str]:
    """Virgülle ayrılmış keyword listesini döner."""
    if not keyword_str:
        return []
    return [k.strip() for k in keyword_str.split(",") if k.strip()]


class BotEngine:
    def __init__(self):
        self.running_campaigns: Dict[int, asyncio.Task] = {}
        self.rank_checker_tasks: Dict[int, asyncio.Task] = {}
        self.log_subscribers: List[Callable] = []
        self._db_factory = None

    def set_db_factory(self, factory):
        self._db_factory = factory

    def subscribe_logs(self, callback: Callable) -> Callable:
        self.log_subscribers.append(callback)

        def unsubscribe():
            if callback in self.log_subscribers:
                self.log_subscribers.remove(callback)

        return unsubscribe

    async def _emit_log(self, campaign_id: Optional[int], level: str, message: str):
        log_data = {
            "campaign_id": campaign_id,
            "level": level,
            "message": message,
            "created_at": datetime.utcnow().isoformat(),
        }
        for cb in list(self.log_subscribers):
            try:
                await cb(log_data)
            except Exception:
                pass

        if self._db_factory:
            try:
                async with self._db_factory() as db:
                    from models import Log as LogModel
                    db.add(LogModel(campaign_id=campaign_id, level=level, message=message))
                    await db.commit()
            except Exception:
                pass

    async def start_campaign(self, campaign_id: int):
        if campaign_id in self.running_campaigns:
            return
        task = asyncio.create_task(self._run_campaign_loop(campaign_id))
        self.running_campaigns[campaign_id] = task
        rank_task = asyncio.create_task(self._rank_checker_loop(campaign_id))
        self.rank_checker_tasks[campaign_id] = rank_task
        await self._emit_log(campaign_id, "info", f"🚀 Kampanya #{campaign_id} başlatıldı")

    async def stop_campaign(self, campaign_id: int):
        task = self.running_campaigns.pop(campaign_id, None)
        if task:
            task.cancel()
        rank_task = self.rank_checker_tasks.pop(campaign_id, None)
        if rank_task:
            rank_task.cancel()
        await self._emit_log(campaign_id, "info", f"⏹ Kampanya #{campaign_id} durduruldu")

    def is_running(self, campaign_id: int) -> bool:
        task = self.running_campaigns.get(campaign_id)
        return task is not None and not task.done()

    async def _get_campaign_dict(self, campaign_id: int) -> Optional[Dict]:
        if not self._db_factory:
            return None
        try:
            async with self._db_factory() as db:
                from models import Campaign as CampaignModel
                from sqlalchemy import select
                result = await db.execute(select(CampaignModel).where(CampaignModel.id == campaign_id))
                c = result.scalar_one_or_none()
                if not c:
                    return None
                return {
                    "id": c.id,
                    "name": c.name,
                    "target_url": c.target_url,
                    "keyword": c.keyword,
                    "search_engine": c.search_engine,
                    "session_duration_min": c.session_duration_min,
                    "session_duration_max": c.session_duration_max,
                    "concurrent_workers": c.concurrent_workers,
                    "daily_visit_target": c.daily_visit_target,
                    "pages_per_session_min": c.pages_per_session_min,
                    "pages_per_session_max": c.pages_per_session_max,
                    "hourly_limit": c.hourly_limit,
                    "active_hours_start": c.active_hours_start or 0,
                    "active_hours_end": c.active_hours_end or 24,
                    "bounce_rate_pct": c.bounce_rate_pct or 30,
                    "referrer_mix": c.referrer_mix or "google:70,direct:20,social:10",
                    "mobile_ratio_pct": c.mobile_ratio_pct or 65,
                    "status": c.status,
                    "total_visits": c.total_visits,
                }
        except Exception:
            return None

    async def _count_recent_visits(self, campaign_id: int, minutes: int) -> int:
        """Son N dakikadaki ziyaret sayısı."""
        if not self._db_factory:
            return 0
        try:
            async with self._db_factory() as db:
                from models import Visit as VisitModel
                from sqlalchemy import select, func
                cutoff = datetime.utcnow() - timedelta(minutes=minutes)
                result = await db.execute(
                    select(func.count(VisitModel.id)).where(
                        VisitModel.campaign_id == campaign_id,
                        VisitModel.started_at >= cutoff,
                    )
                )
                return result.scalar() or 0
        except Exception:
            return 0

    async def _get_proxy_list(self) -> List[Dict]:
        if not self._db_factory:
            return []
        try:
            async with self._db_factory() as db:
                from models import Proxy as ProxyModel
                from sqlalchemy import select
                result = await db.execute(select(ProxyModel).where(ProxyModel.status != "dead"))
                proxies = result.scalars().all()
                return [
                    {
                        "id": p.id,
                        "host": p.host,
                        "port": p.port,
                        "username": p.username,
                        "password": p.password,
                        "protocol": p.protocol,
                    }
                    for p in proxies
                ]
        except Exception:
            return []

    async def _run_campaign_loop(self, campaign_id: int):
        try:
            while True:
                campaign = await self._get_campaign_dict(campaign_id)
                if not campaign or campaign["status"] != "running":
                    break

                # Aktif saat penceresi kontrolu (TR saati)
                now_hour = datetime.now(TURKEY_TZ).hour
                start_h = campaign["active_hours_start"]
                end_h = campaign["active_hours_end"]
                in_window = (
                    start_h <= now_hour < end_h
                    if start_h < end_h
                    else now_hour >= start_h or now_hour < end_h
                )
                if not in_window:
                    await self._emit_log(
                        campaign_id, "info",
                        f"🌙 Aktif saat dışı ({start_h:02d}:00-{end_h:02d}:00), {now_hour:02d}:00 — uyanılıyor sonra",
                    )
                    await asyncio.sleep(600)
                    continue

                # Saatlik limit kontrolu
                if campaign["hourly_limit"]:
                    hourly_count = await self._count_recent_visits(campaign_id, minutes=60)
                    if hourly_count >= campaign["hourly_limit"]:
                        await self._emit_log(
                            campaign_id, "info",
                            f"⏸ Saatlik limit doldu ({hourly_count}/{campaign['hourly_limit']}), 10 dk bekleniyor",
                        )
                        await asyncio.sleep(600)
                        continue

                if campaign["daily_visit_target"] and campaign["total_visits"] >= campaign["daily_visit_target"]:
                    await self._emit_log(campaign_id, "info", "📊 Günlük hedef tamamlandı, bekleniyor...")
                    await asyncio.sleep(300)
                    continue

                proxies = await self._get_proxy_list()
                if not proxies:
                    await self._emit_log(campaign_id, "warning", "⚠️ Proxy listesi boş — direkt bağlantı kullanılıyor")

                sem = asyncio.Semaphore(campaign["concurrent_workers"])
                tasks = [
                    asyncio.create_task(
                        self._bounded_session(sem, campaign, random.choice(proxies) if proxies else None)
                    )
                    for _ in range(campaign["concurrent_workers"])
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
                sleep_sec = _get_batch_sleep()
                await asyncio.sleep(sleep_sec)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            await self._emit_log(campaign_id, "error", f"💥 Kampanya hatası: {str(e)}")
        finally:
            self.running_campaigns.pop(campaign_id, None)
            if self._db_factory:
                try:
                    async with self._db_factory() as db:
                        from models import Campaign as CampaignModel
                        from sqlalchemy import select
                        result = await db.execute(select(CampaignModel).where(CampaignModel.id == campaign_id))
                        c = result.scalar_one_or_none()
                        if c and c.status == "running":
                            c.status = "stopped"
                            await db.commit()
                except Exception:
                    pass

    async def _bounded_session(self, sem: asyncio.Semaphore, campaign: Dict, proxy: Optional[Dict]):
        async with sem:
            await self._run_session(campaign, proxy)

    async def _run_session(self, campaign: Dict, proxy: Optional[Dict]):
        # Bounce session mi?
        bounce_pct = campaign.get("bounce_rate_pct", 30)
        is_bounce = random.randint(1, 100) <= bounce_pct

        if is_bounce:
            # Hizli bounce — 5-30 saniye, 1 sayfa
            session_duration = random.randint(5, 30)
            pages_to_visit = 1
        else:
            # Normal/derin oturum
            session_duration = random.randint(
                campaign["session_duration_min"] * 60,
                campaign["session_duration_max"] * 60,
            )
            pages_to_visit = random.randint(
                campaign["pages_per_session_min"],
                campaign["pages_per_session_max"],
            )

        proxy_url = None
        proxy_id = None
        proxy_label = "direkt"
        if proxy:
            proxy_id = proxy["id"]
            proxy_label = f"{proxy['host']}:{proxy['port']}"
            if proxy["username"] and proxy["password"]:
                proxy_url = f"{proxy['protocol']}://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
            else:
                proxy_url = f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}"

        start_ts = time.time()
        pages_visited = 0
        success = False
        error_msg = None
        # Mobil/Desktop dengesi
        mobile_pct = campaign.get("mobile_ratio_pct", 65)
        user_agent = get_random_ua(mobile_pct=mobile_pct)
        device_type = "📱" if "Mobile" in user_agent or "iPhone" in user_agent or "Android" in user_agent else "💻"

        loop = asyncio.get_event_loop()

        # Google arama simülasyonu
        target_url = campaign["target_url"]
        keywords = _get_keywords_list(campaign["keyword"])
        active_keyword = random.choice(keywords) if keywords else None

        # Referrer mix — google/direct/social karışımı
        referrer_mix = campaign.get("referrer_mix", "google:70,direct:20,social:10")
        referrer_source = _pick_referrer_source(referrer_mix)
        if referrer_source == "google":
            google_referrer = build_referrer(active_keyword or "", campaign["search_engine"])
        elif referrer_source == "social":
            google_referrer = random.choice(SOCIAL_REFERRERS)
        else:
            google_referrer = random.choice(DIRECT_REFERRERS)

        if campaign["search_engine"] == "google" and active_keyword:
            target_domain = urlparse(campaign["target_url"]).netloc
            found, found_url, rank = await loop.run_in_executor(
                _executor,
                lambda kw=active_keyword: _sync_google_search(kw, target_domain, user_agent, proxy_url),
            )
            if found and found_url:
                target_url = found_url
                await self._emit_log(campaign["id"], "info",
                    f"🔍 [{proxy_label}] '{active_keyword}' → {rank}. sırada bulundu → tıklanıyor")
            else:
                await self._emit_log(campaign["id"], "info",
                    f"🌐 [{proxy_label}] Google referrer ile gidiyor ('{active_keyword}')")

        req_headers = {"User-Agent": user_agent, "Referer": google_referrer}

        try:
            status, html = await loop.run_in_executor(
                _executor, lambda u=target_url: _sync_get(u, req_headers, proxy_url)
            )

            if status < 400:
                pages_visited += 1
                print(f"[BOT OK] campaign={campaign['id']} status={status}")
                bounce_tag = " 🚪bounce" if is_bounce else ""
                await self._emit_log(
                    campaign["id"], "info",
                    f"✓ {device_type} [{proxy_label}] {campaign['target_url']} → {status}{bounce_tag}",
                )

                internal_links = self._extract_internal_links(html, campaign["target_url"])
                end_ts = start_ts + session_duration

                while pages_visited < pages_to_visit and time.time() < end_ts:
                    remaining = end_ts - time.time()
                    if remaining < 10:
                        break
                    wait = random.uniform(15, min(90, remaining * 0.4))
                    await asyncio.sleep(wait)

                    if not internal_links:
                        break
                    next_url = random.choice(internal_links)
                    try:
                        sub_headers = {"User-Agent": user_agent, "Referer": campaign["target_url"]}
                        sub_status, _ = await loop.run_in_executor(
                            _executor, lambda u=next_url: _sync_get(u, sub_headers, proxy_url)
                        )
                        if sub_status < 400:
                            pages_visited += 1
                            await self._emit_log(
                                campaign["id"], "info",
                                f"  ↳ [{proxy_label}] {next_url} → {sub_status}",
                            )
                    except Exception:
                        pass

                success = True
                if proxy:
                    await self._update_proxy_status(proxy["id"], "active")
            else:
                error_msg = f"HTTP {status}"
                print(f"[BOT FAIL] campaign={campaign['id']} status={status}")
                await self._emit_log(
                    campaign["id"], "warning",
                    f"✗ [{proxy_label}] {campaign['target_url']} → HTTP {status}",
                )
        except asyncio.CancelledError:
            raise
        except Exception as e:
            error_msg = str(e)[:200]
            tb = traceback.format_exc(limit=3)
            print(f"[BOT ERROR] campaign={campaign['id']} proxy={proxy_label} error={error_msg}\n{tb}")
            await self._emit_log(campaign["id"], "error", f"✗ [{proxy_label}] {type(e).__name__}: {error_msg}")
            if proxy and "proxy" in error_msg.lower():
                await self._update_proxy_status(proxy["id"], "dead")

        await self._save_visit(campaign["id"], proxy_id, int(time.time() - start_ts), pages_visited, success, error_msg)

    def _extract_internal_links(self, html: str, base_url: str) -> List[str]:
        try:
            soup = BeautifulSoup(html, "html.parser")
            base_domain = urlparse(base_url).netloc
            links = set()
            for a in soup.find_all("a", href=True):
                full = urljoin(base_url, a["href"])
                parsed = urlparse(full)
                if parsed.netloc == base_domain and parsed.scheme in ("http", "https"):
                    clean = parsed._replace(fragment="").geturl()
                    links.add(clean)
            return list(links)[:25]
        except Exception:
            return []

    async def _update_proxy_status(self, proxy_id: int, status: str):
        if not self._db_factory:
            return
        try:
            async with self._db_factory() as db:
                from models import Proxy as ProxyModel
                from sqlalchemy import select
                result = await db.execute(select(ProxyModel).where(ProxyModel.id == proxy_id))
                p = result.scalar_one_or_none()
                if p:
                    p.status = status
                    p.last_checked = datetime.utcnow()
                    await db.commit()
        except Exception:
            pass

    async def _rank_checker_loop(self, campaign_id: int):
        """Her 6 saatte bir kampanyanın keyword'lerini Google'da kontrol eder."""
        await asyncio.sleep(30)
        prev_ranks: Dict[str, Optional[int]] = {}
        while True:
            try:
                campaign = await self._get_campaign_dict(campaign_id)
                if not campaign:
                    break
                keywords = _get_keywords_list(campaign["keyword"])
                target_domain = urlparse(campaign["target_url"]).netloc
                ua = get_random_ua()
                loop = asyncio.get_event_loop()

                for kw in keywords:
                    try:
                        found, _, rank = await loop.run_in_executor(
                            _executor,
                            lambda k=kw: _sync_google_search(k, target_domain, ua, None),
                        )
                        rank_val = rank if found else None
                        rank_txt = f"{rank}. sıra" if found else "İlk 100'de yok"
                        await self._emit_log(campaign_id, "info",
                            f"📊 Sıralama kontrolü: '{kw}' → {rank_txt}")

                        # Telegram bildirimi
                        prev = prev_ranks.get(kw)
                        if rank_val is not None:
                            if prev is None:
                                msg = (f"🎉 <b>{campaign['name']}</b>\n"
                                       f"'{kw}' artık Google'da <b>{rank_val}. sırada!</b>")
                                await loop.run_in_executor(_executor, lambda m=msg: _send_telegram(m))
                            elif rank_val < prev:
                                msg = (f"📈 <b>{campaign['name']}</b>\n"
                                       f"'{kw}' <b>{prev} → {rank_val}. sıraya</b> yükseldi! 🚀")
                                await loop.run_in_executor(_executor, lambda m=msg: _send_telegram(m))
                            elif rank_val > prev + 3:
                                msg = (f"📉 <b>{campaign['name']}</b>\n"
                                       f"'{kw}' {prev} → {rank_val}. sıraya düştü.")
                                await loop.run_in_executor(_executor, lambda m=msg: _send_telegram(m))
                        prev_ranks[kw] = rank_val

                        if self._db_factory:
                            async with self._db_factory() as db:
                                from models import RankCheck as RankCheckModel
                                db.add(RankCheckModel(
                                    campaign_id=campaign_id,
                                    keyword=kw,
                                    rank=rank_val,
                                ))
                                await db.commit()
                    except Exception:
                        pass
                    await asyncio.sleep(10)
            except asyncio.CancelledError:
                break
            except Exception:
                pass
            await asyncio.sleep(6 * 3600)

    async def _save_visit(self, campaign_id: int, proxy_id: Optional[int], duration: int, pages: int, success: bool, error: Optional[str]):
        if not self._db_factory:
            return
        try:
            async with self._db_factory() as db:
                from models import Campaign as CampaignModel, Visit as VisitModel
                from sqlalchemy import select
                result = await db.execute(select(CampaignModel).where(CampaignModel.id == campaign_id))
                c = result.scalar_one_or_none()
                if c:
                    c.total_visits += 1
                    if success:
                        c.successful_visits += 1
                    else:
                        c.failed_visits += 1
                    c.updated_at = datetime.utcnow()

                db.add(VisitModel(
                    campaign_id=campaign_id,
                    proxy_id=proxy_id,
                    ended_at=datetime.utcnow(),
                    duration_seconds=duration,
                    pages_visited=pages,
                    status="success" if success else "failed",
                    error_message=error,
                ))
                await db.commit()
        except Exception:
            pass
