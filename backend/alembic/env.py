from logging.config import fileConfig
from logging import getLogger
from sqlalchemy import engine_from_config, pool, create_engine
from sqlalchemy import pool

from alembic import context

# 导入应用的模型和配置
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from app.config import settings
from app.models import Base

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = getLogger('alembic.env')
logger.info('数据库URL: %s', settings.DATABASE_URL.replace('sqlite+aiosqlite://', 'sqlite://'))

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    
    # 如果是离线模式，使用配置文件中的URL
    if not url:
        url = settings.DATABASE_URL
        # 转换 aiosqlite 为 sqlite (alembic 不支持 aiosqlite)
        url = url.replace('sqlite+aiosqlite://', 'sqlite://')
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # 从应用的配置读取数据库URL
    configuration = config.get_section(config.config_ini_section, {})
    
    # 如果配置中没有 sqlalchemy.url，则从 app.config 读取
    if not configuration.get('sqlalchemy.url'):
        db_url = settings.DATABASE_URL
        # 转换 aiosqlite 为 sqlite (alembic 不支持 aiosqlite)
        db_url = db_url.replace('sqlite+aiosqlite://', 'sqlite://')
        configuration['sqlalchemy.url'] = db_url
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # 对 SQLite 启用 batch mode (支持 ALTER TABLE 等操作的 workaround)
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            render_as_batch=True  # 重要：SQLite 需要这个来支持 ALTER TABLE
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
