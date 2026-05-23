"""
GSC Browser Mode — Playwright sync API ile Google araması ve tıklama.
sync_playwright thread içinde event loop gerektirmez → Windows'ta sorunsuz çalışır.
"""
import random
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Callable, Awaitable, List, Tuple
from urllib.parse import urlparse

_browser_executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="gsc_browser")

VIEWPORT_SIZES = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1280, "height": 800},
    {"width": 1536, "height": 864},
]

MOBILE_VIEWPORTS = [
    {"width": 390, "height": 844},
    {"width": 414, "height": 896},
    {"width": 412, "height": 915},
    {"width": 360, "height": 800},
]

STEALTH_SCRIPT = """
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
    Object.defineProperty(navigator, 'languages', { get: () => ['tr-TR', 'tr', 'en-US', 'en'] });
    window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){}, app: {} };
    Object.defineProperty(navigator, 'permissions', {
        get: () => ({ query: (p) => Promise.resolve({ state: p.name === 'notifications' ? 'denied' : 'granted' }) })
    });
    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
    Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
    delete navigator.__proto__.webdriver;
"""

DEFAULT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

_SKIP_PROTO = ("mailto:", "tel:", "whatsapp:", "sms:", "javascript:", "viber:", "callto:")


def _build_proxy_config(proxy: Optional[Dict]) -> Optional[Dict]:
    if not proxy:
        return None
    cfg = {"server": f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}"}
    if proxy.get("username"):
        cfg["username"] = proxy["username"]
    if proxy.get("password"):
        cfg["password"] = proxy["password"]
    return cfg


def _human_type_sync(page, selector: str, text: str):
    el = page.locator(selector).first
    el.click()
    time.sleep(random.uniform(0.3, 0.7))
    for ch in text:
        page.keyboard.type(ch, delay=random.randint(60, 180))
    time.sleep(random.uniform(0.2, 0.5))


def _scroll_sync(page, steps: int = 4):
    for _ in range(steps):
        page.mouse.wheel(0, random.randint(200, 600))
        time.sleep(random.uniform(0.4, 1.2))


def _human_mouse_move(page, target_x: int, target_y: int):
    """Mouse'u mevcut konumdan hedefe insanca hareket ettirir (bezier benzeri)."""
    steps = random.randint(8, 16)
    start_x = random.randint(200, 800)
    start_y = random.randint(200, 500)
    for i in range(steps + 1):
        t = i / steps
        # ease-in-out
        t2 = t * t * (3 - 2 * t)
        x = int(start_x + (target_x - start_x) * t2)
        y = int(start_y + (target_y - start_y) * t2)
        page.mouse.move(x + random.randint(-3, 3), y + random.randint(-3, 3))
        time.sleep(random.uniform(0.01, 0.04))


def _run_browser_sync(campaign: Dict, proxy: Optional[Dict]) -> Dict:
    """
    sync_playwright kullanarak Google araması ve site ziyareti yapar.
    Thread içinde çağrılır — event loop gerekmez.
    Returns: {"success", "pages_visited", "rank", "error", "logs": [(cid, level, msg)]}
    """
    logs: List[Tuple] = []

    def log(level: str, msg: str):
        logs.append((campaign["id"], level, msg))
        print(f"[GSC {level.upper()}] {msg}")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"success": False, "pages_visited": 0, "rank": 0, "logs": logs,
                "error": "Playwright kurulu değil — pip install playwright && playwright install chromium"}

    target_url = campaign["target_url"]
    target_domain = urlparse(target_url).netloc.replace("www.", "")
    keywords_raw = campaign.get("keyword", "") or ""
    keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
    keyword = random.choice(keywords) if keywords else None

    is_mobile = random.randint(1, 100) <= campaign.get("mobile_ratio_pct", 65)
    viewport = random.choice(MOBILE_VIEWPORTS if is_mobile else VIEWPORT_SIZES)
    device_tag = "📱" if is_mobile else "💻"

    try:
        from bot_engine import get_random_ua
        user_agent = get_random_ua(mobile_pct=100 if is_mobile else 0)
    except Exception:
        user_agent = DEFAULT_UA

    proxy_label = f"{proxy['host']}:{proxy['port']}" if proxy else "direkt"
    proxy_config = _build_proxy_config(proxy)

    pages_visited = 0
    rank_found = 0
    success = False
    error_msg = None

    try:
        with sync_playwright() as pw:
            launch_kwargs = {
                "headless": True,
                "args": [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-extensions",
                    "--disable-infobars",
                    "--disable-popup-blocking",
                    "--disable-external-protocol-handler-gestures",
                    "--disable-external-protocol-handlers",
                    "--lang=tr-TR,tr",
                    "--window-size=1920,1080",
                    "--disable-background-timer-throttling",
                    "--disable-renderer-backgrounding",
                    "--disable-backgrounding-occluded-windows",
                ],
            }
            if proxy_config:
                launch_kwargs["proxy"] = proxy_config

            browser = pw.chromium.launch(**launch_kwargs)

            context_kwargs = {
                "viewport": viewport,
                "user_agent": user_agent,
                "locale": "tr-TR",
                "timezone_id": "Europe/Istanbul",
                "color_scheme": "light",
            }
            if is_mobile:
                context_kwargs["is_mobile"] = True
                context_kwargs["has_touch"] = True

            context = browser.new_context(**context_kwargs)
            context.add_init_script(STEALTH_SCRIPT)
            page = context.new_page()

            # Google'a git
            page.goto("https://www.google.com", wait_until="domcontentloaded", timeout=30000)
            time.sleep(random.uniform(0.8, 1.5))

            # Çerez popup — Google measurement için cookie zorunlu
            for selector in ["button:has-text('Kabul et')", "button:has-text('Accept all')",
                              "#L2AGLb", "[aria-label='Accept all']",
                              "button:has-text('Tümünü kabul et')",
                              "[jsname='b3VHJd']"]:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=2000):
                        bbox = btn.bounding_box()
                        if bbox:
                            _human_mouse_move(page, int(bbox["x"] + bbox["width"] / 2),
                                              int(bbox["y"] + bbox["height"] / 2))
                        btn.click()
                        time.sleep(random.uniform(0.8, 1.5))
                        break
                except Exception:
                    pass

            if not keyword:
                page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(random.uniform(1.5, 3.0))
                _scroll_sync(page)
                pages_visited = 1
                success = True
                log("info", f"✓ {device_tag} [{proxy_label}] Direkt ziyaret → {target_url}")
            else:
                # Keyword ara
                search_sel = 'textarea[name="q"], input[name="q"]'
                _human_type_sync(page, search_sel, keyword)
                page.keyboard.press("Enter")
                page.wait_for_load_state("domcontentloaded", timeout=20000)
                time.sleep(random.uniform(1.0, 2.0))

                # CAPTCHA kontrolü
                content = page.content()
                if "recaptcha" in content.lower() or "unusual traffic" in content.lower():
                    browser.close()
                    log("warning", f"🚧 {device_tag} [{proxy_label}] Google CAPTCHA tespit edildi")
                    return {"success": False, "pages_visited": 0, "rank": 0,
                            "logs": logs, "error": f"[{proxy_label}] Google CAPTCHA"}

                # Hedef linki bul (max 3 SERP sayfası)
                found_link = None
                current_rank = 0
                for _ in range(3):
                    h3s = page.locator("h3").all()
                    for h3 in h3s:
                        current_rank += 1
                        try:
                            parent_a = h3.locator("xpath=ancestor::a[1]")
                            href = parent_a.get_attribute("href", timeout=1000) or ""
                            if target_domain in href:
                                found_link = parent_a
                                rank_found = current_rank
                                break
                        except Exception:
                            continue
                    if found_link:
                        break
                    next_btn = page.locator("#pnnext, a[aria-label='Next page']").first
                    try:
                        if next_btn.is_visible(timeout=2000):
                            next_btn.click()
                            page.wait_for_load_state("domcontentloaded", timeout=15000)
                            time.sleep(random.uniform(1.0, 2.0))
                        else:
                            break
                    except Exception:
                        break

                if not found_link:
                    browser.close()
                    log("warning", f"⚠️ {device_tag} [{proxy_label}] '{keyword}' → hedef bulunamadı")
                    return {"success": False, "pages_visited": 0, "rank": 0,
                            "logs": logs, "error": "Sıralamada yok"}

                log("info", f"🔍 {device_tag} [{proxy_label}] '{keyword}' → {rank_found}. sıra bulundu, tıklanıyor…")

                # Sonuca scroll et, biraz bekle (okuyormuş gibi), sonra mouse hareketiyle tıkla
                found_link.scroll_into_view_if_needed()
                time.sleep(random.uniform(0.8, 2.0))
                try:
                    bbox = found_link.bounding_box()
                    if bbox:
                        tx = int(bbox["x"] + bbox["width"] * random.uniform(0.2, 0.8))
                        ty = int(bbox["y"] + bbox["height"] * random.uniform(0.2, 0.8))
                        _human_mouse_move(page, tx, ty)
                        time.sleep(random.uniform(0.1, 0.3))
                        page.mouse.click(tx, ty)
                    else:
                        found_link.click()
                except Exception:
                    found_link.click()
                page.wait_for_load_state("domcontentloaded", timeout=30000)
                pages_visited = 1
                log("info", f"✓ {device_tag} [{proxy_label}] Sitede → {page.url}")

            # Site içi gezinme
            session_duration = random.randint(
                campaign.get("session_duration_min", 3) * 60,
                campaign.get("session_duration_max", 8) * 60,
            )
            pages_target = random.randint(
                campaign.get("pages_per_session_min", 1),
                campaign.get("pages_per_session_max", 4),
            )
            bounce_pct = campaign.get("bounce_rate_pct", 30)
            if random.randint(1, 100) <= bounce_pct:
                session_duration = random.randint(5, 25)
                pages_target = 1

            end_ts = time.time() + session_duration
            _scroll_sync(page)

            while pages_visited < pages_target and time.time() < end_ts:
                remaining = end_ts - time.time()
                if remaining < 8:
                    break
                wait = random.uniform(10, min(60, remaining * 0.4))
                time.sleep(wait)
                try:
                    internal_links = page.locator(
                        f'a[href*="{target_domain}"], a[href^="/"]'
                    ).all()
                    valid_links = []
                    for _l in internal_links[:20]:
                        try:
                            _h = (_l.get_attribute("href", timeout=400) or "").strip()
                            if _h and _h != "#" and not _h.startswith(_SKIP_PROTO):
                                valid_links.append((_l, _h))
                        except Exception:
                            pass
                    if not valid_links:
                        break
                    link, href = random.choice(valid_links)
                    if href and not href.startswith("javascript"):
                        link.scroll_into_view_if_needed()
                        time.sleep(random.uniform(0.3, 0.8))
                        link.click()
                        page.wait_for_load_state("domcontentloaded", timeout=20000)
                        pages_visited += 1
                        _scroll_sync(page, steps=random.randint(2, 5))
                        log("info", f"  ↳ {device_tag} [{proxy_label}] {page.url}")
                except Exception:
                    break

            success = True
            browser.close()

    except Exception as e:
        tb_str = traceback.format_exc(limit=5)
        error_msg = (repr(e) + " | " + tb_str.strip().splitlines()[-1])[:300]
        print(f"[GSC ERROR] {repr(e)}\n{tb_str}")
        log("error", f"💥 Browser Mode hatası [{proxy_label}]: {error_msg}")

    return {
        "success": success,
        "pages_visited": pages_visited,
        "rank": rank_found,
        "logs": logs,
        "error": error_msg,
    }


async def browser_visit_session(
    campaign: Dict,
    proxy: Optional[Dict],
    emit_log: Callable[..., Awaitable],
) -> Dict:
    """
    Ana coroutine — sync Playwright'ı thread pool'da çalıştırır,
    logları ana event loop'ta emit eder.
    """
    import asyncio
    try:
        from playwright.sync_api import sync_playwright  # noqa import check
    except ImportError:
        return {"success": False, "pages_visited": 0, "rank": 0,
                "error": "Playwright kurulu değil"}

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        _browser_executor,
        lambda: _run_browser_sync(campaign, proxy),
    )

    for cid, level, msg in result.pop("logs", []):
        await emit_log(cid, level, msg)

    return result
