"""审计日志模型"""
from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.db.session import Base


class AuditLog(Base):
    """系统操作审计日志（合规要求）"""
    __tablename__ = "audit_log"

    log_id = Column(String(36), primary_key=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(String(36), nullable=False)
    username = Column(String(50), nullable=False)
    user_role = Column(String(20), nullable=True)

    action = Column(String(50), nullable=False)          # CREATE/READ/UPDATE/DELETE/LOGIN/LOGOUT
    resource = Column(String(50), nullable=False)        # patient/followup/referral/assessment/alert/user
    resource_id = Column(String(36), nullable=True)

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    request_method = Column(String(10), nullable=True)   # GET/POST/PUT/DELETE
    request_path = Column(String(255), nullable=True)
    response_status = Column(String(10), nullable=True)  # success/error/denied

    details = Column(JSON, nullable=True)                # 变更详情（before/after）
    is_sensitive = Column(String(1), default='N')       # Y=敏感操作（涉及PII）

    session_id = Column(String(100), nullable=True)
