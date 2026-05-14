from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import List, Optional
import asyncio

from database import init_db, get_db, AsyncSessionLocal
from models import (
    Campaign, Proxy, Visit, Log, RankCheck, User,
    CampaignCreate, CampaignUpdate, CampaignResponse,
    ProxyResponse, LogResponse, StatsResponse, RankCheckResponse,
)
from bot_engine import BotEngine, parse_proxy_string
from auth import get_current_user, require_active_license
from routers.auth_router import router as auth_router

app = FastAPI(title="Request Hit Bot API", version="1.0.0")
bot = BotEngine()
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await init_db()
    bot.set_db_factory(AsyncSessionLocal)
    # Restart sonrasi bellekte olmayan "running" kampanyalari sifirla
    async with AsyncSessionLocal() as db:
        await db.execute(update(Campaign).where(Campaign.status == "running").values(status="stopped"))
        await db.commit()


@app.on_event("shutdown")
async def shutdown():
    pass


# ── Campaigns ───────────────────────────────────────────────────────────────────

def _scope(query, user: User, model):
    """Admin tüm verileri görür; user sadece kendininkini."""
    if user.role == "admin":
        return query
    return query.where(model.user_id == user.id)


async def _get_owned_campaign(campaign_id: int, user: User, db: AsyncSession) -> Campaign:
    q = select(Campaign).where(Campaign.id == campaign_id)
    q = _scope(q, user, Campaign)
    c = (await db.execute(q)).scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Kampanya bulunamadı")
    return c


@app.get("/api/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = _scope(select(Campaign), user, Campaign).order_by(Campaign.id.desc())
    campaigns = (await db.execute(q)).scalars().all()
    dirty = False
    for c in campaigns:
        if bot.is_running(c.id) and c.status != "running":
            c.status = "running"
            dirty = True
        elif not bot.is_running(c.id) and c.status == "running":
            c.status = "stopped"
            dirty = True
    if dirty:
        await db.commit()
    return campaigns


@app.post("/api/campaigns", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    data: CampaignCreate,
    user: User = Depends(require_active_license),
    db: AsyncSession = Depends(get_db),
):
    # Plan limitleri
    count = await db.scalar(select(func.count(Campaign.id)).where(Campaign.user_id == user.id)) or 0
    limits = {"free": 1, "pro": 5, "agency": 50}
    if user.role != "admin" and count >= limits.get(user.plan, 1):
        raise HTTPException(403, f"Plan limiti ({limits.get(user.plan, 1)} kampanya). Yükseltin.")

    c = Campaign(**data.model_dump(), user_id=user.id)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


@app.get("/api/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_owned_campaign(campaign_id, user, db)


@app.put("/api/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    data: CampaignUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    c = await _get_owned_campaign(campaign_id, user, db)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(c, field, value)
    await db.commit()
    await db.refresh(c)
    return c


@app.delete("/api/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    c = await _get_owned_campaign(campaign_id, user, db)
    await bot.stop_campaign(campaign_id)
    await db.delete(c)
    await db.commit()
    return {"ok": True}


@app.post("/api/campaigns/{campaign_id}/start")
async def start_campaign(
    campaign_id: int,
    user: User = Depends(require_active_license),
    db: AsyncSession = Depends(get_db),
):
    c = await _get_owned_campaign(campaign_id, user, db)
    c.status = "running"
    await db.commit()
    await bot.start_campaign(campaign_id)
    return {"ok": True, "status": "running"}


@app.post("/api/campaigns/{campaign_id}/stop")
async def stop_campaign(
    campaign_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    c = await _get_owned_campaign(campaign_id, user, db)
    c.status = "stopped"
    await db.commit()
    await bot.stop_campaign(campaign_id)
    return {"ok": True, "status": "stopped"}


# ── Ranks ──────────────────────────────────────────────────────────────────────

@app.get("/api/campaigns/{campaign_id}/ranks", response_model=List[RankCheckResponse])
async def get_campaign_ranks(
    campaign_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_campaign(campaign_id, user, db)
    result = await db.execute(
        select(RankCheck)
        .where(RankCheck.campaign_id == campaign_id)
        .order_by(RankCheck.checked_at.asc())
        .limit(200)
    )
    return result.scalars().all()


# ── Proxies ─────────────────────────────────────────────────────────────────────

@app.get("/api/proxies", response_model=List[ProxyResponse])
async def list_proxies(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = _scope(select(Proxy), user, Proxy).order_by(Proxy.id.desc())
    return (await db.execute(q)).scalars().all()


@app.post("/api/proxies/bulk")
async def add_proxies_bulk(
    data: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    text = data.get("text", "")
    lines = text.strip().splitlines()
    added = 0
    for line in lines:
        parsed = parse_proxy_string(line)
        if parsed:
            parsed["user_id"] = user.id
            db.add(Proxy(**parsed))
            added += 1
    await db.commit()
    return {"added": added}


@app.delete("/api/proxies/all")
async def delete_all_proxies(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = _scope(select(Proxy), user, Proxy)
    for p in (await db.execute(q)).scalars().all():
        await db.delete(p)
    await db.commit()
    return {"ok": True}


@app.delete("/api/proxies/{proxy_id}")
async def delete_proxy(
    proxy_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = _scope(select(Proxy).where(Proxy.id == proxy_id), user, Proxy)
    p = (await db.execute(q)).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Proxy bulunamadı")
    await db.delete(p)
    await db.commit()
    return {"ok": True}


@app.post("/api/proxies/webshare-refresh")
async def webshare_refresh(
    data: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Webshare API'den proxy listesini çekip DB'yi günceller."""
    import json as _json
    import asyncio
    from bot_engine import _executor

    api_key = data.get("api_key", "")
    if not api_key:
        # config.json'dan oku
        try:
            import os
            cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
            with open(cfg_path, encoding="utf-8") as f:
                cfg = _json.load(f)
            api_key = cfg.get("webshare_api_key", "")
        except Exception:
            pass
    if not api_key:
        raise HTTPException(400, "Webshare API anahtarı gerekli — config.json'a 'webshare_api_key' ekle")

    loop = asyncio.get_event_loop()

    def _fetch_webshare(key: str):
        from curl_cffi.requests import Session as CurlSession
        url = "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size=100"
        with CurlSession(impersonate="chrome124") as s:
            r = s.get(url, headers={"Authorization": f"Token {key}"}, timeout=15)
            if r.status_code != 200:
                raise Exception(f"Webshare HTTP {r.status_code}: {r.text[:200]}")
            return r.json()

    try:
        data_ws = await loop.run_in_executor(_executor, _fetch_webshare, api_key)
    except Exception as e:
        raise HTTPException(502, f"Webshare API hatası: {e}")

    proxies_raw = data_ws.get("results", [])
    if not proxies_raw:
        raise HTTPException(404, "Webshare'de proxy bulunamadı")

    # Mevcut proxyleri temizle (sadece bu kullanicininkiler)
    q_del = _scope(select(Proxy), user, Proxy)
    for p in (await db.execute(q_del)).scalars().all():
        await db.delete(p)

    added = 0
    for item in proxies_raw:
        host = item.get("proxy_address") or item.get("address", "")
        port = item.get("port", 0)
        username = item.get("username", "")
        password = item.get("password", "")
        if host and port:
            db.add(Proxy(
                host=host,
                port=int(port),
                username=username or None,
                password=password or None,
                protocol="http",
                status="unknown",
                user_id=user.id,
            ))
            added += 1

    # API key'i config'e kaydet
    try:
        import os
        cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(cfg_path, encoding="utf-8") as f:
            cfg = _json.load(f)
        cfg["webshare_api_key"] = api_key
        with open(cfg_path, "w", encoding="utf-8") as f:
            _json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    await db.commit()
    return {"added": added, "total": len(proxies_raw)}


@app.post("/api/proxies/test-all")
async def test_all_proxies(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Tüm proxyleri paralel test eder, durumlarını günceller."""
    import asyncio
    from bot_engine import _executor
    from datetime import datetime

    q = _scope(select(Proxy), user, Proxy)
    result = await db.execute(q)
    proxies = result.scalars().all()
    if not proxies:
        return {"tested": 0}

    def _test_proxy(host, port, username, password, protocol):
        from curl_cffi.requests import Session as CurlSession
        if username and password:
            proxy_url = f"{protocol}://{username}:{password}@{host}:{port}"
        else:
            proxy_url = f"{protocol}://{host}:{port}"
        try:
            with CurlSession(impersonate="chrome124") as s:
                r = s.get(
                    "https://httpbin.org/ip",
                    proxies={"http": proxy_url, "https": proxy_url},
                    timeout=10,
                )
                return r.status_code == 200
        except Exception:
            return False

    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(
            _executor,
            _test_proxy, p.host, p.port, p.username, p.password, p.protocol
        )
        for p in proxies
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    active = 0
    dead = 0
    for p, ok in zip(proxies, results):
        p.last_checked = datetime.utcnow()
        if ok is True:
            p.status = "active"
            active += 1
        else:
            p.status = "dead"
            dead += 1

    await db.commit()
    return {"tested": len(proxies), "active": active, "dead": dead}


# ── Stats ────────────────────────────────────────────────────────────────────────

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    c_result = await db.execute(_scope(select(Campaign), user, Campaign))
    campaigns = c_result.scalars().all()

    p_result = await db.execute(_scope(select(Proxy), user, Proxy))
    proxies = p_result.scalars().all()

    return {
        "total_campaigns": len(campaigns),
        "running_campaigns": sum(1 for c in campaigns if bot.is_running(c.id)),
        "total_visits": sum(c.total_visits for c in campaigns),
        "successful_visits": sum(c.successful_visits for c in campaigns),
        "total_proxies": len(proxies),
        "active_proxies": sum(1 for p in proxies if p.status == "active"),
    }


@app.get("/api/analytics/hourly")
async def get_hourly_traffic(
    hours: int = 24,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Son N saatte saat başı ziyaret sayısı."""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from models import Visit
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    q = (
        select(
            func.strftime("%Y-%m-%d %H:00", Visit.started_at).label("hour"),
            func.count(Visit.id).label("total"),
            func.sum(func.iif(Visit.status == "success", 1, 0)).label("success"),
        )
        .where(Visit.started_at >= cutoff)
        .group_by("hour")
        .order_by("hour")
    )
    if user.role != "admin":
        camp_ids = (await db.execute(select(Campaign.id).where(Campaign.user_id == user.id))).scalars().all()
        q = q.where(Visit.campaign_id.in_(list(camp_ids)))
    rows = (await db.execute(q)).all()
    return [{"hour": r.hour, "total": r.total, "success": r.success or 0} for r in rows]


@app.get("/api/analytics/proxies")
async def get_proxy_health(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Proxy durumlarının dağılımı."""
    from sqlalchemy import func
    q = select(Proxy.status, func.count(Proxy.id)).group_by(Proxy.status)
    if user.role != "admin":
        q = q.where(Proxy.user_id == user.id)
    result = await db.execute(q)
    return [{"status": r[0], "count": r[1]} for r in result.all()]


@app.get("/api/analytics/referrers")
async def get_referrer_breakdown(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Son 24 saatteki ziyaret status dağılımı."""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from models import Visit
    cutoff = datetime.utcnow() - timedelta(hours=24)
    q = (
        select(Visit.status, func.count(Visit.id))
        .where(Visit.started_at >= cutoff)
        .group_by(Visit.status)
    )
    if user.role != "admin":
        camp_ids = (await db.execute(select(Campaign.id).where(Campaign.user_id == user.id))).scalars().all()
        q = q.where(Visit.campaign_id.in_(list(camp_ids)))
    result = await db.execute(q)
    return [{"status": r[0], "count": r[1]} for r in result.all()]


# ── Logs ─────────────────────────────────────────────────────────────────────────

@app.get("/api/logs", response_model=List[LogResponse])
async def get_logs(
    campaign_id: Optional[int] = None,
    limit: int = 200,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Kullanicinin kampanya id'lerini bul
    if user.role == "admin":
        camp_ids = None  # admin tumu gorur
    else:
        camps = (await db.execute(select(Campaign.id).where(Campaign.user_id == user.id))).scalars().all()
        camp_ids = list(camps)

    q = select(Log).order_by(Log.id.desc()).limit(limit)
    if campaign_id is not None:
        # Sahiplik kontrolu
        if camp_ids is not None and campaign_id not in camp_ids:
            raise HTTPException(403, "Bu kampanyaya erisim yetkiniz yok")
        q = q.where(Log.campaign_id == campaign_id)
    elif camp_ids is not None:
        q = q.where(Log.campaign_id.in_(camp_ids))

    result = await db.execute(q)
    logs = result.scalars().all()
    return list(reversed(logs))


# ── WebSocket (live logs) ────────────────────────────────────────────────────────

@app.websocket("/ws/logs")
async def ws_logs(websocket: WebSocket):
    await websocket.accept()

    async def send_log(log_data: dict):
        try:
            await websocket.send_json(log_data)
        except Exception:
            pass

    unsubscribe = bot.subscribe_logs(send_log)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        unsubscribe()
