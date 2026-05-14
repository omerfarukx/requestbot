from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional, List

from database import Base


# ── SQLAlchemy ORM Models ──────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user")           # "user" | "admin"
    plan = Column(String(20), default="free")           # "free" | "pro" | "agency"
    is_active = Column(Boolean, default=True)
    license_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    campaigns = relationship("Campaign", back_populates="owner", cascade="all, delete-orphan")
    proxies = relationship("Proxy", back_populates="owner", cascade="all, delete-orphan")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    target_url = Column(String(2048), nullable=False)
    keyword = Column(String(500), nullable=True)
    search_engine = Column(String(50), default="google")
    session_duration_min = Column(Integer, default=5)
    session_duration_max = Column(Integer, default=15)
    concurrent_workers = Column(Integer, default=3)
    daily_visit_target = Column(Integer, nullable=True)
    pages_per_session_min = Column(Integer, default=2)
    pages_per_session_max = Column(Integer, default=8)
    status = Column(String(50), default="idle")
    total_visits = Column(Integer, default=0)
    successful_visits = Column(Integer, default=0)
    failed_visits = Column(Integer, default=0)
    # Gelismis kampanya ayarlari
    hourly_limit = Column(Integer, nullable=True)              # saatlik max ziyaret (None=sinirsiz)
    active_hours_start = Column(Integer, default=0)            # 0-23 (TR saat)
    active_hours_end = Column(Integer, default=24)             # 0-24
    bounce_rate_pct = Column(Integer, default=30)              # %30 oturum hizli ciksin
    referrer_mix = Column(String(500), default="google:70,direct:20,social:10")
    mobile_ratio_pct = Column(Integer, default=65)             # %65 mobil UA
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    owner = relationship("User", back_populates="campaigns")
    visits = relationship("Visit", back_populates="campaign", cascade="all, delete-orphan")


class Proxy(Base):
    __tablename__ = "proxies"

    id = Column(Integer, primary_key=True, index=True)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(255), nullable=True)
    password = Column(String(255), nullable=True)
    protocol = Column(String(20), default="http")
    status = Column(String(20), default="unknown")
    last_checked = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    owner = relationship("User", back_populates="proxies")


class Visit(Base):
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    proxy_id = Column(Integer, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    pages_visited = Column(Integer, default=1)
    status = Column(String(20), default="running")
    error_message = Column(Text, nullable=True)

    campaign = relationship("Campaign", back_populates="visits")


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, nullable=True)
    level = Column(String(20), default="info")
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class RankCheck(Base):
    __tablename__ = "rank_checks"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    keyword = Column(String(500), nullable=False)
    rank = Column(Integer, nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow)


# ── Pydantic Schemas ────────────────────────────────────────────────────────────

class CampaignCreate(BaseModel):
    name: str
    target_url: str
    keyword: Optional[str] = None
    search_engine: str = "google"
    session_duration_min: int = 5
    session_duration_max: int = 15
    concurrent_workers: int = 3
    daily_visit_target: Optional[int] = None
    pages_per_session_min: int = 2
    pages_per_session_max: int = 8
    hourly_limit: Optional[int] = None
    active_hours_start: int = 0
    active_hours_end: int = 24
    bounce_rate_pct: int = 30
    referrer_mix: str = "google:70,direct:20,social:10"
    mobile_ratio_pct: int = 65


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    target_url: Optional[str] = None
    keyword: Optional[str] = None
    search_engine: Optional[str] = None
    session_duration_min: Optional[int] = None
    session_duration_max: Optional[int] = None
    concurrent_workers: Optional[int] = None
    daily_visit_target: Optional[int] = None
    pages_per_session_min: Optional[int] = None
    pages_per_session_max: Optional[int] = None
    hourly_limit: Optional[int] = None
    active_hours_start: Optional[int] = None
    active_hours_end: Optional[int] = None
    bounce_rate_pct: Optional[int] = None
    referrer_mix: Optional[str] = None
    mobile_ratio_pct: Optional[int] = None


class CampaignResponse(BaseModel):
    id: int
    name: str
    target_url: str
    keyword: Optional[str]
    search_engine: str
    session_duration_min: int
    session_duration_max: int
    concurrent_workers: int
    daily_visit_target: Optional[int]
    pages_per_session_min: int
    pages_per_session_max: int
    hourly_limit: Optional[int] = None
    active_hours_start: int = 0
    active_hours_end: int = 24
    bounce_rate_pct: int = 30
    referrer_mix: str = "google:70,direct:20,social:10"
    mobile_ratio_pct: int = 65
    status: str
    total_visits: int
    successful_visits: int
    failed_visits: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProxyResponse(BaseModel):
    id: int
    host: str
    port: int
    username: Optional[str]
    password: Optional[str]
    protocol: str
    status: str
    last_checked: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class LogResponse(BaseModel):
    id: int
    campaign_id: Optional[int]
    level: str
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RankCheckResponse(BaseModel):
    id: int
    campaign_id: int
    keyword: str
    rank: Optional[int]
    checked_at: datetime

    model_config = {"from_attributes": True}


class StatsResponse(BaseModel):
    total_campaigns: int
    running_campaigns: int
    total_visits: int
    successful_visits: int
    total_proxies: int
    active_proxies: int


# ── User Schemas ───────────────────────────────────────────────────────────────

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
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class AdminUserUpdate(BaseModel):
    plan: Optional[str] = None
    is_active: Optional[bool] = None
    license_expires_at: Optional[datetime] = None
    role: Optional[str] = None
