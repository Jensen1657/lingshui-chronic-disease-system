"""
中医管理路由 - CRUD 操作
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.db.session import get_db
from app.dependencies.auth import require_roles
from app.models import TcmRecord, Patient
from app.schemas.tcm import (
    TcmCreate, TcmUpdate, TcmResponse,
    TcmSearchParams, TcmStats, PaginatedTcmResponse
)
from app.services.encryption_service import encryption_service
from app.utils.constants import enc, ORG_NAME_MAP, DISEASE_NAME_MAP, get_org_name, get_disease_name
from app.utils.cache import get as cache_get, set as cache_set, invalidate, DASHBOARD_STATS_KEY, DASHBOARD_KPI_KEY

# 机构名称映射（陵水县13家机构）

router = APIRouter()


@router.post("/", response_model=TcmResponse, status_code=201)
async def create_tcm_record(
        tcm: TcmCreate,
        db: AsyncSession = Depends(get_db)
):
    """
    创建中医管理记录
    - 检查患者是否存在
    - 创建中医管理记录
    """
    # 检查患者是否存在
    patient_result = await db.execute(
        select(Patient).where(Patient.patient_id == tcm.patient_id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # 创建中医管理记录（支持全部扩展字段）
    create_data = tcm.model_dump(exclude_unset=True)
    db_tcm = TcmRecord(
        recorded_by=create_data.get('recorded_by') or create_data.get('visit_doctor') or None
    )
    for field, value in create_data.items():
        if field not in ('recorded_by', 'visit_doctor') and hasattr(TcmRecord, field):
            setattr(db_tcm, field, value)

    # 处理字段别名（tongue_coating -> tongue_coat, pulse -> pulse_status）
    if hasattr(db_tcm, 'tongue_coating') and not db_tcm.tongue_coat and db_tcm.tongue_coating:
        db_tcm.tongue_coat = db_tcm.tongue_coating
    if hasattr(db_tcm, 'pulse') and not db_tcm.pulse_status and db_tcm.pulse:
        db_tcm.pulse_status = db_tcm.pulse

    # 处理日期别名（visit_date -> record_date）
    if not db_tcm.record_date and db_tcm.visit_date:
        db_tcm.record_date = db_tcm.visit_date

    # 设置默认日期
    if not db_tcm.record_date:
        from datetime import date as date_type
        db_tcm.record_date = date_type.today()

    db.add(db_tcm)
    await db.commit()

    # 清除仪表盘缓存
    invalidate(DASHBOARD_STATS_KEY)
    await db.refresh(db_tcm)

    return db_tcm


@router.get("/")
async def list_tcm_records(
        patient_id: Optional[str] = Query(None),
        disease_code: Optional[str] = Query(None),
        syndrome_type: Optional[str] = Query(None),
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        recorded_by: Optional[str] = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        db: AsyncSession = Depends(get_db)
):
    """
    查询中医管理记录列表（支持多条件筛选，分页返回）
    """
    # 构建基础查询（JOIN Patient 获取患者信息）
    base_query = select(TcmRecord, Patient).outerjoin(
        Patient, TcmRecord.patient_id == Patient.patient_id
    )
    count_query = select(func.count(TcmRecord.tcm_id))

    # 应用筛选条件
    if patient_id:
        base_query = base_query.where(TcmRecord.patient_id == patient_id)
        count_query = count_query.where(TcmRecord.patient_id == patient_id)
    if disease_code:
        base_query = base_query.where(TcmRecord.disease_code == disease_code)
        count_query = count_query.where(TcmRecord.disease_code == disease_code)
    if syndrome_type:
        base_query = base_query.where(TcmRecord.syndrome_type == syndrome_type)
        count_query = count_query.where(TcmRecord.syndrome_type == syndrome_type)
    if start_date:
        base_query = base_query.where(TcmRecord.record_date >= start_date)
        count_query = count_query.where(TcmRecord.record_date >= start_date)
    if end_date:
        base_query = base_query.where(TcmRecord.record_date <= end_date)
        count_query = count_query.where(TcmRecord.record_date <= end_date)
    if recorded_by:
        base_query = base_query.where(TcmRecord.recorded_by == recorded_by)
        count_query = count_query.where(TcmRecord.recorded_by == recorded_by)

    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    offset = (page - 1) * page_size
    query = base_query.offset(offset).limit(page_size).order_by(TcmRecord.record_date.desc())

    result = await db.execute(query)
    rows = result.all()

    # 构造返回数据，包含患者姓名和机构名称
    items = []
    for tcm_row in rows:
        tcm_record = tcm_row[0]
        patient = tcm_row[1]

        # 转为字典
        item = {}
        for col in TcmRecord.__table__.columns:
            item[col.name] = getattr(tcm_record, col.name, None)

        # 添加患者姓名（解密）和机构名称
        if patient:
            item['patient_name'] = enc.decrypt(patient.name_enc) if patient.name_enc else ''
            org_code = getattr(patient, 'manage_org_code', '') or ''
            item['org_name'] = ORG_NAME_MAP.get(org_code, org_code) if org_code else '-'
        else:
            item['patient_name'] = tcm_record.patient_id
            item['org_name'] = '-'

        items.append(item)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{tcm_id}")
async def get_tcm_record(
        tcm_id: str,
        db: AsyncSession = Depends(get_db)
):
    """
    根据 ID 获取中医管理记录详情（带缓存）
    """
    cache_key = f"tcm:{tcm_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    
    result = await db.execute(
        select(TcmRecord, Patient).outerjoin(
            Patient, TcmRecord.patient_id == Patient.patient_id
        ).where(TcmRecord.tcm_id == tcm_id)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="中医管理记录不存在")

    tcm_record, patient = row[0], row[1]

    # 转为字典
    item = {}
    for col in TcmRecord.__table__.columns:
        item[col.name] = getattr(tcm_record, col.name, None)

    # 添加患者姓名和机构名称
    if patient:
        item['patient_name'] = enc.decrypt(patient.name_enc) if patient.name_enc else ''
        org_code = getattr(patient, 'manage_org_code', '') or ''
        item['manage_org_name'] = ORG_NAME_MAP.get(org_code, org_code) if org_code else '-'
    else:
        item['patient_name'] = tcm_record.patient_id
        item['manage_org_name'] = '-'

    cache_set(cache_key, item, ttl=60)
    return item


@router.put("/{tcm_id}")
async def update_tcm_record(
        tcm_id: str,
        tcm_update: TcmUpdate,
        db: AsyncSession = Depends(get_db)
):
    """
    更新中医管理记录
    """
    result = await db.execute(
        select(TcmRecord).where(TcmRecord.tcm_id == tcm_id)
    )
    db_tcm = result.scalar_one_or_none()

    if not db_tcm:
        raise HTTPException(status_code=404, detail="中医管理记录不存在")

    # 更新非空字段
    update_data = tcm_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tcm, field, value)

    await db.commit()

    # 清除仪表盘缓存
    invalidate(DASHBOARD_STATS_KEY)
    invalidate(f"tcm:{tcm_id}")
    await db.refresh(db_tcm)

    # 返回完整数据（含 patient_name）
    item = {}
    for col in TcmRecord.__table__.columns:
        item[col.name] = getattr(db_tcm, col.name, None)

    # 获取患者信息
    patient_result = await db.execute(
        select(Patient).where(Patient.patient_id == db_tcm.patient_id)
    )
    patient = patient_result.scalar_one_or_none()
    if patient:
        item['patient_name'] = enc.decrypt(patient.name_enc) if patient.name_enc else ''
        org_code = getattr(patient, 'manage_org_code', '') or ''
        item['manage_org_name'] = ORG_NAME_MAP.get(org_code, org_code) if org_code else '-'
    else:
        item['patient_name'] = db_tcm.patient_id
        item['manage_org_name'] = '-'

    return item


@router.delete("/{tcm_id}")
async def delete_tcm_record(
        tcm_id: str,
        db: AsyncSession = Depends(get_db)
):
    """
    删除中医管理记录
    """
    result = await db.execute(
        select(TcmRecord).where(TcmRecord.tcm_id == tcm_id)
    )
    db_tcm = result.scalar_one_or_none()

    if not db_tcm:
        raise HTTPException(status_code=404, detail="中医管理记录不存在")

    await db.delete(db_tcm)
    await db.commit()

    # 清除仪表盘缓存
    invalidate(DASHBOARD_STATS_KEY)
    invalidate(f"tcm:{tcm_id}")

    return {"message": "中医管理记录已删除"}


@router.get("/stats/summary", response_model=TcmStats)
async def get_tcm_stats(
        org_code: Optional[str] = Query(None),
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        db: AsyncSession = Depends(get_db)
):
    """
    获取中医管理统计信息
    """
    # TODO: 实际实现需要聚合查询
    # 临时返回示例数据
    return {
        "total_records": 0,
        "by_syndrome_type": {},
        "by_disease": {},
        "by_therapy_type": {},
        "avg_records_per_patient": 0.0
    }


@router.get("/patient/{patient_id}/latest")
async def get_latest_tcm_record(
        patient_id: str,
        disease_code: Optional[str] = Query(None),
        db: AsyncSession = Depends(get_db)
):
    """
    获取患者最新一次中医管理记录
    """
    query = select(TcmRecord).where(TcmRecord.patient_id == patient_id)

    if disease_code:
        query = query.where(TcmRecord.disease_code == disease_code)

    query = query.order_by(TcmRecord.record_date.desc()).limit(1)

    result = await db.execute(query)
    tcm_record = result.scalar_one_or_none()

    if not tcm_record:
        raise HTTPException(status_code=404, detail="该患者无中医管理记录")

    return tcm_record
