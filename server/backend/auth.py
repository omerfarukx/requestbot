"""JWT + bcrypt auth helpers."""
import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db

SECRET_KEY = os.environ.get("JWT_SECRET", "change-me-in-prod-min-32-chars-long-secret!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 gün

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(p: str) -> str:
    return bcrypt.hashpw(p.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(401, "Token gecersiz veya suresi dolmus")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    from models import User
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(401, "Token gecersiz")
    user = (await db.execute(select(User).where(User.id == int(user_id)))).scalar_one_or_none()
    if not user:
        raise HTTPException(401, "Kullanici bulunamadi")
    if not user.is_active:
        raise HTTPException(403, "Hesap devre disi")
    return user


async def get_current_admin(user=Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(403, "Admin yetkisi gerekli")
    return user
