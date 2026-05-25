"""审计日志 API 路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta
from app.db.session import get_db
from app.services.audit_log_service import AuditLogService
from app.models.audit_log import AuditLog
from app.dependencies.auth import get_current_active_user, get_admin_user

router = APIRouter(tags=["审计日志"])  # prefix 由 main.py 添加


@router.get("/logs")
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource: Optional[str] = Query(None),
    is_sensitive: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    _=Depends(get_current_active_user),
    db=Depends(get_db),
):
    """查询操作日志（分页）"""
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    logs, total = await AuditLogService.get_logs(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        action=action,
        resource=resource,
        is_sensitive=is_sensitive,
        start_date=start_dt,
        end_date=end_dt,
    )
    return {
        "items": [log_to_dict(log) for log in logs],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/logs/sensitive")
async def get_sensitive_logs(
    days: int = Query(7, ge=1, le=90),
    _=Depends(get_admin_user),  # 仅管理员可查看敏感操作
    db=Depends(get_db),
):
    """获取敏感操作日志（合规检查）"""
    logs = await AuditLogService.get_sensitive_logs(db=db, days=days)
    return {
        "items": [log_to_dict(log) for log in logs],
        "total": len(logs),
        "days": days,
    }


@router.get("/logs/user/{user_id}")
async def get_user_activity(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    _=Depends(get_current_active_user),
    db=Depends(get_db),
):
    """获取用户活动记录"""
    logs = await AuditLogService.get_user_activity(db=db, user_id=user_id, days=days)
    return {
        "items": [log_to_dict(log) for log in logs],
        "total": len(logs),
        "user_id": user_id,
        "days": days,
    }


@router.get("/logs/export")
async def export_audit_logs(
    start_date: str = Query(...),
    end_date: str = Query(...),
    _=Depends(get_admin_user),  # 仅管理员可导出
    db=Depends(get_db),
):
    """导出操作日志（合规审计报告）"""
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)

    logs = await AuditLogService.export_logs(db=db, start_date=start_dt, end_date=end_dt)

    # 生成 CSV 格式报告
    csv_lines = [
        "log_id,timestamp,user_id,username,action,resource,resource_id,ip_address,response_status,is_sensitive",
    ]
    for log in logs:
        csv_lines.append(
            f"{log.log_id},"
            f"{log.timestamp},"
            f"{log.user_id},"
            f"{log.username},"
            f"{log.action},"
            f"{log.resource},"
            f"{log.resource_id or ''},"
            f"{log.ip_address or ''},"
            f"{log.response_status or ''},"
            f"{log.is_sensitive}"
        )

    return {
        "reportText": "\n".join(csv_lines),
        "format": "csv",
        "startDate": start_date,
        "endDate": end_date,
        "totalRecords": len(logs),
    }


@router.get("/stats")
async def get_audit_stats(
    _=Depends(get_current_active_user),
    db=Depends(get_db),
):
    """获取审计统计信息"""
    from sqlalchemy import func, select

    # 总日志数
    total = (await db.execute(select(func.count(AuditLog.log_id)))).scalar() or 0

    # 今日日志数
    from datetime import date as _date
    today = (await db.execute(
        select(func.count(AuditLog.log_id)).where(
            func.date(AuditLog.timestamp) == str(_date.today())
        )
    )).scalar() or 0

    # 敏感操作数（近7天）
    week_ago = datetime.now() - timedelta(days=7)
    sensitive = (await db.execute(
        select(func.count(AuditLog.log_id)).where(
            AuditLog.is_sensitive == 'Y',
            AuditLog.timestamp >= week_ago,
        )
    )).scalar() or 0

    # 活跃用户数（近30天）
    month_ago = datetime.now() - timedelta(days=30)
    active_users = (await db.execute(
        select(func.count(func.distinct(AuditLog.user_id))).where(
            AuditLog.timestamp >= month_ago
        )
    )).scalar() or 0

    return {
        "totalLogs": total,
        "todayLogs": today,
        "sensitiveOperations": sensitive,
        "activeUsers": active_users,
    }


def log_to_dict(log: AuditLog) -> dict:
    """将 AuditLog 模型转换为字典"""
    return {
        "logId": log.log_id,
        "timestamp": str(log.timestamp),
        "userId": log.user_id,
        "username": log.username,
        "userRole": log.user_role,
        "action": log.action,
        "resource": log.resource,
        "resourceId": log.resource_id,
        "ipAddress": log.ip_address,
        "requestMethod": log.request_method,
        "requestPath": log.request_path,
        "responseStatus": log.response_status,
        "details": log.details,
        "isSensitive": log.is_sensitive,
        "sessionId": log.session_id,
    }
