"""
Auth modülü — JWT token üretimi + doğrulama, şifre hash
"""
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db

# ── Config ────────────────────────────────────────────────────────────────────

SECRET_KEY = os.environ.get("JWT_SECRET", "")
if not SECRET_KEY:
    import warnings
    SECRET_KEY = "changeme-use-env-var-in-production-32chars!"
    warnings.warn(
        "[GÜVENLİK] JWT_SECRET env degiskeni ayarlanmamis! "
        "Uretimde mutlaka guvenli bir deger belirleyin.",
        RuntimeWarning, stacklevel=2,
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 gün

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ── Şifre ────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]  # bcrypt 72-byte limit
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except Exception:
        return False


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Bağımlılıklar ────────────────────────────────────────────────────────────

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    from models import User
    payload = decode_token(token)
    user_id: int = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token geçersiz")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Hesap devre dışı")
    return user


async def get_current_admin(user=Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin yetkisi gerekli")
    return user


async def require_active_license(user=Depends(get_current_user)):
    """Pro/ajans planı ve geçerli lisans kontrolü."""
    if user.role == "admin":
        return user
    if user.plan == "free":
        raise HTTPException(status_code=403, detail="Bu özellik için Pro lisans gerekli")
    if user.license_expires_at and user.license_expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=403, detail="Lisansınızın süresi dolmuş — yenileyin")
    return user
