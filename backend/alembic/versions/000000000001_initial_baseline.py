"""Initial migration (baseline for existing database)

Revision ID: 000000000001
Revises: 
Create Date: 2026-05-22 22:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '000000000001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Initial migration - baseline for existing database.
    All tables already exist in the production database.
    No operations needed here.
    """
    pass


def downgrade() -> None:
    """
    Downgrade - drop all tables (for development only).
    """
    # 注意：这是破坏性操作，仅用于开发环境重置数据库
    tables = [
        'sys_audit_log', 'kpi_org_stats', 'followup_reminder',
        'followup_diabetes', 'followup_hypertension', 'followup_record',
        'emergency_alert', 'tcm_record', 'patient_self_report',
        'referral_record', 'annual_assessment', 'alert_record',
        'disease_ckd', 'disease_copd', 'disease_coronary_heart_disease',
        'disease_diabetes', 'disease_hypertension', 'disease_stroke',
        'patient_wechat', 'patient', 'dim_drug', 'dim_disease_type',
        'dim_region', 'sys_role_permission', 'sys_user'
    ]
    
    for table in tables:
        op.drop_table(table)
