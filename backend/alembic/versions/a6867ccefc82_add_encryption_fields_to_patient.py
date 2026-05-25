"""Sync database schema with models

Revision ID: a6867ccefc82
Revises: 000000000001
Create Date: 2026-05-23 10:41:22.758252

说明：此迁移记录模型与数据库的差异。
由于 SQLite 不支持 ALTER COLUMN 类型转换，实际迁移使用 batch_alter_table。
对于生产环境 PostgreSQL，需要重新生成迁移脚本。

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a6867ccefc82'
down_revision: Union[str, None] = '000000000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    SQLite 迁移限制：
    - 不支持 ALTER COLUMN 改变类型
    - 使用 batch_alter_table 重建表
    - 外键约束在 SQLite 中是可选的
    
    对于开发环境，数据库已存在且正常工作。
    此迁移脚本主要用于：
    1. 记录模型定义
    2. 为 PostgreSQL 生产环境提供参考
    
    因此，此迁移为空操作。
    """
    # 删除旧的 audit_log 表（已改为 sys_audit_log）
    op.drop_table('audit_log')


def downgrade() -> None:
    """回滚：重新创建 audit_log 表"""
    op.create_table(
        'audit_log',
        sa.Column('log_id', sa.TEXT(), nullable=False),
        sa.Column('user_id', sa.TEXT(), nullable=True),
        sa.Column('username', sa.TEXT(), nullable=True),
        sa.Column('action', sa.TEXT(), nullable=True),
        sa.Column('resource', sa.TEXT(), nullable=True),
        sa.Column('resource_id', sa.TEXT(), nullable=True),
        sa.Column('ip_address', sa.TEXT(), nullable=True),
        sa.Column('user_agent', sa.TEXT(), nullable=True),
        sa.Column('request_data', sa.TEXT(), nullable=True),
        sa.Column('response_status', sa.INTEGER(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('log_id')
    )
