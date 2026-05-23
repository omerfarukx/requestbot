"""Auth endpoints."""
import secrets
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from time import time

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, UserRegister, UserLogin, UserResponse, TokenResponse, ActivityLog
from auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

_rate_store: dict[str, list[float]] = defaultdict(list)

def _check_rate(key: str, max_calls: int, window: int) -> None:
    now = time()
    calls = _rate_store[key]
    _rate_store[key] = [t for t in calls if now - t < window]
    if len(_rate_store[key]) >= max_calls:
        raise HTTPException(429, f"Cok fazla istek. {window} saniye bekleyin.")
    _rate_store[key].append(now)


@router.post("/register", response_model=TokenResponse)
async def register(request: Request, data: UserRegister, db: AsyncSession = Depends(get_db)):
    _check_rate(f"reg:{request.client.host if request.client else '?'}", 5, 60)
    if len(data.password) < 6:
        raise HTTPException(400, "Sifre en az 6 karakter olmali")

    exists = await db.execute(
        select(User).where((User.email == data.email) | (User.username == data.username))
    )
    if exists.scalar_one_or_none():
        raise HTTPException(400, "E-posta veya kullanici adi zaten kayitli")

    # Ilk kayit = admin + agency + 10 yil lisans
    total = await db.scalar(select(func.count(User.id))) or 0
    role = "admin" if total == 0 else "user"
    plan = "agency" if total == 0 else "free"
    license_exp = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=3650) if total == 0 else None

    u = User(
        email=data.email,
        username=data.username,
        password_hash=hash_password(data.password),
        role=role,
        plan=plan,
        is_active=True,
        license_expires_at=license_exp,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    db.add(ActivityLog(user_id=u.id, event="register",
                       ip=request.client.host if request.client else None,
                       detail=f"plan={u.plan}"))
    await db.commit()

    return TokenResponse(
        access_token=create_access_token({"sub": str(u.id)}),
        user=UserResponse.model_validate(u),
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, data: UserLogin, db: AsyncSession = Depends(get_db)):
    _check_rate(f"login:{request.client.host if request.client else '?'}", 10, 60)
    res = await db.execute(
        select(User).where((User.username == data.username) | (User.email == data.username))
    )
    u = res.scalar_one_or_none()
    if not u or not verify_password(data.password, u.password_hash):
        raise HTTPException(401, "Kullanici adi veya sifre hatali")
    if not u.is_active:
        raise HTTPException(403, "Hesap devre disi")
    db.add(ActivityLog(user_id=u.id, event="login",
                       ip=request.client.host if request.client else None,
                       detail=f"plan={u.plan}"))
    await db.commit()
    return TokenResponse(
        access_token=create_access_token({"sub": str(u.id)}),
        user=UserResponse.model_validate(u),
    )


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    _check_rate(f"forgot:{request.client.host if request.client else '?'}", 3, 300)
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
    res = await db.execute(select(User).where(User.email == data.email))
    u = res.scalar_one_or_none()
    if u:
        u.password_reset_token = token
        u.password_reset_expires = expires
        await db.commit()
        return {"ok": True, "reset_url": f"/reset-password?token={token}"}
    return {"ok": True, "reset_url": None}


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    if len(data.new_password) < 6:
        raise HTTPException(400, "Sifre en az 6 karakter olmali")
    res = await db.execute(select(User).where(User.password_reset_token == data.token))
    u = res.scalar_one_or_none()
    if not u:
        raise HTTPException(400, "Gecersiz sifirlama baglantisi")
    if u.password_reset_expires and datetime.now(timezone.utc).replace(tzinfo=None) > u.password_reset_expires:
        raise HTTPException(400, "Sifirlama baglantisinin suresi dolmus. Tekrar talep edin.")
    u.password_hash = hash_password(data.new_password)
    u.password_reset_token = None
    u.password_reset_expires = None
    await db.commit()
    return {"ok": True}
