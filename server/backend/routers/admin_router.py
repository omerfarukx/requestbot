"""Admin endpointleri."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, Device, Order, ActivityLog, PageView, UserResponse, AdminUserUpdate
from auth import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/site-stats")
async def site_stats(_: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    """Site geneli trafik ve kullanici istatistikleri."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    d7  = now - timedelta(days=7)
    d30 = now - timedelta(days=30)

    async def pv_count(since=None):
        q = select(func.count(PageView.id))
        if since:
            q = q.where(PageView.created_at >= since)
        return await db.scalar(q) or 0

    async def pv_unique(since=None):
        q = select(func.count(func.distinct(PageView.ip)))
        if since:
            q = q.where(PageView.created_at >= since)
        return await db.scalar(q) or 0

    async def ev_count(event, since=None):
        q = select(func.count(ActivityLog.id)).where(ActivityLog.event == event)
        if since:
            q = q.where(ActivityLog.created_at >= since)
        return await db.scalar(q) or 0

    top_paths_res = await db.execute(
        select(PageView.path, func.count(PageView.id).label("cnt"))
        .group_by(PageView.path)
        .order_by(func.count(PageView.id).desc())
        .limit(10)
    )
    top_paths = [{"path": r.path, "count": r.cnt} for r in top_paths_res]

    daily_res = await db.execute(
        select(
            func.strftime("%Y-%m-%d", PageView.created_at).label("day"),
            func.count(PageView.id).label("cnt"),
        )
        .where(PageView.created_at >= d30)
        .group_by(func.strftime("%Y-%m-%d", PageView.created_at))
        .order_by(func.strftime("%Y-%m-%d", PageView.created_at))
    )
    daily = [{"day": r.day, "count": r.cnt} for r in daily_res]

    return {
        "page_views": {
            "total": await pv_count(),
            "last_7d": await pv_count(d7),
            "last_30d": await pv_count(d30),
            "unique_ips_total": await pv_unique(),
            "unique_ips_7d": await pv_unique(d7),
        },
        "events": {
            "registrations_total": await ev_count("register"),
            "registrations_7d": await ev_count("register", d7),
            "logins_total": await ev_count("login"),
            "logins_7d": await ev_count("login", d7),
            "downloads_total": await ev_count("download"),
            "downloads_7d": await ev_count("download", d7),
            "bot_sessions_total": await ev_count("bot_session"),
            "bot_sessions_7d": await ev_count("bot_session", d7),
        },
        "top_pages": top_paths,
        "daily_views": daily,
    }


@router.get("/users", response_model=list[UserResponse])
async def list_users(_: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).order_by(User.id.desc()))
    return res.scalars().all()


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: AdminUserUpdate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    u = await db.get(User, user_id)
    if not u:
        raise HTTPException(404, "Kullanici bulunamadi")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(u, k, v)
    await db.commit()
    await db.refresh(u)
    return u


@router.post("/users/{user_id}/extend")
async def extend_license(
    user_id: int,
    days: int = 30,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    u = await db.get(User, user_id)
    if not u:
        raise HTTPException(404, "Kullanici bulunamadi")
    _now = datetime.now(timezone.utc).replace(tzinfo=None)
    base = u.license_expires_at if (u.license_expires_at and u.license_expires_at >= _now) else _now
    u.license_expires_at = base + timedelta(days=days)
    if u.plan == "free":
        u.plan = "pro"
    await db.commit()
    return {"ok": True, "new_expiry": u.license_expires_at}


@router.post("/users/{user_id}/grant-reset")
async def grant_reset_credit(
    user_id: int,
    count: int = 1,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Manuel cihaz sifirlama hakki ver (destek talebi vs.)."""
    u = await db.get(User, user_id)
    if not u:
        raise HTTPException(404, "Kullanici bulunamadi")
    u.reset_credits += count
    await db.commit()
    return {"ok": True, "reset_credits": u.reset_credits}


@router.get("/orders")
async def list_orders(
    status: str = "pending",
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Bekleyen/tamamlanan siparisleri listele."""
    q = (
        select(Order, User.username, User.email)
        .join(User, Order.user_id == User.id)
        .where(Order.status == status)
        .order_by(Order.created_at.desc())
    )
    rows = (await db.execute(q)).all()
    return [
        {
            "id": o.id,
            "merchant_oid": o.merchant_oid,
            "product": o.product,
            "amount_tl": round(o.amount_kurus / 100, 2),
            "status": o.status,
            "user_id": o.user_id,
            "username": username,
            "email": email,
            "created_at": o.created_at.isoformat(),
        }
        for o, username, email in rows
    ]


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == current.id:
        raise HTTPException(400, "Kendinizi silemezsiniz")
    u = await db.get(User, user_id)
    if not u:
        raise HTTPException(404, "Kullanici bulunamadi")
    await db.delete(u)
    await db.commit()
    return {"ok": True}


@router.get("/users/{user_id}/detail")
async def user_detail(
    user_id: int,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Kullanicinin tam detayi: hesap + cihaz + siparisler."""
    u = await db.get(User, user_id)
    if not u:
        raise HTTPException(404, "Kullanici bulunamadi")

    device = (await db.execute(
        select(Device).where(Device.user_id == user_id)
    )).scalar_one_or_none()

    orders_res = await db.execute(
        select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
    )
    orders = orders_res.scalars().all()

    logs_res = await db.execute(
        select(ActivityLog)
        .where(ActivityLog.user_id == user_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(50)
    )
    activity = logs_res.scalars().all()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    days_left: Optional[int] = None
    if u.license_expires_at:
        delta = (u.license_expires_at - now).days
        days_left = max(delta, 0)

    return {
        "user": {
            "id": u.id,
            "email": u.email,
            "username": u.username,
            "role": u.role,
            "plan": u.plan,
            "is_active": u.is_active,
            "license_expires_at": u.license_expires_at.isoformat() if u.license_expires_at else None,
            "days_left": days_left,
            "reset_credits": u.reset_credits,
            "created_at": u.created_at.isoformat(),
        },
        "device": {
            "machine_id": device.machine_id,
            "hostname": device.hostname,
            "os_info": device.os_info,
            "last_ip": device.last_ip,
            "first_seen": device.first_seen.isoformat(),
            "last_seen": device.last_seen.isoformat(),
        } if device else None,
        "activity": [
            {
                "id": a.id,
                "event": a.event,
                "ip": a.ip,
                "detail": a.detail,
                "created_at": a.created_at.isoformat(),
            }
            for a in activity
        ],
        "orders": [
            {
                "id": o.id,
                "merchant_oid": o.merchant_oid,
                "product": o.product,
                "amount_tl": round(o.amount_kurus / 100, 2),
                "currency": o.currency,
                "status": o.status,
                "paid_at": o.paid_at.isoformat() if o.paid_at else None,
                "created_at": o.created_at.isoformat(),
            }
            for o in orders
        ],
    }
