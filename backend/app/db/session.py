"""Async database session - SQLite + PostgreSQL 兼容版本"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from app.config import get_settings

Base = declarative_base()

settings = get_settings()
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# SQLite 不支持 pool_size / max_overflow，需要条件处理
engine_kwargs = {"echo": settings.DEBUG}
if not is_sqlite:
    engine_kwargs.update(
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
    )

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
