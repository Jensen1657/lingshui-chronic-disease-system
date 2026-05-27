"""
双向转诊闭环管理路由
包含：CRUD + 资格校验 + 超时追踪 + 随访关联 + 统计
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import date, datetime
from uuid import UUID

from app.db.session import get_db
from app.dependencies.auth import require_roles, get_current_active_user
from app.models import ReferralRecord, Patient, SysUser
from app.services.referral_service import ReferralService
from app.services.encryption_service import get_encryption_service
from app.utils.constants import enc, ORG_NAME_MAP, DISEASE_NAME_MAP, get_org_name, get_disease_name
from app.utils.cache import get as cache_get, set as cache_set, invalidate, DASHBOARD_STATS_KEY, DASHBOARD_KPI_KEY
from app.utils.data_permission import build_org_filter

# 机构编码→名称映射（陵水县行政区划）
from app.dependencies.auth import get_current_user
from app.schemas.referral import (
    ReferralCreate, ReferralUpdate, ReferralResponse,
    ReferralSearchParams, ReferralStats, PaginatedReferralResponse
)

router = APIRouter()


# ---------- CRUD ----------

@router.post("/", response_model=ReferralResponse, status_code=201, dependencies=[Depends(require_roles("ADMIN", "DOCTOR"))])
async def create_referral(
    data: ReferralCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建双向转诊（含资格校验）"""
    # 资格校验
    check = await ReferralService.check_eligibility(db, data.patient_id, data.disease_code, data.referral_type)
    if not check["is_eligible"]:
        raise HTTPException(status_code=400, detail=f"不符合转诊条件: {check['reason']}")

    # 验证患者
    patient = (await db.execute(
        select(Patient).where(Patient.patient_id == data.patient_id)
    )).scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    referral = ReferralRecord(
        referral_id=str(uuid.uuid4()),
        patient_id=data.patient_id,
        disease_code=data.disease_code,
        referral_type=data.referral_type,
        apply_org_code=data.apply_org_code,
        receive_org_code=data.receive_org_code or "",
        referral_reason=data.referral_reason,
        match_criteria=check.get("match_criteria", {}),
        is_eligible=True,
        status="PENDING",
    )
    db.add(referral)
    await db.commit()

    # 清除仪表盘缓存
    invalidate(DASHBOARD_STATS_KEY)
    await db.refresh(referral)
    return referral


@router.get("/", dependencies=[Depends(require_roles("ADMIN", "DOCTOR"))])
async def list_referrals(
    patient_id: Optional[str] = None,
    referral_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: SysUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """查询转诊列表（分页）"""
    # 构建基础查询
    base_query = select(ReferralRecord)
    count_query = select(func.count(ReferralRecord.referral_id))

    # ===== 数据权限过滤 =====
    org_filter = build_org_filter(ReferralRecord.apply_org_code, current_user)
    if org_filter is not None:
        base_query = base_query.where(org_filter)
        count_query = count_query.where(org_filter)

    if patient_id:
        base_query = base_query.where(ReferralRecord.patient_id == patient_id)
        count_query = count_query.where(ReferralRecord.patient_id == patient_id)
    if referral_type:
        base_query = base_query.where(ReferralRecord.referral_type == referral_type)
        count_query = count_query.where(ReferralRecord.referral_type == referral_type)
    if status:
        base_query = base_query.where(ReferralRecord.status == status)
        count_query = count_query.where(ReferralRecord.status == status)
    
    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    skip = (page - 1) * page_size
    query = base_query.offset(skip).limit(page_size).order_by(ReferralRecord.apply_at.desc())
    
    result = await db.execute(query)
    referrals = result.scalars().all()
    
    # 批量获取患者姓名
    encryption_service = enc
    patient_ids = list(set(r.patient_id for r in referrals))
    patient_names = {}
    if patient_ids:
        pts = (await db.execute(
            select(Patient).where(Patient.patient_id.in_(patient_ids))
        )).scalars().all()
        for p in pts:
            patient_names[p.patient_id] = enc.decrypt(p.name_enc) if p.name_enc else p.patient_id
    
    # 构建返回数据（补充患者姓名和机构名称）
    items = []
    for r in referrals:
        d = {
            "referral_id": r.referral_id,
            "patient_id": r.patient_id,
            "patient_name": patient_names.get(r.patient_id, r.patient_id),
            "disease_code": r.disease_code,
            "referral_type": r.referral_type,
            "apply_org_code": r.apply_org_code,
            "apply_org_name": ORG_NAME_MAP.get(r.apply_org_code, r.apply_org_code),
            "receive_org_code": r.receive_org_code or "",
            "receive_org_name": ORG_NAME_MAP.get(r.receive_org_code, r.receive_org_code) if r.receive_org_code else "-",
            "status": r.status,
            "apply_at": r.apply_at.isoformat() if r.apply_at else None,
            "is_eligible": r.is_eligible,
            "referral_reason": r.referral_reason,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        items.append(d)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{referral_id}", dependencies=[Depends(require_roles("ADMIN", "DOCTOR"))])
async def get_referral(referral_id: str, db: AsyncSession = Depends(get_db)):
    """获取转诊详情（带缓存）"""
    # 检查缓存
    cache_key = f"referral:{referral_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    
    r = (await db.execute(
        select(ReferralRecord).where(ReferralRecord.referral_id == referral_id)
    )).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="转诊记录不存在")
    
    # 转为dict（用于缓存）
    from sqlalchemy.orm import class_mapper
    columns = [c.key for c in class_mapper(r.__class__).columns]
    result = {c: getattr(r, c) for c in columns}
    
    # 缓存结果（60秒）
    cache_set(cache_key, result, ttl=60)
    
    return result


@router.post("/{referral_id}/accept")
async def accept_referral(
    referral_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """接收机构接受转诊 → 触发通知给申请医生"""
    r = (await db.execute(
        select(ReferralRecord).where(ReferralRecord.referral_id == referral_id)
    )).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="转诊记录不存在")
    if r.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能接受待处理的转诊")
    r.status = "ACCEPTED"
    r.receive_at = datetime.now()
    r.receive_doctor = current_user.get("sub", "")
    await db.commit()

    # 清除相关缓存
    invalidate(DASHBOARD_STATS_KEY)
    invalidate(f"referral:{referral_id}")

    # 🔔 闭环通知：通知申请医生转诊已被接受
    try:
        from app.services.notification_service import NotificationService
        await NotificationService.notify_referral_accepted(db, r, current_user.get("sub", ""))
    except Exception:
        pass  # 通知失败不影响主流程

    return {"message": "转诊已接受", "referral_id": referral_id}


@router.post("/{referral_id}/reject")
async def reject_referral(
    referral_id: str,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """接收机构拒绝转诊 → 触发通知给申请医生"""
    r = (await db.execute(
        select(ReferralRecord).where(ReferralRecord.referral_id == referral_id)
    )).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="转诊记录不存在")
    if r.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能拒绝待处理的转诊")
    r.status = "REJECTED"
    r.reject_reason = reason
    r.receive_doctor = current_user.get("sub", "")
    await db.commit()

    # 清除相关缓存
    invalidate(DASHBOARD_STATS_KEY)
    invalidate(f"referral:{referral_id}")

    # 🔔 闭环通知：通知申请医生转诊已被拒绝
    try:
        from app.services.notification_service import NotificationService
        await NotificationService.notify_referral_rejected(db, r, reason, current_user.get("sub", ""))
    except Exception:
        pass

    return {"message": "转诊已拒绝", "reason": reason}


@router.post("/{referral_id}/complete")
async def complete_referral(
    referral_id: str,
    post_referral_fu_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """完成转诊 → 校验随访关联 + 触发通知"""
    r = (await db.execute(
        select(ReferralRecord).where(ReferralRecord.referral_id == referral_id)
    )).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="转诊记录不存在")
    if r.status != "ACCEPTED":
        raise HTTPException(status_code=400, detail="只能完成已接受的转诊")

    # 建议：完成转诊时关联随访（非强制，但记录提示）
    if post_referral_fu_id:
        fu_result = await db.execute(
            select(FollowupRecord).where(FollowupRecord.followup_id == post_referral_fu_id)
        )
        fu = fu_result.scalar_one_or_none()
        if fu and fu.patient_id == r.patient_id:
            r.post_referral_fu_id = post_referral_fu_id

    r.status = "COMPLETED"
    r.completed_at = datetime.now()
    await db.commit()

    # 清除仪表盘缓存
    invalidate(DASHBOARD_STATS_KEY)

    # 🔔 闭环通知：通知申请医生转诊已完成（可安排下转或随访）
    try:
        from app.services.notification_service import NotificationService
        await NotificationService.notify_referral_completed(db, r, current_user.get("sub", ""))
    except Exception:
        pass

    return {
        "message": "转诊已完成",
        "referral_id": referral_id,
        "post_referral_fu_id": r.post_referral_fu_id,
        "tip": "建议7天内完成转诊后随访" if not r.post_referral_fu_id else "",
    }


# ---------- 闭环功能 ----------

@router.post("/check-eligibility")
async def check_eligibility(
    patient_id: str,
    disease_code: str,
    referral_type: str,
    db: AsyncSession = Depends(get_db),
):
    """转诊资格校验（不创建记录，仅检查）"""
    return await ReferralService.check_eligibility(db, patient_id, disease_code, referral_type)


@router.post("/track-timeouts")
async def track_timeouts(db: AsyncSession = Depends(get_db)):
    """扫描超时转诊（仅返回列表，不写入预警）"""
    return await ReferralService.track_referrals(db)


@router.post("/generate-timeout-alerts")
async def generate_timeout_alerts(db: AsyncSession = Depends(get_db)):
    """扫描超时转诊并自动生成预警记录"""
    count = await ReferralService.generate_timeout_alerts(db)
    return {"message": f"已生成{count}条超时预警", "count": count}


@router.get("/post-fu-overdue")
async def check_post_fu_deadline(db: AsyncSession = Depends(get_db)):
    """查询已完成转诊但未关联随访的逾期记录"""
    return await ReferralService.check_post_fu_deadline(db)


@router.post("/{referral_id}/link-followup")
async def link_followup(
    referral_id: str,
    followup_id: str,
    db: AsyncSession = Depends(get_db),
):
    """将随访记录关联到已完成转诊"""
    return await ReferralService.link_followup(db, referral_id, followup_id)


@router.get("/stats/summary")
async def get_referral_stats(
    org_code: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    """转诊闭环统计"""
    return await ReferralService.get_referral_stats(db, org_code, start_date, end_date)
