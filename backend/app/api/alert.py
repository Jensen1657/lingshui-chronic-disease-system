"""
预警管理路由 - CRUD 操作
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from app.utils.constants import enc, ORG_NAME_MAP
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.dependencies.auth import require_roles, get_current_active_user
from app.models import AlertRecord, Patient, SysUser  # 从 models/__init__.py 导入
from app.schemas.alert import (
    AlertCreate, AlertUpdate, AlertResponse,
    AlertSearchParams, AlertStats, AlertBatchHandle, PaginatedAlertResponse
)
from app.utils.data_permission import build_org_filter
from app.utils.cache import get as cache_get, set as cache_set, invalidate, DASHBOARD_STATS_KEY, DASHBOARD_KPI_KEY

router = APIRouter()


@router.post("/", response_model=AlertResponse, status_code=201)
async def create_alert(
        alert: AlertCreate,
        db: AsyncSession = Depends(get_db)
):
    """
    创建预警记录
    """
    db_alert = AlertRecord(
        patient_id=alert.patient_id,
        org_code=alert.org_code,
        alert_type=alert.alert_type,
        alert_level=alert.alert_level,
        alert_title=alert.alert_title,
        alert_content=alert.alert_content,
        is_handled=False
    )

    db.add(db_alert)
    await db.commit()

    # 清除仪表盘缓存
    invalidate(DASHBOARD_STATS_KEY)
    await db.refresh(db_alert)

    return db_alert


@router.get("/")
async def list_alerts(
        patient_id: Optional[str] = Query(None),
        org_code: Optional[str] = Query(None),
        alert_type: Optional[str] = Query(None),
        alert_level: Optional[str] = Query(None),
        is_handled: Optional[bool] = Query(None),
        start_date: Optional[datetime] = Query(None),
        end_date: Optional[datetime] = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        current_user: SysUser = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
):
    """
    查询预警记录列表（支持多条件筛选，分页返回）
    """
    # 构建基础查询
    base_query = select(AlertRecord)
    count_query = select(func.count(AlertRecord.alert_id))

    # ===== 数据权限过滤 =====
    org_filter = build_org_filter(AlertRecord.org_code, current_user)
    if org_filter is not None:
        base_query = base_query.where(org_filter)
        count_query = count_query.where(org_filter)

    # 应用筛选条件
    if patient_id:
        base_query = base_query.where(AlertRecord.patient_id == patient_id)
        count_query = count_query.where(AlertRecord.patient_id == patient_id)
    if org_code:
        base_query = base_query.where(AlertRecord.org_code == org_code)
        count_query = count_query.where(AlertRecord.org_code == org_code)
    if alert_type:
        base_query = base_query.where(AlertRecord.alert_type == alert_type)
        count_query = count_query.where(AlertRecord.alert_type == alert_type)
    if alert_level:
        base_query = base_query.where(AlertRecord.alert_level == alert_level)
        count_query = count_query.where(AlertRecord.alert_level == alert_level)
    if is_handled is not None:
        base_query = base_query.where(AlertRecord.is_handled == is_handled)
        count_query = count_query.where(AlertRecord.is_handled == is_handled)
    if start_date:
        base_query = base_query.where(AlertRecord.created_at >= start_date)
        count_query = count_query.where(AlertRecord.created_at >= start_date)
    if end_date:
        base_query = base_query.where(AlertRecord.created_at <= end_date)
        count_query = count_query.where(AlertRecord.created_at <= end_date)
    
    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    skip = (page - 1) * page_size
    query = select(AlertRecord, Patient.name_enc.label("patient_name_enc"))\
        .outerjoin(Patient, AlertRecord.patient_id == Patient.patient_id)\
        .offset(skip).limit(page_size).order_by(AlertRecord.created_at.desc())
    
    result = await db.execute(query)
    rows = result.all()
    

    items = []
    for row in rows:
        alert = row[0]
        name_enc = row[1]
        patient_name = None
        if name_enc:
            try:
                patient_name = enc.decrypt(name_enc)
            except Exception:
                patient_name = str(alert.patient_id)
        else:
            patient_name = str(alert.patient_id)
        org_name = ORG_NAME_MAP.get(alert.org_code, alert.org_code or "-") if alert.org_code else "-"
        data = {**{k: v for k, v in alert.__dict__.items() if not k.startswith('_')},
                "patient_name": patient_name, "org_name": org_name}
        items.append(data)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{alert_id}")
async def get_alert(
        alert_id: str,
        db: AsyncSession = Depends(get_db)
):
    """
    根据 ID 获取预警记录详情（带缓存）
    """
    # 检查缓存
    cache_key = f"alert:{alert_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    
    result = await db.execute(
        select(AlertRecord).where(AlertRecord.alert_id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="预警记录不存在")

    # 转为dict缓存
    data = {k: v for k, v in alert.__dict__.items() if not k.startswith('_')}
    cache_set(cache_key, data, ttl=60)
    return data


@router.post("/{alert_id}/handle", dependencies=[Depends(require_roles('ADMIN', 'DOCTOR'))])
async def handle_alert(
        alert_id: str,
        handle_note: Optional[str] = None,
        current_user: SysUser = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
):
    """
    处理预警（标记为已处理）
    """
    from uuid import UUID
    
    try:
        alert_id_uuid = UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的预警ID")
    
    result = await AlertService.process_alert(db, alert_id_uuid, current_user, handle_note)
    
    if not result:
        raise HTTPException(status_code=404, detail="预警记录不存在")
    
    # 清除相关缓存
    invalidate(DASHBOARD_STATS_KEY)
    invalidate(f"alert:{alert_id}")

    return {"message": "预警已处理"}


@router.post("/batch-handle")
async def batch_handle_alerts(
        batch_request: AlertBatchHandle,
        current_user: SysUser = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
):
    """
    批量处理预警
    """
    result = await db.execute(
        select(AlertRecord).where(
            AlertRecord.alert_id.in_(batch_request.alert_ids),
            AlertRecord.is_handled == False
        )
    )
    rows = result.all()

    if not alerts:
        raise HTTPException(status_code=404, detail="未找到待处理的预警记录")

    # 批量标记为已处理
    for alert in alerts:
        alert.is_handled = True
        alert.handled_by = current_user.username
        alert.handled_at = datetime.now()
        alert.handle_note = batch_request.handle_note

    await db.commit()

    # 清除仪表盘缓存
    invalidate(DASHBOARD_STATS_KEY)

    return {"message": f"已处理 {len(alerts)} 条预警"}


@router.get("/stats/summary", response_model=AlertStats)
async def get_alert_stats(
        org_code: Optional[str] = Query(None),
        start_date: Optional[datetime] = Query(None),
        end_date: Optional[datetime] = Query(None),
        db: AsyncSession = Depends(get_db)
):
    """
    获取预警统计信息
    """
    from sqlalchemy import case
    
    # 构建筛选条件
    filters = []
    if org_code:
        filters.append(AlertRecord.org_code == org_code)
    if start_date:
        filters.append(AlertRecord.created_at >= start_date)
    if end_date:
        filters.append(AlertRecord.created_at <= end_date)
    
    # total_alerts: 总预警数
    total_result = await db.execute(
        select(func.count(AlertRecord.alert_id)).where(and_(*filters) if filters else True)
    )
    total_alerts = total_result.scalar() or 0
    
    # by_type: 按预警类型分组
    type_result = await db.execute(
        select(AlertRecord.alert_type, func.count(AlertRecord.alert_id))
        .where(and_(*filters) if filters else True)
        .group_by(AlertRecord.alert_type)
    )
    by_type = {row[0]: row[1] for row in type_result.all() if row[0]}
    
    # by_level: 按预警级别分组
    level_result = await db.execute(
        select(AlertRecord.alert_level, func.count(AlertRecord.alert_id))
        .where(and_(*filters) if filters else True)
        .group_by(AlertRecord.alert_level)
    )
    by_level = {row[0]: row[1] for row in level_result.all() if row[0]}
    
    # by_org: 按机构分组
    org_result = await db.execute(
        select(AlertRecord.org_code, func.count(AlertRecord.alert_id))
        .where(and_(*filters) if filters else True)
        .group_by(AlertRecord.org_code)
    )
    by_org = {row[0]: row[1] for row in org_result.all() if row[0]}
    
    # by_month: 按月分组
    try:
        # PostgreSQL
        month_expr = func.to_char(AlertRecord.created_at, 'YYYY-MM')
    except Exception:
        # SQLite
        month_expr = func.strftime('%Y-%m', AlertRecord.created_at)
    
    month_result = await db.execute(
        select(month_expr.label('month'), func.count(AlertRecord.alert_id))
        .where(and_(*filters) if filters else True)
        .group_by(month_expr)
        .order_by(month_expr)
    )
    by_month = {row[0]: row[1] for row in month_result.all() if row[0]}
    
    # handled_count: 已处理数量
    handled_result = await db.execute(
        select(func.count(AlertRecord.alert_id))
        .where(and_(*filters) if filters else True)
        .where(AlertRecord.is_handled == True)
    )
    handled_count = handled_result.scalar() or 0
    
    # unhandled_count: 未处理数量
    unhandled_count = total_alerts - handled_count
    
    # avg_handle_minutes: 平均处理时间（分钟）
    # 需要 handled_at - created_at 的平均值
    try:
        from sqlalchemy import cast, Interval
        # PostgreSQL: EXTRACT(EPOCH FROM (handled_at - created_at))/60
        avg_minutes_result = await db.execute(
            select(
                func.avg(
                    func.extract('epoch', AlertRecord.handled_at - AlertRecord.created_at) / 60
                )
            )
            .where(and_(*filters) if filters else True)
            .where(AlertRecord.is_handled == True)
            .where(AlertRecord.handled_at.isnot(None))
        )
        avg_handle_minutes = avg_minutes_result.scalar()
    except Exception:
        # SQLite: 使用 JulianDay 计算分钟差
        avg_minutes_result = await db.execute(
            select(
                func.avg(
                    (func.julianday(AlertRecord.handled_at) - func.julianday(AlertRecord.created_at)) * 24 * 60
                )
            )
            .where(and_(*filters) if filters else True)
            .where(AlertRecord.is_handled == True)
            .where(AlertRecord.handled_at.isnot(None))
        )
        avg_handle_minutes = avg_minutes_result.scalar()
    
    return {
        "total_alerts": total_alerts,
        "by_type": by_type,
        "by_level": by_level,
        "by_org": by_org,
        "by_month": by_month,
        "handled_count": handled_count,
        "unhandled_count": unhandled_count,
        "avg_handle_minutes": float(avg_handle_minutes) if avg_handle_minutes else None
    }


@router.get("/patient/{patient_id}/unhandled")
async def get_unhandled_alerts(
        patient_id: str,
        db: AsyncSession = Depends(get_db)
):
    """
    获取患者未处理的预警记录
    """
    query = select(AlertRecord).where(
        AlertRecord.patient_id == patient_id,
        AlertRecord.is_handled == False
    ).order_by(AlertRecord.created_at.desc())

    result = await db.execute(query)
    rows = result.all()

    return alerts
