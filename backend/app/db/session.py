"""Async database session - SQLite + PostgreSQL 兼容版本（惰性初始化，避免 pydantic-settings Python 3.9 bug）"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from app.config import get_settings

Base = declarative_base()

# 惰性 engine & session factory
_engine = None
_factory = None


def _get_engine():
    """惰性创建异步引擎，不在模块加载时触发 get_settings()"""
    global _engine
    if _engine is None:
        settings = get_settings()
        is_sqlite = settings.DATABASE_URL.startswith("sqlite")
        engine_kwargs = {"echo": settings.DEBUG}
        if not is_sqlite:
            engine_kwargs.update(
                pool_size=20,
                max_overflow=10,
                pool_pre_ping=True,
            )
        _engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)
    return _engine


def _get_factory():
    """惰性创建异步会话工厂"""
    global _factory
    if _factory is None:
        _factory = async_sessionmaker(
            _get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _factory


def async_session_factory():
    """公开的异步会话工厂（供中间件等模块使用）"""
    return _get_factory()()


def __getattr__(name):
    """惰性模块属性访问，兼容 from app.db.session import engine"""
    if name == 'engine':
        return _get_engine()
    if name == '_engine':
        return _get_engine()
    if name == 'async_session_factory':
        return _get_factory
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：yield 一个异步数据库会话"""
    factory = _get_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
