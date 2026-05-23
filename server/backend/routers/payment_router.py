"""PayTR iFrame odeme entegrasyonu."""
import base64
import hashlib
import hmac as _hmac
import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from database import get_db
from models import User, Order, ActivityLog

router = APIRouter(prefix="/api/payment", tags=["payment"])

MERCHANT_ID   = os.environ.get("PAYTR_MERCHANT_ID", "")
MERCHANT_KEY  = os.environ.get("PAYTR_MERCHANT_KEY", "")
MERCHANT_SALT = os.environ.get("PAYTR_MERCHANT_SALT", "")
TEST_MODE     = int(os.environ.get("PAYTR_TEST_MODE", "1"))
BASE_URL      = os.environ.get("BASE_URL", "https://requesthitbot.com")

PRODUCTS: dict[str, dict] = {
    "monthly":      {"name": "RequestBot Aylık",   "amount": 29900,  "plan": "pro", "days": 30},
    "yearly":       {"name": "RequestBot Yıllık",  "amount": 199000, "plan": "pro", "days": 365},
    "device_reset": {"name": "Cihaz Sıfırlama",   "amount": 1500,   "plan": None,  "days": 0},
}


def _paytr_token(key: str, salt: str, hash_str: str) -> bytes:
    """PayTR resmi Python ornegine gore HMAC-SHA256 → base64 bytes."""
    return base64.b64encode(
        _hmac.new(key.encode(), hash_str.encode() + salt.encode(), hashlib.sha256).digest()
    )


def _callback_hmac(key: str, salt: str, msg: str) -> str:
    """Callback hash dogrulama icin HMAC → base64 string."""
    return base64.b64encode(
        _hmac.new(key.encode(), (msg + salt).encode(), hashlib.sha256).digest()
    ).decode()


class StartPaymentRequest(BaseModel):
    product: str


@router.post("/start")
async def start_payment(
    data: StartPaymentRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """PayTR iFrame token üret → frontend'e döndür."""
    if data.product not in PRODUCTS:
        raise HTTPException(400, "Geçersiz ürün")
    if not MERCHANT_ID:
        raise HTTPException(503, "Ödeme servisi henüz yapılandırılmamış")

    pinfo        = PRODUCTS[data.product]
    merchant_oid = f"RB{uuid.uuid4().hex[:12].upper()}"
    # nginx arkasindaki gercek IP
    forwarded = request.headers.get("X-Forwarded-For", "")
    user_ip   = forwarded.split(",")[0].strip() if forwarded else (
        request.client.host if request.client else "1.1.1.1"
    )
    amount       = pinfo["amount"]

    basket = base64.b64encode(
        json.dumps([[pinfo["name"], f"{amount / 100:.2f}", 1]]).encode()
    ).decode()

    # Resmi PayTR Python ornegine gore — tum degerler STRING
    pa_str       = str(amount)
    no_inst      = "0"
    max_inst     = "0"
    currency     = "TL"
    test_mode_s  = str(TEST_MODE)
    debug_on_s   = "1"
    timeout_s    = "30"

    ok_url   = f"{BASE_URL}/payment/result?status=success&oid={merchant_oid}"
    fail_url = f"{BASE_URL}/payment/result?status=failed&oid={merchant_oid}"

    # Hash: merchant_id + user_ip + merchant_oid + email + payment_amount
    #       + user_basket + no_installment + max_installment + currency + test_mode
    hash_str = (
        MERCHANT_ID + user_ip + merchant_oid + user.email
        + pa_str + basket
        + no_inst + max_inst + currency + test_mode_s
    )
    paytr_token = _paytr_token(MERCHANT_KEY, MERCHANT_SALT, hash_str).decode()

    payload = {
        "merchant_id":       MERCHANT_ID,
        "user_ip":           user_ip,
        "merchant_oid":      merchant_oid,
        "email":             user.email,
        "payment_amount":    pa_str,
        "paytr_token":       paytr_token,
        "user_basket":       basket,
        "debug_on":          debug_on_s,
        "no_installment":    no_inst,
        "max_installment":   max_inst,
        "user_name":         user.username,
        "user_address":      "Türkiye",
        "user_phone":        "05000000000",
        "merchant_ok_url":   ok_url,
        "merchant_fail_url": fail_url,
        "timeout_limit":     timeout_s,
        "currency":          currency,
        "test_mode":         test_mode_s,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post("https://www.paytr.com/odeme/api/get-token", data=payload)

    try:
        result = resp.json()
    except Exception:
        raise HTTPException(502, f"PayTR geçersiz yanıt: {resp.text[:200]}")
    if result.get("status") != "success":
        reason = result.get("reason", "PayTR token alınamadı")
        import logging
        logging.getLogger("payment").error("PayTR hata: %s | payload: %s", reason, {k:v for k,v in payload.items() if k not in ('paytr_token','user_basket')})
        raise HTTPException(502, reason)

    order = Order(
        user_id=user.id,
        merchant_oid=merchant_oid,
        product=data.product,
        amount_kurus=amount,
        status="pending",
    )
    db.add(order)
    await db.commit()

    return {"ok": True, "token": result["token"], "merchant_oid": merchant_oid}


@router.post("/callback", response_class=PlainTextResponse)
async def paytr_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """PayTR webhook — ödeme sonucu bildirimi. Yanıt mutlaka 'OK' olmalı."""
    form         = await request.form()
    merchant_oid = str(form.get("merchant_oid", ""))
    status       = str(form.get("status", ""))
    total_amount = str(form.get("total_amount", ""))
    hash_val     = str(form.get("hash", ""))

    # Hash doğrula — PayTR tekrar denediğinde bile OK dönmeliyiz
    expected = _callback_hmac(MERCHANT_KEY, MERCHANT_SALT, merchant_oid + status + total_amount)
    if hash_val != expected:
        return PlainTextResponse("OK")

    res = await db.execute(select(Order).where(Order.merchant_oid == merchant_oid))
    order = res.scalar_one_or_none()
    if not order:
        return PlainTextResponse("OK")

    # Tekrar işleme engeli
    if order.status == "success":
        return PlainTextResponse("OK")

    raw = json.dumps(dict(form), default=str)[:2000]
    order.raw_callback = raw

    if status == "success":
        order.status = "success"
        order.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)

        pinfo = PRODUCTS.get(order.product, {})
        u = await db.get(User, order.user_id)

        if u and pinfo:
            if pinfo.get("plan"):
                u.plan = pinfo["plan"]
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                if u.license_expires_at and u.license_expires_at > now:
                    u.license_expires_at += timedelta(days=pinfo["days"])
                else:
                    u.license_expires_at = now + timedelta(days=pinfo["days"])
                db.add(ActivityLog(
                    user_id=u.id, event="payment",
                    detail=f"{order.product} | {merchant_oid} | {total_amount} kurus",
                ))
            elif order.product == "device_reset":
                u.reset_credits += 1
                db.add(ActivityLog(
                    user_id=u.id, event="payment",
                    detail=f"device_reset | {merchant_oid}",
                ))
    else:
        order.status = "failed"

    await db.commit()
    return PlainTextResponse("OK")


@router.get("/products")
async def list_products():
    """Satılabilir ürün listesi (fiyatlar TL)."""
    return [
        {
            "id":     pid,
            "name":   p["name"],
            "amount": p["amount"],
            "amount_tl": round(p["amount"] / 100, 2),
            "plan":   p["plan"],
            "days":   p["days"],
        }
        for pid, p in PRODUCTS.items()
    ]
