"""
RequestBot Lisans Sunucusu
- Auth (register/login)
- Lisans + cihaz dogrulama
- Admin paneli
- .exe indirme
- PayTR odeme (router henuz eklenmedi)
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from pydantic import BaseModel
from typing import Optional

from database import init_db, get_db, engine
from sqlalchemy import text
from routers.auth_router import router as auth_router
from routers.license_router import router as license_router
from routers.admin_router import router as admin_router
from routers.download_router import router as download_router
from routers.payment_router import router as payment_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with engine.begin() as conn:
        for stmt in [
            "ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(64)",
            "ALTER TABLE users ADD COLUMN password_reset_expires DATETIME",
        ]:
            try:
                await conn.execute(text(stmt))
            except Exception:
                pass
    print("[Server] Lisans sunucusu hazir — http://0.0.0.0:8001")
    yield

app = FastAPI(title="RequestBot License Server", version="1.0.0", lifespan=lifespan)

_raw_origins = os.environ.get(
    "ALLOWED_ORIGINS",
    "https://requesthitbot.com,http://localhost:5173,http://localhost:5174",
)
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(auth_router)
app.include_router(license_router)
app.include_router(admin_router)
app.include_router(download_router)
app.include_router(payment_router)


@app.get("/")
async def root():
    return {"service": "RequestBot License Server", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


class PageViewIn(BaseModel):
    path: str
    referrer: Optional[str] = None


@app.post("/api/stats/pageview", status_code=204)
async def track_pageview(
    data: PageViewIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Anonim sayfa goruntulemesi — auth gerektirmez."""
    from models import PageView
    db.add(PageView(
        path=data.path[:200],
        ip=request.client.host if request.client else None,
        referrer=(data.referrer or "")[:500] or None,
    ))
    await db.commit()
