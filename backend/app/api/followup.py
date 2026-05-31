"""
随访管理路由 - CRUD 操作
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from sqlalchemy import extract as sqlextract
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.db.session import get_db
from app.models import FollowupRecord, Patient, SysUser  # 从 models/__init__.py 导入
from app.schemas.followup import (
    FollowupCreate, FollowupUpdate, FollowupResponse,
    FollowupSearchParams, FollowupStats, PaginatedFollowupResponse
)
from app.dependencies.auth import require_roles, get_current_active_user
from app.services.encryption_service import get_encryption_service
from app.utils.constants import enc, ORG_NAME_MAP, DISEASE_NAME_MAP, get_org_name, get_disease_name
from app.utils.data_permission import build_org_filter
from app.utils.cache import get as cache_get, set as cache_set, invalidate, DASHBOARD_STATS_KEY, DASHBOARD_KPI_KEY

router = APIRouter()


@router.post("")
@router.post("/", response_model=FollowupResponse, status_code=201, dependencies=[Depends(require_roles('ADMIN', 'DOCTOR', 'NURSE'))])
async def create_followup(
        followup: FollowupCreate,
        current_user: SysUser = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
):
    """
    创建新的随访记录
    - 检查患者是否存在
    - 生成随访编号
    - 创建随访记录
    """
    # 检查患者是否存在
    patient_result = await db.execute(
        select(Patient).where(Patient.patient_id == followup.patient_id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # 获取该患者的随访次数，生成随访编号
    followup_count_result = await db.execute(
        select(func.count(FollowupRecord.followup_id)).where(
            FollowupRecord.patient_id == followup.patient_id,
            FollowupRecord.disease_code == followup.disease_code
        )
    )
    followup_no = followup_count_result.scalar() + 1

    # 创建随访记录
    db_followup = FollowupRecord(
        patient_id=followup.patient_id,
        disease_code=followup.disease_code,
        followup_no=followup_no,
        followup_type=followup.followup_type,
        followup_date=followup.followup_date,
        performed_by=current_user.username,
        org_code=followup.org_code,
        bp_systolic=followup.bp_systolic,
        bp_diastolic=followup.bp_diastolic,
        fbg=followup.fbg,
        pbg=followup.pbg,
        hba1c=followup.hba1c,
        ldl_c=followup.ldl_c,
        hdl_c=followup.hdl_c,
        tc=followup.tc,
        tg=followup.tg,
        weight=followup.weight,
        bmi=followup.bmi,
        heart_rate=followup.heart_rate,
        medication_adherence=followup.medication_adherence,
        is_controlled=followup.is_controlled,
        next_followup_date=followup.next_followup_date,
        symptoms=followup.symptoms,
        signs=followup.signs,
        medication_changed=followup.medication_changed,
        medication_note=followup.medication_note,
        location_lat=followup.location_lat,
        location_lng=followup.location_lng,
        audio_record_url=followup.audio_record_url,
        device_data=followup.device_data
    )

    db.add(db_followup)
    await db.commit()

    # 清除仪表盘缓存
    invalidate(DASHBOARD_STATS_KEY)
    await db.refresh(db_followup)

    return db_followup


@router.get("")
@router.get("/", dependencies=[Depends(require_roles("ADMIN", "DOCTOR", "NURSE"))])
async def list_followups(
        patient_id: Optional[str] = Query(None),
        disease_code: Optional[str] = Query(None),
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        performed_by: Optional[str] = Query(None),
        org_code: Optional[str] = Query(None),
        is_controlled: Optional[bool] = Query(None),
        is_audited: Optional[bool] = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        current_user: SysUser = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
):
    """
    查询随访记录列表（支持多条件筛选，分页返回）
    """
    # 构建基础查询
    base_query = select(FollowupRecord)
    count_query = select(func.count(FollowupRecord.followup_id))

    # ===== 数据权限过滤 =====
    org_filter = build_org_filter(FollowupRecord.org_code, current_user)
    if org_filter is not None:
        base_query = base_query.where(org_filter)
        count_query = count_query.where(org_filter)

    # 应用筛选条件
    if patient_id:
        base_query = base_query.where(FollowupRecord.patient_id == patient_id)
        count_query = count_query.where(FollowupRecord.patient_id == patient_id)
    if disease_code:
        base_query = base_query.where(FollowupRecord.disease_code == disease_code)
        count_query = count_query.where(FollowupRecord.disease_code == disease_code)
    if start_date:
        base_query = base_query.where(FollowupRecord.followup_date >= start_date)
        count_query = count_query.where(FollowupRecord.followup_date >= start_date)
    if end_date:
        base_query = base_query.where(FollowupRecord.followup_date <= end_date)
        count_query = count_query.where(FollowupRecord.followup_date <= end_date)
    if performed_by:
        base_query = base_query.where(FollowupRecord.performed_by == performed_by)
        count_query = count_query.where(FollowupRecord.performed_by == performed_by)
    if org_code:
        base_query = base_query.where(FollowupRecord.org_code == org_code)
        count_query = count_query.where(FollowupRecord.org_code == org_code)
    if is_controlled is not None:
        base_query = base_query.where(FollowupRecord.is_controlled == is_controlled)
        count_query = count_query.where(FollowupRecord.is_controlled == is_controlled)
    if is_audited is not None:
        base_query = base_query.where(FollowupRecord.is_audited == is_audited)
        count_query = count_query.where(FollowupRecord.is_audited == is_audited)

    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页（JOIN 患者表获取姓名）
    skip = (page - 1) * page_size
    query = select(FollowupRecord, Patient.name_enc.label("patient_name"))\
        .outerjoin(Patient, FollowupRecord.patient_id == Patient.patient_id)\
        .offset(skip).limit(page_size).order_by(FollowupRecord.followup_date.desc())

    result = await db.execute(query)
    rows = result.all()

    # 批量解密患者姓名 + 机构名称映射
    items = []
    for row in rows:
        followup = row[0]
        name_enc = row[1]
        # 解密姓名
        if name_enc:
            try:
                patient_name = enc.decrypt(name_enc)
            except Exception:
                patient_name = str(followup.patient_id)
        else:
            patient_name = str(followup.patient_id)
        # 机构名称
        org_name = ORG_NAME_MAP.get(followup.org_code, followup.org_code or '-')
        data = {**{k: v for k, v in followup.__dict__.items() if not k.startswith('_')},
                "patient_name": patient_name, "org_name": org_name}
        items.append(data)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{followup_id}", response_model=FollowupResponse, dependencies=[Depends(require_roles("ADMIN", "DOCTOR", "NURSE"))])
async def get_followup(
        followup_id: str,
        db: AsyncSession = Depends(get_db)
):
    """
    根据 ID 获取随访记录详情（带缓存）
    """
    # 检查缓存
    cache_key = f"followup:{followup_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    
    # JOIN 查询获取患者姓名（加密字段 name_enc）
    result = await db.execute(
        select(FollowupRecord, Patient.name_enc.label("patient_name"))
        .outerjoin(Patient, FollowupRecord.patient_id == Patient.patient_id)
        .where(FollowupRecord.followup_id == followup_id)
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="随访记录不存在")

    followup = row[0]
    patient_name = row[1]

    # 转为 dict 并附加患者姓名
    data = {
        **{k: v for k, v in followup.__dict__.items() if not k.startswith('_')},
        "patient_name": patient_name,
    }
    
    # 缓存结果（60秒）
    cache_set(cache_key, data, ttl=60)
    
    return data


@router.put("/{followup_id}", response_model=FollowupResponse, dependencies=[Depends(require_roles("ADMIN", "DOCTOR", "NURSE"))])
async def update_followup(
        followup_id: str,
        followup_update: FollowupUpdate,
        db: AsyncSession = Depends(get_db)
):
    """
    更新随访记录
    """
    result = await db.execute(
        select(FollowupRecord).where(FollowupRecord.followup_id == followup_id)
    )
    db_followup = result.scalar_one_or_none()

    if not db_followup:
        raise HTTPException(status_code=404, detail="随访记录不存在")

    # 更新非空字段
    update_data = followup_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_followup, field, value)

    await db.commit()

    # 清除相关缓存
    invalidate(DASHBOARD_STATS_KEY)
    invalidate(f"followup:{followup_id}")
    await db.refresh(db_followup)

    return db_followup


@router.post("/{followup_id}/audit")
async def audit_followup(
        followup_id: str,
        audit_note: Optional[str] = None,
        current_user: SysUser = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
):
    """
    审核随访记录
    """
    result = await db.execute(
        select(FollowupRecord).where(FollowupRecord.followup_id == followup_id)
    )
    db_followup = result.scalar_one_or_none()

    if not db_followup:
        raise HTTPException(status_code=404, detail="随访记录不存在")

    # 标记为已审核
    db_followup.is_audited = True
    db_followup.audited_by = current_user.username,
    db_followup.audited_at = func.now()
    db_followup.audit_note = audit_note

    await db.commit()

    # 清除相关缓存
    invalidate(DASHBOARD_STATS_KEY)
    invalidate(f"followup:{followup_id}")

    return {"message": "随访记录已审核"}


@router.get("/export")
async def export_followups(
        patient_id: Optional[str] = Query(None),
        disease_code: Optional[str] = Query(None),
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        performed_by: Optional[str] = Query(None),
        org_code: Optional[str] = Query(None),
        is_controlled: Optional[bool] = Query(None),
        is_audited: Optional[bool] = Query(None),
        _=Depends(require_roles("ADMIN", "DOCTOR", "NURSE")),
        db: AsyncSession = Depends(get_db)
):
    """
    导出随访记录（CSV格式）
    """
    from datetime import datetime
    from sqlalchemy import case
    
    # 构建查询（复用 list_followups 的逻辑）
    query = select(FollowupRecord, Patient.name_enc.label("patient_name_enc")) \
        .outerjoin(Patient, FollowupRecord.patient_id == Patient.patient_id)
    
    # 应用筛选条件
    if patient_id:
        query = query.where(FollowupRecord.patient_id == patient_id)
    if disease_code:
        query = query.where(FollowupRecord.disease_code == disease_code)
    if start_date:
        query = query.where(FollowupRecord.followup_date >= start_date)
    if end_date:
        query = query.where(FollowupRecord.followup_date <= end_date)
    if performed_by:
        query = query.where(FollowupRecord.performed_by == performed_by)
    if org_code:
        query = query.where(FollowupRecord.org_code == org_code)
    if is_controlled is not None:
        query = query.where(FollowupRecord.is_controlled == is_controlled)
    if is_audited is not None:
        query = query.where(FollowupRecord.is_audited == is_audited)
    
    query = query.order_by(FollowupRecord.followup_date.desc())
    
    # 执行查询
    result = await db.execute(query)
    rows = result.all()
    
    # 获取加密服务
    encryption_service = enc
    
    # 生成 CSV
    csv_lines = [
        "随访ID,患者ID,患者姓名,随访次数,疾病代码,随访类型,随访日期,执行人,机构代码,"
        "收缩压,舒张压,空腹血糖,餐后血糖,HbA1c,LDL-C,HDL-C,总胆固醇,甘油三酯,体重,BMI,心率,"
        "用药依从性,是否达标,下次随访日期,症状,体征,是否审核,审核人,审核时间"
    ]
    
    for row in rows:
        followup = row[0]
        patient_name_enc = row[1]
        
        # 解密患者姓名
        patient_name = ""
        try:
            if patient_name_enc:
                patient_name = enc.decrypt(patient_name_enc)
        except:
            patient_name = "[解密失败]"
        
        # 随访类型映射
        followup_type_map = {
            "REGULAR": "定期随访",
            "FIRST_VISIT": "首次随访",
            "EMERGENCY": "急诊随访",
            "PHONE": "电话随访",
            "WECHAT": "微信随访"
        }
        followup_type_text = followup_type_map.get(followup.followup_type, followup.followup_type)
        
        # 用药依从性映射
        adherence_map = {
            "GOOD": "良好",
            "MODERATE": "中等",
            "POOR": "较差"
        }
        adherence_text = adherence_map.get(followup.medication_adherence, "") if followup.medication_adherence else ""
        
        # 构建 CSV 行
        csv_row = ",".join([
            followup.followup_id or "",
            followup.patient_id or "",
            f'"{patient_name}"' if ',' in patient_name or '"' in patient_name else patient_name,
            str(followup.followup_no or ""),
            followup.disease_code or "",
            followup_type_text,
            str(followup.followup_date or ""),
            followup.performed_by or "",
            followup.org_code or "",
            str(followup.bp_systolic or ""),
            str(followup.bp_diastolic or ""),
            str(followup.fbg or ""),
            str(followup.pbg or ""),
            str(followup.hba1c or ""),
            str(followup.ldl_c or ""),
            str(followup.hdl_c or ""),
            str(followup.tc or ""),
            str(followup.tg or ""),
            str(followup.weight or ""),
            str(followup.bmi or ""),
            str(followup.heart_rate or ""),
            adherence_text,
            "是" if followup.is_controlled else "否" if followup.is_controlled is not None else "",
            str(followup.next_followup_date or ""),
            followup.symptoms or "",
            followup.signs or "",
            "是" if followup.is_audited else "否" if followup.is_audited is not None else "",
            followup.audited_by or "",
            str(followup.audited_at or "")
        ])
        csv_lines.append(csv_row)
    
    return {
        "reportText": "\n".join(csv_lines),
        "format": "csv",
        "totalRecords": len(rows),
        "exportTime": datetime.now().isoformat()
    }


@router.get("/stats/summary", response_model=FollowupStats)
async def get_followup_stats(
        org_code: Optional[str] = Query(None),
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        db: AsyncSession = Depends(get_db)
):
    """
    获取随访统计信息
    """
    from sqlalchemy import case
    
    # 构建筛选条件
    filters = []
    if org_code:
        filters.append(FollowupRecord.org_code == org_code)
    if start_date:
        filters.append(FollowupRecord.followup_date >= start_date)
    if end_date:
        filters.append(FollowupRecord.followup_date <= end_date)
    
    # total_followups: 总随访次数
    total_result = await db.execute(
        select(func.count(FollowupRecord.followup_id)).where(and_(*filters) if filters else True)
    )
    total_followups = total_result.scalar() or 0
    
    # by_disease: 按疾病分组
    disease_result = await db.execute(
        select(FollowupRecord.disease_code, func.count(FollowupRecord.followup_id))
        .where(and_(*filters) if filters else True)
        .group_by(FollowupRecord.disease_code)
    )
    by_disease = {row[0]: row[1] for row in disease_result.all() if row[0]}
    
    # by_org: 按机构分组
    org_result = await db.execute(
        select(FollowupRecord.org_code, func.count(FollowupRecord.followup_id))
        .where(and_(*filters) if filters else True)
        .group_by(FollowupRecord.org_code)
    )
    by_org = {row[0]: row[1] for row in org_result.all() if row[0]}
    
    # by_month: 按月分组
    # 使用 EXTRACT 或 strftime 兼容不同数据库
    try:
        # PostgreSQL
        from sqlalchemy.dialects.postgresql import extract
        month_expr = func.to_char(FollowupRecord.followup_date, 'YYYY-MM')
    except ImportError:
        # SQLite
        month_expr = func.strftime('%Y-%m', FollowupRecord.followup_date)
    
    month_result = await db.execute(
        select(month_expr.label('month'), func.count(FollowupRecord.followup_id))
        .where(and_(*filters) if filters else True)
        .group_by(month_expr)
        .order_by(month_expr)
    )
    by_month = {row[0]: row[1] for row in month_result.all() if row[0]}
    
    # controlled_rate: 控制率（is_controlled 为 True 的比例）
    controlled_result = await db.execute(
        select(
            func.avg(case((FollowupRecord.is_controlled == True, 1), else_=0))
        ).where(and_(*filters) if filters else True)
    )
    controlled_rate = controlled_result.scalar() or 0.0
    
    # avg_bp_systolic, avg_bp_diastolic, avg_fbg: 平均值
    avg_systolic_result = await db.execute(
        select(func.avg(FollowupRecord.bp_systolic))
        .where(and_(*filters) if filters else True)
        .where(FollowupRecord.bp_systolic.isnot(None))
    )
    avg_bp_systolic = avg_systolic_result.scalar()
    
    avg_diastolic_result = await db.execute(
        select(func.avg(FollowupRecord.bp_diastolic))
        .where(and_(*filters) if filters else True)
        .where(FollowupRecord.bp_diastolic.isnot(None))
    )
    avg_bp_diastolic = avg_diastolic_result.scalar()
    
    avg_fbg_result = await db.execute(
        select(func.avg(FollowupRecord.fbg))
        .where(and_(*filters) if filters else True)
        .where(FollowupRecord.fbg.isnot(None))
    )
    avg_fbg = avg_fbg_result.scalar()
    
    # pending_audit: 待审核数量
    pending_result = await db.execute(
        select(func.count(FollowupRecord.followup_id))
        .where(and_(*filters) if filters else True)
        .where(FollowupRecord.is_audited == False)
    )
    pending_audit = pending_result.scalar() or 0
    
    return {
        "total_followups": total_followups,
        "by_disease": by_disease,
        "by_org": by_org,
        "by_month": by_month,
        "controlled_rate": float(controlled_rate) if controlled_rate else 0.0,
        "avg_bp_systolic": float(avg_bp_systolic) if avg_bp_systolic else None,
        "avg_bp_diastolic": float(avg_bp_diastolic) if avg_bp_diastolic else None,
        "avg_fbg": float(avg_fbg) if avg_fbg else None,
        "pending_audit": pending_audit
    }


@router.get("/patient/{patient_id}/latest")
async def get_latest_followup(
        patient_id: str,
        disease_code: Optional[str] = Query(None),
        db: AsyncSession = Depends(get_db)
):
    """
    获取患者最近一次随访记录
    """
    query = select(FollowupRecord).where(FollowupRecord.patient_id == patient_id)

    if disease_code:
        query = query.where(FollowupRecord.disease_code == disease_code)

    query = query.order_by(FollowupRecord.followup_date.desc()).limit(1)

    result = await db.execute(query)
    followup = result.scalar_one_or_none()

    if not followup:
        raise HTTPException(status_code=404, detail="该患者无随访记录")

    return followup
