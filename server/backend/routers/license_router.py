"""
Lisans + cihaz dogrulama.

Akış:
- Client login sonrası /validate cagirir, machine_id gonderir.
- Server ilk gorur ise: cihazi kaydet.
- Server farkli cihaz gorur ise: REDDET (cihaz sifirlama gerek).
- Lisans suresi gecmis ise: REDDET.
- Aksi: success + yeni heartbeat zamani.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import (
    User, Device,
    LicenseValidateRequest, LicenseValidateResponse,
    DeviceResponse,
)
from auth import get_current_user

router = APIRouter(prefix="/api/license", tags=["license"])


@router.post("/validate", response_model=LicenseValidateResponse)
async def validate(
    data: LicenseValidateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Client her başlatmada + 5 dakikada bir çağırır."""
    if not user.is_active:
        return LicenseValidateResponse(valid=False, reason="Hesap devre disi")

    if user.role != "admin":
        if not user.license_expires_at or user.license_expires_at < datetime.utcnow():
            return LicenseValidateResponse(valid=False, reason="Lisans suresi dolmus")
        if user.plan == "free":
            return LicenseValidateResponse(valid=False, reason="Aktif lisans yok — paket satin alin")

    client_ip = request.client.host if request.client else None

    # Cihaz var mi?
    existing = (await db.execute(
        select(Device).where(Device.user_id == user.id)
    )).scalar_one_or_none()

    if existing is None:
        # Ilk kayit
        d = Device(
            user_id=user.id,
            machine_id=data.machine_id,
            hostname=data.hostname,
            os_info=data.os_info,
            last_ip=client_ip,
        )
        db.add(d)
        await db.commit()
    else:
        # Cihaz uyusmazligi
        if existing.machine_id != data.machine_id:
            return LicenseValidateResponse(
                valid=False,
                reason="Bu hesap baska bir cihaza kayitli. Cihaz sifirlama paketi satin alin.",
            )
        # Heartbeat update
        existing.last_seen = datetime.utcnow()
        existing.last_ip = client_ip
        if data.hostname:
            existing.hostname = data.hostname
        if data.os_info:
            existing.os_info = data.os_info
        await db.commit()

    return LicenseValidateResponse(
        valid=True,
        plan=user.plan,
        expires_at=user.license_expires_at,
    )


@router.get("/device", response_model=DeviceResponse | None)
async def my_device(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Kullanicinin kayitli cihaz bilgisi."""
    d = (await db.execute(
        select(Device).where(Device.user_id == user.id)
    )).scalar_one_or_none()
    return d


@router.post("/reset-device")
async def reset_device(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cihazi sifirla — reset_credits gerekli."""
    if user.role != "admin" and user.reset_credits <= 0:
        raise HTTPException(
            403,
            "Cihaz sifirlama hakkiniz yok. Cihaz sifirlama paketi satin alin (15 TL).",
        )

    d = (await db.execute(
        select(Device).where(Device.user_id == user.id)
    )).scalar_one_or_none()

    if d:
        await db.delete(d)

    if user.role != "admin":
        user.reset_credits -= 1

    await db.commit()
    return {"ok": True, "remaining_credits": user.reset_credits}
