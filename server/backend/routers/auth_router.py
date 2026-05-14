"""Auth endpoints."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, UserRegister, UserLogin, UserResponse, TokenResponse
from auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
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
    license_exp = datetime.utcnow() + timedelta(days=3650) if total == 0 else None

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

    return TokenResponse(
        access_token=create_access_token({"sub": str(u.id)}),
        user=UserResponse.model_validate(u),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(User).where((User.username == data.username) | (User.email == data.username))
    )
    u = res.scalar_one_or_none()
    if not u or not verify_password(data.password, u.password_hash):
        raise HTTPException(401, "Kullanici adi veya sifre hatali")
    if not u.is_active:
        raise HTTPException(403, "Hesap devre disi")
    return TokenResponse(
        access_token=create_access_token({"sub": str(u.id)}),
        user=UserResponse.model_validate(u),
    )


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user
