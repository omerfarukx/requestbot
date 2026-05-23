"""
Lisans + cihaz dogrulama.

Akış:
- Client login sonrası /validate cagirir, machine_id gonderir.
- Server ilk gorur ise: cihazi kaydet.
- Server farkli cihaz gorur ise: REDDET (cihaz sifirlama gerek).
- Lisans suresi gecmis ise: REDDET.
- Aksi: success + yeni heartbeat zamani.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import (
    User, Device, Order, ActivityLog,
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
        if not user.license_expires_at or user.license_expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
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
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        existing.last_seen = now_utc
        existing.last_ip = client_ip
        if data.hostname:
            existing.hostname = data.hostname
        if data.os_info:
            existing.os_info = data.os_info

        # bot_session logu saatte 1 kez
        one_hour_ago = now_utc.replace(minute=0, second=0, microsecond=0)
        recent = await db.scalar(
            select(func.count(ActivityLog.id)).where(
                ActivityLog.user_id == user.id,
                ActivityLog.event == "bot_session",
                ActivityLog.created_at >= one_hour_ago,
            )
        )
        if not recent:
            db.add(ActivityLog(
                user_id=user.id, event="bot_session",
                ip=client_ip,
                detail=f"plan={user.plan}",
            ))
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
    request: Request,
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

    db.add(ActivityLog(
        user_id=user.id, event="device_reset",
        ip=request.client.host if request.client else None,
        detail=f"remaining={user.reset_credits}",
    ))
    await db.commit()
    return {"ok": True, "remaining_credits": user.reset_credits}


@router.post("/order/device-reset")
async def order_device_reset(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cihaz sifirlama paketi icin bekleyen siparis olustur."""
    import uuid
    import os
    merchant_oid = f"DR{uuid.uuid4().hex[:12].upper()}"
    order = Order(
        user_id=user.id,
        merchant_oid=merchant_oid,
        product="device_reset",
        amount_kurus=1500,
        status="pending",
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return {
        "ok": True,
        "order_id": order.id,
        "merchant_oid": merchant_oid,
        "amount": "15 ₺",
        "bank": os.environ.get("PAYMENT_BANK", "Papara"),
        "iban": os.environ.get("PAYMENT_IBAN", "Lütfen admin ile iletişime geçin"),
        "name": os.environ.get("PAYMENT_NAME", "RequestHitBot"),
        "note": merchant_oid,
    }
