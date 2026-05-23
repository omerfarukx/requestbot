from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

_data_dir = os.environ.get("REQUESTBOT_DATA") or os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")), "RequestBot"
)
os.makedirs(_data_dir, exist_ok=True)
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(_data_dir, 'requestbot.db').replace(chr(92), '/')}"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _run_migrations(conn)


async def _run_migrations(conn):
    """Mevcut DB'ye eksik kolonları ekler (ALTER TABLE IF NOT EXISTS yerine try/except)."""
    migrations = [
        "ALTER TABLE campaigns ADD COLUMN mode VARCHAR(20) DEFAULT 'http'",
        "ALTER TABLE campaigns ADD COLUMN hourly_limit INTEGER",
        "ALTER TABLE campaigns ADD COLUMN active_hours_start INTEGER DEFAULT 0",
        "ALTER TABLE campaigns ADD COLUMN active_hours_end INTEGER DEFAULT 24",
        "ALTER TABLE campaigns ADD COLUMN bounce_rate_pct INTEGER DEFAULT 30",
        "ALTER TABLE campaigns ADD COLUMN referrer_mix VARCHAR(500) DEFAULT 'google:70,direct:20,social:10'",
        "ALTER TABLE campaigns ADD COLUMN mobile_ratio_pct INTEGER DEFAULT 65",
    ]
    for sql in migrations:
        try:
            await conn.execute(__import__("sqlalchemy").text(sql))
        except Exception:
            pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
