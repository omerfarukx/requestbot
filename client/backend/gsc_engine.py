"""
GSC Browser Mode — Playwright sync API ile Google araması ve tıklama.
sync_playwright thread içinde event loop gerektirmez → Windows'ta sorunsuz çalışır.
Gelişmiş: human mouse (Bezier), profil kalıcılığı, doğal scroll, dwell time, CTR simülasyonu.
"""
import random
import time
import os
import tempfile
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Callable, Awaitable, List, Tuple
from urllib.parse import urlparse

_browser_executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="gsc_browser")

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
(function() {
    // webdriver bayrağını gizle
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    try { delete navigator.__proto__.webdriver; } catch(e) {}

    // Plugin listesi — gerçek Chrome gibi
    const pluginData = [
        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
        { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
    ];
    const pluginArray = pluginData.map(p => {
        const plugin = Object.create(Plugin.prototype);
        Object.defineProperties(plugin, {
            name:        { value: p.name,        enumerable: true },
            filename:    { value: p.filename,    enumerable: true },
            description: { value: p.description, enumerable: true },
            length:      { value: 0,             enumerable: true },
        });
        return plugin;
    });
    pluginArray.item = (i) => pluginArray[i];
    pluginArray.namedItem = (name) => pluginArray.find(p => p.name === name) || null;
    pluginArray.refresh = () => {};
    Object.defineProperty(pluginArray, 'length', { value: pluginArray.length });
    Object.defineProperty(navigator, 'plugins', { get: () => pluginArray });

    // Diller
    Object.defineProperty(navigator, 'languages', { get: () => ['tr-TR', 'tr', 'en-US', 'en'] });

    // Chrome runtime nesnesi
    window.chrome = {
        runtime: {
            connect: () => {},
            sendMessage: () => {},
            id: undefined,
        },
        loadTimes: function() {
            return { requestTime: Date.now() / 1000 - Math.random() * 2, startLoadTime: Date.now() / 1000 };
        },
        csi: function() { return { startE: Date.now() - 500, onloadT: Date.now() }; },
        app: {
            isInstalled: false,
            getDetails: function() { return null; },
            getIsInstalled: function() { return false; },
            installState: function() {},
            runningState: function() { return 'cannot_run'; },
        },
    };

    // Permissions
    try {
        const origQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : origQuery.call(window.navigator.permissions, parameters)
        );
    } catch(e) {}

    // Donanım bilgileri
    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
    Object.defineProperty(navigator, 'deviceMemory',        { get: () => 8 });
    Object.defineProperty(navigator, 'maxTouchPoints',      { get: () => 0 });

    // Bağlantı
    Object.defineProperty(navigator, 'connection', {
        get: () => ({ effectiveType: '4g', downlink: 10, rtt: 50, saveData: false })
    });

    // Ekran rengi
    Object.defineProperty(screen, 'colorDepth', { get: () => 24 });
    Object.defineProperty(screen, 'pixelDepth', { get: () => 24 });

    // WebGL vendor/renderer sahte değerleri
    try {
        const getParam = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(p) {
            if (p === 37445) return 'Intel Inc.';
            if (p === 37446) return 'Intel Iris OpenGL Engine';
            return getParam.call(this, p);
        };
        const getParam2 = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(p) {
            if (p === 37445) return 'Intel Inc.';
            if (p === 37446) return 'Intel Iris OpenGL Engine';
            return getParam2.call(this, p);
        };
    } catch(e) {}

    // toString sahteciliğini önle
    const origToString = Function.prototype.toString;
    Function.prototype.toString = function() {
        if (this === window.chrome.runtime.connect) return 'function connect() { [native code] }';
        return origToString.call(this);
    };
})();
"""

DEFAULT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

_PROFILES_BASE = os.path.join(tempfile.gettempdir(), "rhb_profiles")


def _get_profile_state_path(campaign_id: int) -> str:
    """Kampanya başına 5 farklı profil slotu — döngüsel kullanım."""
    os.makedirs(_PROFILES_BASE, exist_ok=True)
    slot = random.randint(0, 4)
    return os.path.join(_PROFILES_BASE, f"c{campaign_id}_s{slot}_state.json")


def _build_proxy_config(proxy: Optional[Dict]) -> Optional[Dict]:
    if not proxy:
        return None
    cfg = {"server": f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}"}
    if proxy.get("username"):
        cfg["username"] = proxy["username"]
    if proxy.get("password"):
        cfg["password"] = proxy["password"]
    return cfg


# ── Human behavior helpers ────────────────────────────────────────────────────

def _bezier(p0, p1, p2, p3, t):
    """Cubic Bezier eğrisi noktası."""
    u = 1 - t
    return (
        u**3 * p0[0] + 3*u**2*t * p1[0] + 3*u*t**2 * p2[0] + t**3 * p3[0],
        u**3 * p0[1] + 3*u**2*t * p1[1] + 3*u*t**2 * p2[1] + t**3 * p3[1],
    )


def _human_mouse_move(page, tx: int, ty: int, sx: int = None, sy: int = None):
    """Bezier eğrisiyle doğal mouse hareketi."""
    vp = page.viewport_size or {"width": 1280, "height": 720}
    sx = sx if sx is not None else random.randint(80, vp["width"] - 80)
    sy = sy if sy is not None else random.randint(80, vp["height"] - 80)
    cp1 = (sx + random.randint(-220, 220), sy + random.randint(-120, 120))
    cp2 = (tx + random.randint(-180, 180), ty + random.randint(-120, 120))
    steps = random.randint(18, 32)
    for i in range(steps + 1):
        t = i / steps
        t_e = t * t * (3 - 2 * t)          # ease-in-out
        x, y = _bezier((sx, sy), cp1, cp2, (tx, ty), t_e)
        page.mouse.move(int(x), int(y))
        time.sleep(random.uniform(0.004, 0.018))


def _human_click_element(page, element):
    """Elemente Bezier mouse hareketiyle tıkla."""
    try:
        box = element.bounding_box(timeout=2000)
        if box:
            cx = int(box["x"] + box["width"]  * random.uniform(0.25, 0.75))
            cy = int(box["y"] + box["height"] * random.uniform(0.25, 0.75))
            _human_mouse_move(page, cx, cy)
            time.sleep(random.uniform(0.08, 0.25))
            page.mouse.down()
            time.sleep(random.uniform(0.04, 0.12))
            page.mouse.up()
            return
    except Exception:
        pass
    element.click()


def _human_type(page, text: str):
    """Karakter karakter, değişken hızlı yazma."""
    for ch in text:
        page.keyboard.type(ch, delay=random.randint(85, 230))
        if random.random() < 0.05:
            time.sleep(random.uniform(0.3, 0.9))
    time.sleep(random.uniform(0.4, 1.0))


def _scroll_natural(page, steps: int = None):
    """Değişken hızlı, arada geri giden doğal scroll."""
    if steps is None:
        steps = random.randint(3, 7)
    for _ in range(steps):
        page.mouse.wheel(0, random.randint(120, 500))
        time.sleep(random.uniform(0.15, 0.7))
        if random.random() < 0.12:
            page.mouse.wheel(0, -random.randint(40, 120))
            time.sleep(random.uniform(0.2, 0.5))


def _reading_pause(page):
    """Sayfada okuma simülasyonu — hafif mouse hareketiyle."""
    vp = page.viewport_size or {"width": 1280, "height": 720}
    pauses = random.randint(2, 5)
    for _ in range(pauses):
        page.mouse.move(
            random.randint(60, vp["width"] - 60),
            random.randint(60, vp["height"] - 60),
        )
        time.sleep(random.uniform(1.5, 4.5))


def _idle_behavior(page, duration: float):
    """Verilen süre boyunca scroll + mouse ile aktif bekleme."""
    end = time.time() + duration
    vp = page.viewport_size or {"width": 1280, "height": 720}
    while time.time() < end:
        r = random.random()
        if r < 0.30:
            page.mouse.wheel(0, random.randint(-80, 250))
            time.sleep(random.uniform(0.5, 2.0))
        elif r < 0.55:
            page.mouse.move(
                random.randint(50, vp["width"] - 50),
                random.randint(50, vp["height"] - 50),
            )
            time.sleep(random.uniform(0.3, 1.5))
        else:
            time.sleep(random.uniform(1.0, 3.5))


# ── Core browser session ───────────────────────────────────────────────────────

def _run_browser_sync(campaign: Dict, proxy: Optional[Dict]) -> Dict:
    """
    sync_playwright kullanarak Google araması ve site ziyareti yapar.
    Thread içinde çağrılır — event loop gerekmez.
    Returns: {"success", "pages_visited", "rank", "error", "logs": [(cid, level, msg)]}
    """
    logs: List[Tuple] = []

    def _safe_print(s: str):
        try:
            print(s)
        except UnicodeEncodeError:
            print(s.encode("ascii", "replace").decode("ascii"))

    def log(level: str, msg: str):
        logs.append((campaign["id"], level, msg))
        _safe_print(f"[GSC {level.upper()}] {msg}")

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
    state_path = _get_profile_state_path(campaign["id"])

    pages_visited = 0
    rank_found = 0
    success = False
    error_msg = None

    try:
        with sync_playwright() as pw:
            launch_kwargs = {
                "headless": False,
                "args": [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--disable-extensions",
                    "--disable-infobars",
                    "--disable-popup-blocking",
                    "--lang=tr-TR,tr",
                    "--disable-background-timer-throttling",
                    "--disable-renderer-backgrounding",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-ipc-flooding-protection",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--window-position=0,0",
                    f"--window-size={viewport['width']},{viewport['height']}",
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

            # Kalıcı profil state — cookie/localStorage yüklenir
            if os.path.exists(state_path):
                try:
                    context_kwargs["storage_state"] = state_path
                except Exception:
                    pass

            context = browser.new_context(**context_kwargs)
            context.add_init_script(STEALTH_SCRIPT)
            page = context.new_page()

            # Proxy üzerinden gereksiz medya yükleme — bandwidth tasarrufu ~%70
            BLOCK_TYPES = {"image", "media", "font", "other"}
            BLOCK_DOMAINS = {"googlevideo.com", "gstatic.com", "ytimg.com", "doubleclick.net"}
            def _route_handler(route):
                try:
                    rt = route.request.resource_type
                    url = route.request.url
                    if rt in BLOCK_TYPES and not any(d in url for d in ("google.com", "googleusercontent.com")):
                        route.abort()
                        return
                    if any(d in url for d in BLOCK_DOMAINS):
                        route.abort()
                        return
                except Exception:
                    pass
                route.continue_()
            page.route("**/*", _route_handler)

            # Analytics/tracker'ların görmesi için gerçekçi header'lar
            page.set_extra_http_headers({
                "Accept":                    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language":           "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding":           "gzip, deflate, br",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest":            "document",
                "Sec-Fetch-Mode":            "navigate",
                "Sec-Fetch-Site":            "none",
                "Sec-Fetch-User":            "?1",
            })

            # ── Google'a git ────────────────────────────────────────────────
            page.goto("https://www.google.com", wait_until="domcontentloaded", timeout=30000)
            time.sleep(random.uniform(1.2, 2.8))

            # Çerez popup
            for selector in [
                "button:has-text('Kabul et')", "button:has-text('Tümünü kabul et')",
                "button:has-text('Accept all')", "#L2AGLb",
                "[aria-label='Accept all']", "[aria-label='Tümünü kabul et']",
            ]:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=1500):
                        _human_click_element(page, btn)
                        time.sleep(random.uniform(0.6, 1.3))
                        break
                except Exception:
                    pass

            # ── Direkt ziyaret (keyword yok) ────────────────────────────────
            if not keyword:
                page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(random.uniform(2.0, 4.0))
                _scroll_natural(page)
                _reading_pause(page)
                pages_visited = 1
                success = True
                log("info", f"✓ {device_tag} [{proxy_label}] Direkt ziyaret → {target_url}")

            else:
                # ── Google araması ──────────────────────────────────────────
                search_sel = 'textarea[name="q"], input[name="q"]'
                try:
                    sb = page.locator(search_sel).first
                    _human_click_element(page, sb)
                except Exception:
                    pass
                time.sleep(random.uniform(0.5, 1.0))
                _human_type(page, keyword)
                page.keyboard.press("Enter")
                page.wait_for_load_state("domcontentloaded", timeout=20000)
                time.sleep(random.uniform(1.8, 3.5))

                # CAPTCHA kontrolü — sayfa hâlâ yükleniyorsa bekle
                content = ""
                for _ct in range(3):
                    try:
                        page.wait_for_load_state("networkidle", timeout=8000)
                        content = page.content()
                        break
                    except Exception:
                        time.sleep(1)
                # Gerçek CAPTCHA tespiti — URL bazlı (false positive önlemi)
                _cur_url = page.url
                _is_captcha = (
                    "/sorry/" in _cur_url
                    or "google.com/sorry" in _cur_url
                    or "unusual traffic" in content.lower()
                    or 'id="captcha-form"' in content
                    or 'name="captcha"' in content
                )
                if _is_captcha:
                    _save_state(context, state_path)
                    browser.close()
                    log("warning", f"🚧 {device_tag} [{proxy_label}] Google CAPTCHA tespit edildi")
                    return {"success": False, "pages_visited": 0, "rank": 0,
                            "logs": logs, "error": f"CAPTCHA:[{proxy_label}]"}

                # Sonuçların yüklenmesini bekle
                try:
                    page.wait_for_selector("#search, #rso, .g", timeout=10000)
                except Exception:
                    pass
                time.sleep(random.uniform(1.0, 2.0))

                # SERP'de gerçekçi scroll
                _scroll_natural(page, steps=random.randint(2, 4))
                time.sleep(random.uniform(0.8, 1.8))

                # Hedef linki bul (max 3 SERP sayfası)
                # Yöntem 1: doğrudan href içinde domain ara (en güvenilir)
                # Yöntem 2: h3 → ancestor::a (fallback)
                found_link = None
                current_rank = 0
                for _page_num in range(3):
                    # --- Yöntem 1: CSS href selector ---
                    try:
                        direct_links = page.locator(
                            f'a[href*="{target_domain}"]'
                        ).all()
                        for lnk in direct_links:
                            try:
                                href = lnk.get_attribute("href", timeout=500) or ""
                                # Google /search, /imgres vb. iç linklerini atla
                                if target_domain in href and not href.startswith("/search"):
                                    current_rank += 1
                                    found_link = lnk
                                    rank_found = current_rank
                                    break
                            except Exception:
                                continue
                    except Exception:
                        pass

                    # --- Yöntem 2: h3 → ancestor::a (fallback) ---
                    if not found_link:
                        h3s = page.locator("h3").all()
                        for h3 in h3s:
                            current_rank += 1
                            try:
                                parent_a = h3.locator("xpath=ancestor::a[1]")
                                href = parent_a.get_attribute("href", timeout=800) or ""
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
                            _human_click_element(page, next_btn)
                            page.wait_for_load_state("domcontentloaded", timeout=15000)
                            time.sleep(random.uniform(1.5, 3.0))
                        else:
                            break
                    except Exception:
                        break

                # Rastgele başka bir sonuca kısa bak — rank tespitinden SONRA
                if not found_link:
                    try:
                        other_links = page.locator("h3").all()
                        if other_links and len(other_links) > 1:
                            decoy = random.choice(other_links[:min(5, len(other_links))])
                            _human_click_element(page, decoy)
                            time.sleep(random.uniform(0.3, 0.6))
                            page.go_back()
                            page.wait_for_load_state("domcontentloaded", timeout=10000)
                            time.sleep(random.uniform(0.8, 1.5))
                    except Exception:
                        pass

                if not found_link:
                    # Sıralamada yok ama direkt ziyaret yap — analytics'e yine de sayılır
                    log("warning", f"⚠️ {device_tag} [{proxy_label}] '{keyword}' → sıralamada yok, direkt ziyaret yapılıyor")
                    page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_load_state("networkidle", timeout=10000)
                    _scroll_natural(page, steps=random.randint(3, 6))
                    _reading_pause(page)
                    _idle_behavior(page, random.uniform(15, 30))
                    pages_visited += 1
                    _save_state(context, state_path)
                    browser.close()
                    log("info", f"✓ {device_tag} [{proxy_label}] Direkt ziyaret tamamlandı → {target_url}")
                    return {"success": True, "pages_visited": pages_visited, "rank": 0,
                            "logs": logs, "error": None}

                log("info", f"🔍 {device_tag} [{proxy_label}] '{keyword}' → {rank_found}. sıra, tıklanıyor…")

                found_link.scroll_into_view_if_needed()
                time.sleep(random.uniform(0.6, 1.8))
                _human_click_element(page, found_link)
                page.wait_for_load_state("domcontentloaded", timeout=30000)
                pages_visited = 1
                log("info", f"✓ {device_tag} [{proxy_label}] Sitede → {page.url}")

            # ── Dwell time + site içi gezinme ──────────────────────────────
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
                session_duration = random.randint(10, 40)
                pages_target = 1

            end_ts = time.time() + session_duration

            # İlk sayfada oku
            _scroll_natural(page)
            _reading_pause(page)

            while pages_visited < pages_target and time.time() < end_ts:
                remaining = end_ts - time.time()
                if remaining < 10:
                    break
                idle_t = random.uniform(10, min(50, remaining * 0.45))
                _idle_behavior(page, idle_t)

                try:
                    internal_links = page.locator(
                        f'a[href*="{target_domain}"], a[href^="/"]'
                    ).all()
                    internal_links = [
                        lnk for lnk in internal_links
                        if lnk.get_attribute("href", timeout=500) not in ("", "#", None)
                    ]
                    if not internal_links:
                        break
                    link = random.choice(internal_links[:15])
                    href = link.get_attribute("href", timeout=500) or ""
                    if href and not href.startswith("javascript"):
                        link.scroll_into_view_if_needed()
                        time.sleep(random.uniform(0.3, 0.9))
                        _human_click_element(page, link)
                        page.wait_for_load_state("domcontentloaded", timeout=20000)
                        pages_visited += 1
                        _scroll_natural(page, steps=random.randint(2, 5))
                        _reading_pause(page)
                        log("info", f"  ↳ {device_tag} [{proxy_label}] {page.url}")
                except Exception:
                    break

            # Profil state kaydet — bir sonraki ziyarette cookie'ler yüklenir
            _save_state(context, state_path)
            success = True
            browser.close()

    except Exception as e:
        tb_str = traceback.format_exc(limit=5)
        error_msg = (repr(e) + " | " + tb_str.strip().splitlines()[-1])[:300]
        _safe_print(f"[GSC ERROR] {repr(e)}\n{tb_str}")
        log("error", f"💥 Browser Mode hatası [{proxy_label}]: {error_msg}")

    return {
        "success": success,
        "pages_visited": pages_visited,
        "rank": rank_found,
        "logs": logs,
        "error": error_msg,
    }


def _save_state(context, path: str):
    """Browser context state'ini diske kaydet (cookie + localStorage)."""
    try:
        context.storage_state(path=path)
    except Exception:
        pass


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
