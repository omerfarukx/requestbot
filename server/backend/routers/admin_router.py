"""Admin endpointleri."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, UserResponse, AdminUserUpdate
from auth import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


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
    base = u.license_expires_at if (u.license_expires_at and u.license_expires_at >= datetime.utcnow()) else datetime.utcnow()
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
