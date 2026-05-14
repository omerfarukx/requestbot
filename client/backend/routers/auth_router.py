"""Auth endpoints: register, login, me, license uzatma (admin)."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import (
    User, UserRegister, UserLogin, UserResponse,
    TokenResponse, AdminUserUpdate,
)
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, get_current_admin,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    # E-posta veya kullanıcı adı kontrolü
    existing = await db.execute(
        select(User).where((User.email == data.email) | (User.username == data.username))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Bu e-posta veya kullanıcı adı zaten kayıtlı")

    if len(data.password) < 6:
        raise HTTPException(400, "Şifre en az 6 karakter olmalı")

    # İlk kayıt olan kullanıcı admin olur
    total = await db.scalar(select(func.count(User.id))) or 0
    role = "admin" if total == 0 else "user"
    plan = "agency" if total == 0 else "free"
    license_exp = datetime.utcnow() + timedelta(days=3650) if total == 0 else None

    user = User(
        email=data.email,
        username=data.username,
        password_hash=hash_password(data.password),
        role=role,
        plan=plan,
        is_active=True,
        license_expires_at=license_exp,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(
            (User.username == data.username) | (User.email == data.username)
        )
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Kullanıcı adı veya şifre hatalı")
    if not user.is_active:
        raise HTTPException(403, "Hesap devre dışı")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user


# ── Admin endpoints ──────────────────────────────────────────────────────────

@router.get("/admin/users", response_model=list[UserResponse])
async def admin_list_users(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.id.desc()))
    return result.scalars().all()


@router.patch("/admin/users/{user_id}", response_model=UserResponse)
async def admin_update_user(
    user_id: int,
    data: AdminUserUpdate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Kullanıcı bulunamadı")

    if data.plan is not None:
        user.plan = data.plan
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.license_expires_at is not None:
        user.license_expires_at = data.license_expires_at
    if data.role is not None:
        user.role = data.role

    await db.commit()
    await db.refresh(user)
    return user


@router.post("/admin/users/{user_id}/extend")
async def admin_extend_license(
    user_id: int,
    days: int = 30,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lisansı X gün uzat. Süresi geçmişse şu andan itibaren başlat."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Kullanıcı bulunamadı")

    base = user.license_expires_at
    if not base or base < datetime.utcnow():
        base = datetime.utcnow()
    user.license_expires_at = base + timedelta(days=days)
    if user.plan == "free":
        user.plan = "pro"

    await db.commit()
    return {"ok": True, "new_expiry": user.license_expires_at}


@router.post("/sso", response_model=TokenResponse)
async def sso_login(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Launcher SSO — lisans sunucusu token'ini local JWT'ye cevir.
    Sadece localhost'tan cagirilabilir.
    """
    client_host = request.client.host if request.client else ""
    if client_host not in ("127.0.0.1", "::1", "localhost"):
        raise HTTPException(403, "Sadece lokal erisim")

    body = await request.json()
    user_data = body.get("user", {})
    username = user_data.get("username", "")
    email = user_data.get("email") or f"{username}@requestbot.local"
    plan = user_data.get("plan", "free")
    role = user_data.get("role", "user")

    if not username:
        raise HTTPException(400, "Kullanici adi gerekli")

    license_exp = None
    exp_str = user_data.get("license_expires_at")
    if exp_str:
        try:
            license_exp = datetime.fromisoformat(str(exp_str).replace("Z", "+00:00"))
        except Exception:
            pass

    result = await db.execute(
        select(User).where((User.username == username) | (User.email == email))
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=email,
            username=username,
            password_hash="sso:no-password",
            role=role,
            plan=plan,
            is_active=True,
            license_expires_at=license_exp,
        )
        db.add(user)
    else:
        user.plan = plan
        user.role = role
        user.is_active = True
        if license_exp:
            user.license_expires_at = license_exp

    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.delete("/admin/users/{user_id}")
async def admin_delete_user(
    user_id: int,
    current: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == current.id:
        raise HTTPException(400, "Kendinizi silemezsiniz")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Kullanıcı bulunamadı")
    await db.delete(user)
    await db.commit()
    return {"ok": True}
