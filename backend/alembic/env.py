from logging.config import fileConfig
from logging import getLogger
from sqlalchemy import engine_from_config, pool
from alembic import context

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

# 不在模块顶层导入 app.models（会触发 app.config → pydantic-settings bug）
# 改用延迟导入：在 migration 函数内部再 import
target_metadata = None  # 占位，run_migrations 时动态加载

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = getLogger('alembic.env')


def _get_metadata():
    """延迟导入 Base.metadata，避免启动时报错"""
    from app.models import Base
    return Base.metadata


def _to_sync_url(url: str) -> str:
    """异步驱动 URL 转同步（Alembic 需要）"""
    if not url:
        return url
    return url.replace('sqlite+aiosqlite://', 'sqlite://') \
               .replace('postgresql+asyncpg://', 'postgresql+psycopg2://')


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    url = _to_sync_url(url)

    context.configure(
        url=url,
        target_metadata=_get_metadata(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=False,  # SQLite 动态类型，类型变更无意义
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section, {})

    db_url = configuration.get('sqlalchemy.url', '')
    db_url = _to_sync_url(db_url)
    configuration['sqlalchemy.url'] = db_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=_get_metadata(),
            render_as_batch=True,  # SQLite 需要
            compare_type=False,  # SQLite 动态类型，类型变更无意义
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
