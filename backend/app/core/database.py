import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("sqlite+aiosqlite:///./"):
    backend_root = Path(__file__).resolve().parent.parent.parent
    db_file = (backend_root / db_url.replace("sqlite+aiosqlite:///./", "")).resolve()
    # Normalize Windows drive letter and forward slashes for SQLite URI
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

engine = create_async_engine(db_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
