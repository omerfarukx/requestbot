"""Lisansli .exe indirme."""
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from database import get_db
from models import User, ActivityLog

router = APIRouter(prefix="/api/download", tags=["download"])

_default_downloads = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "downloads")
DOWNLOADS_DIR = os.environ.get("DOWNLOADS_DIR", _default_downloads)
LATEST_EXE = "RequestBot.exe"


@router.get("/latest")
async def download_latest(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """RequestBot.exe indir — sadece aktif lisansi olan."""
    if user.role != "admin":
        if not user.license_expires_at or user.license_expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(403, "Lisans suresi dolmus")
        if user.plan == "free":
            raise HTTPException(403, "Aktif lisans yok")

    path = os.path.join(DOWNLOADS_DIR, LATEST_EXE)
    if not os.path.isfile(path):
        raise HTTPException(404, "Henuz dosya yuklenmedi")

    db.add(ActivityLog(
        user_id=user.id, event="download",
        ip=request.client.host if request.client else None,
        detail=LATEST_EXE,
    ))
    await db.commit()

    return FileResponse(
        path,
        media_type="application/vnd.microsoft.portable-executable",
        filename=LATEST_EXE,
    )


@router.get("/info")
async def download_info(user: User = Depends(get_current_user)):
    """Indirilebilir surum bilgisi."""
    path = os.path.join(DOWNLOADS_DIR, LATEST_EXE)
    if not os.path.isfile(path):
        return {"available": False}
    stat = os.stat(path)
    return {
        "available": True,
        "filename": LATEST_EXE,
        "size_mb": round(stat.st_size / (1024 * 1024), 1),
        "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }
