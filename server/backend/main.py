"""
RequestBot Lisans Sunucusu
- Auth (register/login)
- Lisans + cihaz dogrulama
- Admin paneli
- .exe indirme
- PayTR odeme (router henuz eklenmedi)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers.auth_router import router as auth_router
from routers.license_router import router as license_router
from routers.admin_router import router as admin_router
from routers.download_router import router as download_router

app = FastAPI(title="RequestBot License Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(license_router)
app.include_router(admin_router)
app.include_router(download_router)


@app.on_event("startup")
async def startup():
    await init_db()
    print("[Server] Lisans sunucusu hazir — http://0.0.0.0:8001")


@app.get("/")
async def root():
    return {"service": "RequestBot License Server", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}
