"""
gsc_engine'i izole test eder.
Çalıştır: python test_browser.py
"""
import asyncio, sys, os
sys.path.insert(0, os.path.join("client", "backend"))

async def fake_log(cid, level, msg):
    print(f"  [{level}] {msg}")

async def main():
    from gsc_engine import browser_visit_session
    campaign = {
        "id": 999,
        "target_url": "https://example.com",
        "keyword": "example",
        "search_engine": "google",
        "session_duration_min": 1,
        "session_duration_max": 1,
        "concurrent_workers": 1,
        "pages_per_session_min": 1,
        "pages_per_session_max": 1,
        "mobile_ratio_pct": 50,
        "bounce_rate_pct": 0,
    }
    print("Browser session başlatılıyor...")
    result = await browser_visit_session(campaign, None, fake_log)
    print(f"\nSonuç: {result}")

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

asyncio.run(main())
