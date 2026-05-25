"""审计日志服务层"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional, Dict, Any
from uuid import uuid4
from datetime import datetime, timedelta
from app.models.audit_log import AuditLog


class AuditLogService:
    """审计日志服务"""

    @staticmethod
    async def log_action(
        db: AsyncSession,
        user_id: str,
        username: str,
        user_role: Optional[str],
        action: str,
        resource: str,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        response_status: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        is_sensitive: str = 'N',
        session_id: Optional[str] = None,
    ) -> AuditLog:
        """记录操作日志"""
        log = AuditLog(
            log_id=str(uuid4()),
            user_id=user_id,
            username=username,
            user_role=user_role,
            action=action,
            resource=resource,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_path=request_path,
            response_status=response_status,
            details=details,
            is_sensitive=is_sensitive,
            session_id=session_id,
        )
        db.add(log)
        await db.flush()
        return log

    @staticmethod
    async def get_logs(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        is_sensitive: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[List[AuditLog], int]:
        """查询操作日志（分页）"""
        query = select(AuditLog)
        count_query = select(func.count(AuditLog.log_id))

        # 过滤条件
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
            count_query = count_query.where(AuditLog.user_id == user_id)
        if action:
            query = query.where(AuditLog.action == action)
            count_query = count_query.where(AuditLog.action == action)
        if resource:
            query = query.where(AuditLog.resource == resource)
            count_query = count_query.where(AuditLog.resource == resource)
        if is_sensitive:
            query = query.where(AuditLog.is_sensitive == is_sensitive)
            count_query = count_query.where(AuditLog.is_sensitive == is_sensitive)
        if start_date:
            query = query.where(AuditLog.timestamp >= start_date)
            count_query = count_query.where(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.where(AuditLog.timestamp <= end_date)
            count_query = count_query.where(AuditLog.timestamp <= end_date)

        # 排序（最新优先）
        query = query.order_by(desc(AuditLog.timestamp))

        # 分页
        query = query.offset(skip).limit(limit)

        logs = (await db.execute(query)).scalars().all()
        total = (await db.execute(count_query)).scalar_one()
        return logs, total

    @staticmethod
    async def get_sensitive_logs(
        db: AsyncSession,
        days: int = 7,
    ) -> List[AuditLog]:
        """获取敏感操作日志（合规检查）"""
        cutoff = datetime.now() - timedelta(days=days)
        query = (
            select(AuditLog)
            .where(
                AuditLog.is_sensitive == 'Y',
                AuditLog.timestamp >= cutoff,
            )
            .order_by(desc(AuditLog.timestamp))
        )
        return (await db.execute(query)).scalars().all()

    @staticmethod
    async def get_user_activity(
        db: AsyncSession,
        user_id: str,
        days: int = 30,
    ) -> List[AuditLog]:
        """获取用户活动记录"""
        cutoff = datetime.now() - timedelta(days=days)
        query = (
            select(AuditLog)
            .where(
                AuditLog.user_id == user_id,
                AuditLog.timestamp >= cutoff,
            )
            .order_by(desc(AuditLog.timestamp))
        )
        return (await db.execute(query)).scalars().all()

    @staticmethod
    async def export_logs(
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
    ) -> List[AuditLog]:
        """导出操作日志（合规审计报告）"""
        query = (
            select(AuditLog)
            .where(
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date,
            )
            .order_by(AuditLog.timestamp)
        )
        return (await db.execute(query)).scalars().all()
