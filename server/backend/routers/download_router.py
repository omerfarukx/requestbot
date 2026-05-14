"""Lisansli .exe indirme."""
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from auth import get_current_user
from models import User

router = APIRouter(prefix="/api/download", tags=["download"])

DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "downloads")
LATEST_EXE = "RequestBot.exe"


@router.get("/latest")
async def download_latest(user: User = Depends(get_current_user)):
    """RequestBot.exe indir — sadece aktif lisansi olan."""
    if user.role != "admin":
        if not user.license_expires_at or user.license_expires_at < datetime.utcnow():
            raise HTTPException(403, "Lisans suresi dolmus")
        if user.plan == "free":
            raise HTTPException(403, "Aktif lisans yok")

    path = os.path.join(DOWNLOADS_DIR, LATEST_EXE)
    if not os.path.isfile(path):
        raise HTTPException(404, "Henuz dosya yuklenmedi")

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
