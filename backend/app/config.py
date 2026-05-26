"""Application configuration."""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "陵水县人民医院慢病管理系统"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:////Users/shayuen/.qclaw/workspace/slow_disease_system/backend/slow_disease.db",
    )
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "change-me-in-production-!!!",
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "0" * 64)
    CORS_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


# 惰性加载 settings（避免模块导入时触发 pydantic-settings Python 3.9 bug）
class _LazySettings:
    def __getattr__(self, name: str):
        return getattr(get_settings(), name)
    def __setattr__(self, name: str, value):
        setattr(get_settings(), name, value)
    def __repr__(self):
        return repr(get_settings())
    def __dir__(self):
        return dir(get_settings())

settings = _LazySettings()  # type: ignore[assignment]
