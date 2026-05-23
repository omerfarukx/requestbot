"""
Server modelleri:
- User    : musteri hesabi
- Device  : machine_id <-> user eslesmesi (tek cihaz kilidi)
- Order   : PayTR odeme kaydi
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from pydantic import BaseModel

from database import Base


# ── ORM ───────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user")           # user | admin
    plan = Column(String(20), default="free")           # free | pro | agency
    is_active = Column(Boolean, default=True)
    license_expires_at = Column(DateTime, nullable=True)
    reset_credits = Column(Integer, default=0)          # cihaz sifirlama paketi
    password_reset_token = Column(String(64), nullable=True, index=True)
    password_reset_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")


class Device(Base):
    """Her user'a baglı tek cihaz. machine_id = donanim parmak izi."""
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    machine_id = Column(String(128), nullable=False)
    hostname = Column(String(255), nullable=True)
    os_info = Column(String(255), nullable=True)
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_ip = Column(String(64), nullable=True)

    user = relationship("User", back_populates="devices")


class PageView(Base):
    """Anonim sayfa görüntüleme logu (giriş gerektirmez)."""
    __tablename__ = "page_views"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(200), nullable=False)          # /  /login  /register vb.
    ip = Column(String(64), nullable=True)
    referrer = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True)


class ActivityLog(Base):
    """login / download / bot_session / device_reset event loglari."""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event = Column(String(50), nullable=False)   # login|register|download|bot_session|device_reset
    ip = Column(String(64), nullable=True)
    detail = Column(String(300), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True)

    user = relationship("User", back_populates="activity_logs")


class Order(Base):
    """PayTR odeme kaydi."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    merchant_oid = Column(String(64), unique=True, nullable=False, index=True)  # PayTR siparis no
    product = Column(String(50), nullable=False)        # "license_pro_1m" | "device_reset"
    amount_kurus = Column(Integer, nullable=False)      # PayTR kurus cinsinden
    currency = Column(String(8), default="TL")
    status = Column(String(20), default="pending")      # pending | success | failed
    paid_at = Column(DateTime, nullable=True)
    raw_callback = Column(String(2000), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    user = relationship("User", back_populates="orders")


# ── Pydantic ──────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: str
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    plan: str
    is_active: bool
    license_expires_at: Optional[datetime]
    reset_credits: int
    created_at: datetime
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class LicenseValidateRequest(BaseModel):
    machine_id: str
    hostname: Optional[str] = None
    os_info: Optional[str] = None


class LicenseValidateResponse(BaseModel):
    valid: bool
    reason: Optional[str] = None
    plan: Optional[str] = None
    expires_at: Optional[datetime] = None


class DeviceResponse(BaseModel):
    id: int
    hostname: Optional[str]
    os_info: Optional[str]
    first_seen: datetime
    last_seen: datetime
    last_ip: Optional[str]
    model_config = {"from_attributes": True}


class ActivityLogResponse(BaseModel):
    id: int
    event: str
    ip: Optional[str]
    detail: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class AdminUserUpdate(BaseModel):
    plan: Optional[str] = None
    is_active: Optional[bool] = None
    license_expires_at: Optional[datetime] = None
    role: Optional[str] = None
    reset_credits: Optional[int] = None
