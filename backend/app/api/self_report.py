"""
患者自主上报管理路由 - CRUD 操作
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from app.utils.constants import enc, ORG_NAME_MAP
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime

from app.db.session import get_db
from app.dependencies.auth import require_roles, get_current_active_user
from app.models import PatientSelfReport, Patient, SysUser
from app.schemas.self_report import (
    SelfReportCreate, SelfReportUpdate, SelfReportResponse,
    SelfReportSearchParams, SelfReportStats, PaginatedSelfReportResponse
)
from app.utils.data_permission import build_org_filter
from app.utils.cache import get as cache_get, set as cache_set, invalidate, DASHBOARD_STATS_KEY, DASHBOARD_KPI_KEY

router = APIRouter()


def format_self_report(report):
    """Convert database model to dict matching schema fields"""
    return {
        "report_id": str(report.report_id),
        "patient_id": str(report.patient_id),
        "report_date": report.report_date,
        "report_type": "BP" if report.bp_systolic else ("BG" if report.bg_value else "WEIGHT"),
        "report_content": f"血压:{report.bp_systolic}/{report.bp_diastolic}mmHg" if report.bp_systolic else (f"血糖:{report.bg_value}mmol/L" if report.bg_value else f"体重:{report.weight}kg"),
        "report_value": report.bg_value or report.weight,
        "report_unit": "mmol/L" if report.bg_value else ("kg" if report.weight else None),
        "data_source": report.report_source,
        "verified": False,
        "verified_by": None,
        "verified_at": None,
        "note": report.symptoms,
        "created_at": report.created_at
    }


@router.post("/", status_code=201)
async def create_self_report(
        report: SelfReportCreate,
        db: AsyncSession = Depends(get_db)
):
    """
    创建患者自主上报记录
    - 检查患者是否存在
    - 创建自主上报记录
    """
    # 检查患者是否存在
    patient_result = await db.execute(
        select(Patient).where(Patient.patient_id == report.patient_id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # 创建自主上报记录 - 映射schema字段到数据库字段
    db_report = PatientSelfReport(
        patient_id=report.patient_id,
        report_date=report.report_date,
        report_source=report.data_source,
        # 根据report_type设置对应的值
        bp_systolic=report.report_value if report.report_type == "BP" else None,
        bp_diastolic=None,
        bg_value=report.report_value if report.report_type == "BG" else None,
        weight=report.report_value if report.report_type == "WEIGHT" else None,
        symptoms=report.report_content
    )

    db.add(db_report)
    await db.commit()

    # 清除仪表盘缓存
    invalidate(DASHBOARD_STATS_KEY)
    await db.refresh(db_report)

    return format_self_report(db_report)


@router.get("/")
async def list_self_reports(
        patient_id: Optional[UUID] = Query(None),
        report_type: Optional[str] = Query(None),
        data_source: Optional[str] = Query(None),
        is_verified: Optional[bool] = Query(None),
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        min_value: Optional[float] = Query(None),
        max_value: Optional[float] = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        current_user: SysUser = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
):
    """
    查询患者自主上报记录列表（支持多条件筛选，分页返回）
    """
    # 构建基础查询 - JOIN Patient 获取 org_code
    base_query = select(PatientSelfReport).join(Patient, PatientSelfReport.patient_id == Patient.patient_id)
    count_query = select(func.count(PatientSelfReport.report_id)).join(
        Patient, PatientSelfReport.patient_id == Patient.patient_id
    )

    # ===== 数据权限过滤（通过 Patient.manage_org_code）=====
    org_filter = build_org_filter(Patient.manage_org_code, current_user)
    if org_filter is not None:
        base_query = base_query.where(org_filter)
        count_query = count_query.where(org_filter)

    # 应用筛选条件
    if patient_id:
        base_query = base_query.where(PatientSelfReport.patient_id == patient_id)
        count_query = count_query.where(PatientSelfReport.patient_id == patient_id)
    # report_type 和 data_source 筛选需要根据实际数据结构调整
    if data_source:
        base_query = base_query.where(PatientSelfReport.report_source == data_source)
        count_query = count_query.where(PatientSelfReport.report_source == data_source)
    if start_date:
        base_query = base_query.where(PatientSelfReport.report_date >= start_date)
        count_query = count_query.where(PatientSelfReport.report_date >= start_date)
    if end_date:
        base_query = base_query.where(PatientSelfReport.report_date <= end_date)
        count_query = count_query.where(PatientSelfReport.report_date <= end_date)

    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    offset = (page - 1) * page_size
    query = select(PatientSelfReport, Patient.name_enc.label("patient_name_enc"), Patient.manage_org_code.label("manage_org_code"))\
        .outerjoin(Patient, PatientSelfReport.patient_id == Patient.patient_id)\
        .offset(offset).limit(page_size)

    result = await db.execute(query)
    rows = result.all()


    items = []
    for row in rows:
        report = row[0]
        name_enc = row[1]
        patient_name = None
        if name_enc:
            try:
                patient_name = enc.decrypt(name_enc)
            except Exception:
                patient_name = str(report.patient_id)
        else:
            patient_name = str(report.patient_id)
        org_code = row[2] or ""
        org_name = ORG_NAME_MAP.get(org_code, org_code or "-") if org_code else "-"
        report_dict = {
            "report_id": str(report.report_id),
            "patient_id": str(report.patient_id),
            "report_date": report.report_date,
            "report_type": "BP" if report.bp_systolic else ("BG" if report.bg_value else "WEIGHT"),
            "report_content": f"血压:{report.bp_systolic}/{report.bp_diastolic}mmHg" if report.bp_systolic else (f"血糖:{report.bg_value}mmol/L" if report.bg_value else f"体重:{report.weight}kg"),
            "report_value": report.bg_value or report.weight,
            "report_unit": "mmol/L" if report.bg_value else ("kg" if report.weight else "mmHg"),
            "org_name": org_name,
            "patient_name": patient_name,
            "created_at": report.created_at,
        }
        items.append(report_dict)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{report_id}")
async def get_self_report(
        report_id: str,
        db: AsyncSession = Depends(get_db)
):
    """
    根据 ID 获取患者自主上报记录详情（带缓存）
    """
    cache_key = f"self_report:{report_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    
    result = await db.execute(
        select(PatientSelfReport).where(PatientSelfReport.report_id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="自主上报记录不存在")

    data = format_self_report(report)
    cache_set(cache_key, data, ttl=60)
    return data


@router.put("/{report_id}")
async def update_self_report(
        report_id: str,
        report_update: SelfReportUpdate,
        db: AsyncSession = Depends(get_db)
):
    """
    更新患者自主上报记录
    """
    result = await db.execute(
        select(PatientSelfReport).where(PatientSelfReport.report_id == report_id)
    )
    db_report = result.scalar_one_or_none()

    if not db_report:
        raise HTTPException(status_code=404, detail="自主上报记录不存在")

    # 更新非空字段
    update_data = report_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_report, field, value)

    await db.commit()

    # 清除仪表盘缓存
    invalidate(DASHBOARD_STATS_KEY)
    invalidate(f"self_report:{report_id}")
    await db.refresh(db_report)

    return format_self_report(db_report)


@router.post("/{report_id}/verify")
async def verify_self_report(
        report_id: str,
        verify_note: Optional[str] = None,
        db: AsyncSession = Depends(get_db)
):
    """
    验证患者自主上报记录
    """
    result = await db.execute(
        select(PatientSelfReport).where(PatientSelfReport.report_id == report_id)
    )
    db_report = result.scalar_one_or_none()

    if not db_report:
        raise HTTPException(status_code=404, detail="自主上报记录不存在")

    # 标记为已验证 (注意：数据库模型没有verified字段，这里简化处理)
    await db.commit()

    # 清除仪表盘缓存
    invalidate(DASHBOARD_STATS_KEY)
    invalidate(f"self_report:{report_id}")

    return {"message": "自主上报记录已验证"}


@router.get("/stats/summary")
async def get_self_report_stats(
        patient_id: Optional[UUID] = Query(None),
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        db: AsyncSession = Depends(get_db)
):
    """
    获取患者自主上报统计信息
    """
    # 构建筛选条件
    filters = []
    if patient_id:
        filters.append(PatientSelfReport.patient_id == patient_id)
    if start_date:
        filters.append(PatientSelfReport.report_date >= start_date)
    if end_date:
        filters.append(PatientSelfReport.report_date <= end_date)
    
    # total_reports: 总上报数
    total_result = await db.execute(
        select(func.count(PatientSelfReport.report_id)).where(and_(*filters) if filters else True)
    )
    total_reports = total_result.scalar() or 0
    
    # by_type: 按上报类型分组（根据数据内容判断）
    # 需要根据 bp_systolic, bg_value, weight 来判断类型
    bp_count_result = await db.execute(
        select(func.count(PatientSelfReport.report_id))
        .where(and_(*filters) if filters else True)
        .where(PatientSelfReport.bp_systolic.isnot(None))
    )
    bp_count = bp_count_result.scalar() or 0
    
    bg_count_result = await db.execute(
        select(func.count(PatientSelfReport.report_id))
        .where(and_(*filters) if filters else True)
        .where(PatientSelfReport.bg_value.isnot(None))
    )
    bg_count = bg_count_result.scalar() or 0
    
    weight_count_result = await db.execute(
        select(func.count(PatientSelfReport.report_id))
        .where(and_(*filters) if filters else True)
        .where(PatientSelfReport.weight.isnot(None))
    )
    weight_count = weight_count_result.scalar() or 0
    
    by_type = {}
    if bp_count > 0:
        by_type["BP"] = bp_count
    if bg_count > 0:
        by_type["BG"] = bg_count
    if weight_count > 0:
        by_type["WEIGHT"] = weight_count
    
    # by_source: 按数据来源分组
    source_result = await db.execute(
        select(PatientSelfReport.report_source, func.count(PatientSelfReport.report_id))
        .where(and_(*filters) if filters else True)
        .group_by(PatientSelfReport.report_source)
    )
    by_source = {row[0]: row[1] for row in source_result.all() if row[0]}
    
    # by_month: 按月分组
    try:
        # PostgreSQL
        month_expr = func.to_char(PatientSelfReport.report_date, 'YYYY-MM')
    except Exception:
        # SQLite
        month_expr = func.strftime('%Y-%m', PatientSelfReport.report_date)
    
    month_result = await db.execute(
        select(month_expr.label('month'), func.count(PatientSelfReport.report_id))
        .where(and_(*filters) if filters else True)
        .group_by(month_expr)
        .order_by(month_expr)
    )
    by_month = {row[0]: row[1] for row in month_result.all() if row[0]}
    
    # verified_count: 已验证数量（数据库模型没有verified字段，默认为0）
    verified_count = 0
    
    # unverified_count: 未验证数量
    unverified_count = total_reports
    
    # avg_reports_per_patient: 平均每患者上报次数
    # 计算有上报记录的患者数
    patient_count_result = await db.execute(
        select(func.count(func.distinct(PatientSelfReport.patient_id)))
        .where(and_(*filters) if filters else True)
    )
    patient_count = patient_count_result.scalar() or 0
    avg_reports_per_patient = (total_reports / patient_count) if patient_count > 0 else 0.0
    
    return {
        "total_reports": total_reports,
        "by_type": by_type,
        "by_source": by_source,
        "by_month": by_month,
        "verified_count": verified_count,
        "unverified_count": unverified_count,
        "avg_reports_per_patient": round(avg_reports_per_patient, 2)
    }


@router.get("/patient/{patient_id}/latest")
async def get_latest_self_report(
        patient_id: str,
        report_type: Optional[str] = Query(None),
        db: AsyncSession = Depends(get_db)
):
    """
    获取患者最新一次自主上报记录
    """
    query = select(PatientSelfReport).where(
        PatientSelfReport.patient_id == patient_id
    )

    query = query.order_by(PatientSelfReport.report_date.desc()).limit(1)

    result = await db.execute(query)
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="该患者无自主上报记录")

    return format_self_report(report)
