"""
急救联动路由 - CRUD 操作
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.dependencies.auth import require_roles, get_current_active_user
from app.models import EmergencyAlert, Patient, SysUser
from app.schemas.emergency import (
    EmergencyAlertCreate, EmergencyAlertUpdate, EmergencyAlertResponse,
    EmergencyAlertSearchParams, EmergencyAlertStats, PaginatedEmergencyAlertResponse
)
from app.services.encryption_service import encryption_service
from app.utils.constants import enc, ORG_NAME_MAP, DISEASE_NAME_MAP, get_org_name, get_disease_name
from app.utils.cache import get as cache_get, set as cache_set, invalidate, DASHBOARD_STATS_KEY, DASHBOARD_KPI_KEY

# 机构名称映射（陵水县17家机构）

router = APIRouter()


@router.post("")
@router.post("/", response_model=EmergencyAlertResponse, status_code=201)
async def create_emergency_alert(
        alert: EmergencyAlertCreate,
        current_user: SysUser = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
):
    """
    创建急救联动预警
    - 检查患者是否存在
    - 创建急救联动预警记录
    """
    # 检查患者是否存在
    patient_result = await db.execute(
        select(Patient).where(Patient.patient_id == alert.patient_id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # 创建急救联动预警记录
    db_alert = EmergencyAlert(
        patient_id=alert.patient_id,
        alert_type=alert.alert_type,
        trigger_by=current_user.username,
        patient_history=alert.patient_history,
        medications=alert.medications,
        allergies=alert.allergies,
        vital_signs=alert.vital_signs,
        target_org=alert.target_org,
        target_dept=alert.target_dept,
        estimated_arrival=alert.estimated_arrival,
        status='ACTIVATED'
    )

    db.add(db_alert)
    await db.commit()

    # 清除仪表盘缓存
    invalidate(DASHBOARD_STATS_KEY)
    await db.refresh(db_alert)

    return db_alert


@router.get("")
@router.get("/")
async def list_emergency_alerts(
        patient_id: Optional[str] = Query(None),
        alert_type: Optional[str] = Query(None),
        trigger_by: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        start_date: Optional[datetime] = Query(None),
        end_date: Optional[datetime] = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        db: AsyncSession = Depends(get_db)
):
    """
    查询急救联动预警列表（支持多条件筛选，分页返回）
    """
    # 构建基础查询（JOIN Patient 获取患者信息）
    base_query = select(EmergencyAlert, Patient).outerjoin(
        Patient, EmergencyAlert.patient_id == Patient.patient_id
    )
    count_query = select(func.count(EmergencyAlert.alert_id))

    # 应用筛选条件
    if patient_id:
        base_query = base_query.where(EmergencyAlert.patient_id == patient_id)
        count_query = count_query.where(EmergencyAlert.patient_id == patient_id)
    if alert_type:
        base_query = base_query.where(EmergencyAlert.alert_type == alert_type)
        count_query = count_query.where(EmergencyAlert.alert_type == alert_type)
    if trigger_by:
        base_query = base_query.where(EmergencyAlert.trigger_by == trigger_by)
        count_query = count_query.where(EmergencyAlert.trigger_by == trigger_by)
    if status:
        base_query = base_query.where(EmergencyAlert.status == status)
        count_query = count_query.where(EmergencyAlert.status == status)
    if start_date:
        base_query = base_query.where(EmergencyAlert.trigger_at >= start_date)
        count_query = count_query.where(EmergencyAlert.trigger_at >= start_date)
    if end_date:
        base_query = base_query.where(EmergencyAlert.trigger_at <= end_date)
        count_query = count_query.where(EmergencyAlert.trigger_at <= end_date)

    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    offset = (page - 1) * page_size
    query = base_query.offset(offset).limit(page_size).order_by(EmergencyAlert.trigger_at.desc())

    result = await db.execute(query)
    rows = result.all()

    # 构造返回数据，包含患者姓名、机构名称和医生姓名
    items = []
    # 预加载所有相关用户
    all_user_ids = set()
    for row in rows:
        alert = row[0]
        if alert.trigger_by:
            all_user_ids.add(alert.trigger_by)

    user_map = {}
    if all_user_ids:
        user_result = await db.execute(
            select(SysUser).where(SysUser.user_id.in_(all_user_ids))
        )
        for u in user_result.scalars().all():
            user_map[u.user_id] = u.real_name or u.username or u.user_id

    for row in rows:
        alert = row[0]
        patient = row[1]

        # 转为字典
        item = {}
        for col in EmergencyAlert.__table__.columns:
            item[col.name] = getattr(alert, col.name, None)

        # 添加患者信息（解密）和机构名称
        if patient:
            item['patient_name'] = encryption_service.decrypt(patient.name_enc) if patient.name_enc else ''
            org_code = getattr(patient, 'manage_org_code', '') or ''
            item['org_name'] = ORG_NAME_MAP.get(org_code, org_code) if org_code else '-'
        else:
            item['patient_name'] = alert.patient_id
            item['org_name'] = '-'

        # 在管医生（从 trigger_by 获取）
        item['doctor_name'] = user_map.get(alert.trigger_by, alert.trigger_by or '-')

        items.append(item)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{alert_id}")
async def get_emergency_alert(
        alert_id: str,
        db: AsyncSession = Depends(get_db)
):
    """
    根据 ID 获取急救联动预警详情（带缓存）
    """
    cache_key = f"emergency:{alert_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    
    result = await db.execute(
        select(EmergencyAlert, Patient).outerjoin(
            Patient, EmergencyAlert.patient_id == Patient.patient_id
        ).where(EmergencyAlert.alert_id == alert_id)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="急救联动预警不存在")

    alert, patient = row[0], row[1]
    item = {}
    for col in EmergencyAlert.__table__.columns:
        item[col.name] = getattr(alert, col.name, None)

    if patient:
        item['patient_name'] = enc.decrypt(patient.name_enc) if patient.name_enc else ''
        org_code = getattr(patient, 'manage_org_code', '') or ''
        item['manage_org_name'] = ORG_NAME_MAP.get(org_code, org_code) if org_code else '-'
    else:
        item['patient_name'] = alert.patient_id
        item['manage_org_name'] = '-'

    cache_set(cache_key, item, ttl=60)
    return item


@router.put("/{alert_id}")
async def update_emergency_alert(
        alert_id: str,
        alert_update: EmergencyAlertUpdate,
        db: AsyncSession = Depends(get_db)
):
    """
    更新急救联动预警
    """
    result = await db.execute(
        select(EmergencyAlert).where(EmergencyAlert.alert_id == alert_id)
    )
    db_alert = result.scalar_one_or_none()

    if not db_alert:
        raise HTTPException(status_code=404, detail="急救联动预警不存在")

    # 更新非空字段
    update_data = alert_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_alert, field, value)

    await db.commit()

    # 清除仪表盘缓存
    invalidate(DASHBOARD_STATS_KEY)
    invalidate(f"emergency:{alert_id}")
    await db.refresh(db_alert)

    # 返回完整数据
    item = {}
    for col in EmergencyAlert.__table__.columns:
        item[col.name] = getattr(db_alert, col.name, None)

    patient_result = await db.execute(
        select(Patient).where(Patient.patient_id == db_alert.patient_id)
    )
    patient = patient_result.scalar_one_or_none()
    if patient:
        item['patient_name'] = enc.decrypt(patient.name_enc) if patient.name_enc else ''
        org_code = getattr(patient, 'manage_org_code', '') or ''
        item['manage_org_name'] = ORG_NAME_MAP.get(org_code, org_code) if org_code else '-'
    else:
        item['patient_name'] = db_alert.patient_id
        item['manage_org_name'] = '-'

    return item


@router.post("/{alert_id}/cancel")
async def cancel_emergency_alert(
        alert_id: str,
        cancel_reason: Optional[str] = None,
        db: AsyncSession = Depends(get_db)
):
    """
    取消急救联动预警
    """
    result = await db.execute(
        select(EmergencyAlert).where(EmergencyAlert.alert_id == alert_id)
    )
    db_alert = result.scalar_one_or_none()

    if not db_alert:
        raise HTTPException(status_code=404, detail="急救联动预警不存在")

    if db_alert.status != "ACTIVATED":
        raise HTTPException(status_code=400, detail="只能取消已激活的预警")

    # 更新状态为已取消
    db_alert.status = "CANCELLED"

    await db.commit()

    # 清除仪表盘缓存
    invalidate(DASHBOARD_STATS_KEY)
    invalidate(f"emergency:{alert_id}")

    return {"message": "急救联动预警已取消"}


@router.post("/{alert_id}/complete", dependencies=[Depends(require_roles('ADMIN', 'DOCTOR'))])
async def complete_emergency_alert(
        alert_id: str,
        current_user: SysUser = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
):
    """
    完成急救联动预警
    """
    from uuid import UUID
    
    try:
        emergency_id = UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的预警ID")
    
    result = await EmergencyService.process_emergency(db, emergency_id, current_user)
    
    if not result:
        raise HTTPException(status_code=404, detail="急救联动预警不存在")
    
    # 清除仪表盘缓存
    invalidate(DASHBOARD_STATS_KEY)
    invalidate(f"emergency:{alert_id}")

    return {"message": "急救联动预警已完成"}


@router.get("/stats/summary", response_model=EmergencyAlertStats)
async def get_emergency_alert_stats(
        target_org: Optional[str] = Query(None),
        start_date: Optional[datetime] = Query(None),
        end_date: Optional[datetime] = Query(None),
        db: AsyncSession = Depends(get_db)
):
    """
    获取急救联动预警统计信息
    """
    # 构建筛选条件
    filters = []
    if target_org:
        filters.append(EmergencyAlert.target_org == target_org)
    if start_date:
        filters.append(EmergencyAlert.trigger_at >= start_date)
    if end_date:
        filters.append(EmergencyAlert.trigger_at <= end_date)
    
    # total_alerts: 总预警数
    total_result = await db.execute(
        select(func.count(EmergencyAlert.alert_id)).where(and_(*filters) if filters else True)
    )
    total_alerts = total_result.scalar() or 0
    
    # by_type: 按预警类型分组
    type_result = await db.execute(
        select(EmergencyAlert.alert_type, func.count(EmergencyAlert.alert_id))
        .where(and_(*filters) if filters else True)
        .group_by(EmergencyAlert.alert_type)
    )
    by_type = {row[0]: row[1] for row in type_result.all() if row[0]}
    
    # by_status: 按状态分组
    status_result = await db.execute(
        select(EmergencyAlert.status, func.count(EmergencyAlert.alert_id))
        .where(and_(*filters) if filters else True)
        .group_by(EmergencyAlert.status)
    )
    by_status = {row[0]: row[1] for row in status_result.all() if row[0]}
    
    # by_org: 按目标机构分组
    org_result = await db.execute(
        select(EmergencyAlert.target_org, func.count(EmergencyAlert.alert_id))
        .where(and_(*filters) if filters else True)
        .group_by(EmergencyAlert.target_org)
    )
    by_org = {row[0]: row[1] for row in org_result.all() if row[0]}
    
    # by_month: 按月分组
    try:
        # PostgreSQL
        month_expr = func.to_char(EmergencyAlert.trigger_at, 'YYYY-MM')
    except Exception:
        # SQLite
        month_expr = func.strftime('%Y-%m', EmergencyAlert.trigger_at)
    
    month_result = await db.execute(
        select(month_expr.label('month'), func.count(EmergencyAlert.alert_id))
        .where(and_(*filters) if filters else True)
        .group_by(month_expr)
        .order_by(month_expr)
    )
    by_month = {row[0]: row[1] for row in month_result.all() if row[0]}
    
    # avg_response_minutes: 平均响应时间（分钟）
    # 需要计算 COMPLETED 状态的预警从触发到完成的时间
    try:
        # PostgreSQL: EXTRACT(EPOCH FROM (updated_at - trigger_at))/60
        # 假设 completed_at 存储在 updated_at 中，或者需要另外的字段
        # 这里简化为使用 updated_at
        avg_minutes_result = await db.execute(
            select(
                func.avg(
                    func.extract('epoch', EmergencyAlert.updated_at - EmergencyAlert.trigger_at) / 60
                )
            )
            .where(and_(*filters) if filters else True)
            .where(EmergencyAlert.status == 'COMPLETED')
            .where(EmergencyAlert.updated_at.isnot(None))
        )
        avg_response_minutes = avg_minutes_result.scalar()
    except Exception:
        # SQLite: 使用 JulianDay 计算分钟差
        avg_minutes_result = await db.execute(
            select(
                func.avg(
                    (func.julianday(EmergencyAlert.updated_at) - func.julianday(EmergencyAlert.trigger_at)) * 24 * 60
                )
            )
            .where(and_(*filters) if filters else True)
            .where(EmergencyAlert.status == 'COMPLETED')
            .where(EmergencyAlert.updated_at.isnot(None))
        )
        avg_response_minutes = avg_minutes_result.scalar()
    
    # activated_count: 激活数量
    activated_result = await db.execute(
        select(func.count(EmergencyAlert.alert_id))
        .where(and_(*filters) if filters else True)
        .where(EmergencyAlert.status == 'ACTIVATED')
    )
    activated_count = activated_result.scalar() or 0
    
    # completed_count: 完成数量
    completed_result = await db.execute(
        select(func.count(EmergencyAlert.alert_id))
        .where(and_(*filters) if filters else True)
        .where(EmergencyAlert.status == 'COMPLETED')
    )
    completed_count = completed_result.scalar() or 0
    
    # cancelled_count: 取消数量
    cancelled_result = await db.execute(
        select(func.count(EmergencyAlert.alert_id))
        .where(and_(*filters) if filters else True)
        .where(EmergencyAlert.status == 'CANCELLED')
    )
    cancelled_count = cancelled_result.scalar() or 0
    
    return {
        "total_alerts": total_alerts,
        "by_type": by_type,
        "by_status": by_status,
        "by_org": by_org,
        "by_month": by_month,
        "avg_response_minutes": float(avg_response_minutes) if avg_response_minutes else None,
        "activated_count": activated_count,
        "completed_count": completed_count,
        "cancelled_count": cancelled_count
    }


@router.get("/patient/{patient_id}/active")
async def get_active_emergency_alerts(
        patient_id: str,
        db: AsyncSession = Depends(get_db)
):
    """
    获取患者激活中的急救联动预警
    """
    query = select(EmergencyAlert).where(
        EmergencyAlert.patient_id == patient_id,
        EmergencyAlert.status == "ACTIVATED"
    ).order_by(EmergencyAlert.trigger_at.desc())

    result = await db.execute(query)
    alerts = result.scalars().all()

    return alerts
