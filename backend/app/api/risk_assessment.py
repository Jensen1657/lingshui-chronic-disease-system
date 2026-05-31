"""
患者风险评估 & 分级诊疗 API — 叶胜业：全量纳管 + 分级诊疗
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, case
from typing import Optional
from pydantic import BaseModel, Field
from datetime import date, datetime, timedelta

from app.db.session import get_db
from app.models.meeting_models import PatientRiskAssessment
from app.models import Patient, SysUser

router = APIRouter(tags=["风险评估"])


class RiskAssessmentCreate(BaseModel):
    patient_id: str
    risk_score: int
    risk_level: str  # LOW/MEDIUM/HIGH/CRITICAL
    risk_factors: Optional[list] = None
    manage_level: str  # VILLAGE/TOWNSHIP/COUNTY/REFERRAL
    assigned_org: Optional[str] = None
    assigned_doctor: Optional[str] = None
    bp_assessment: Optional[str] = None
    bg_assessment: Optional[str] = None
    lipid_assessment: Optional[str] = None
    kidney_assessment: Optional[str] = None
    compliance_assessment: Optional[str] = None
    followup_frequency: Optional[str] = None
    need_up_referral: bool = False
    referral_note: Optional[str] = None
    assessment_note: Optional[str] = None
    valid_until: Optional[date] = None
    next_assessment_date: Optional[date] = None


class BatchAssessRequest(BaseModel):
    patient_ids: list[str]
    auto_stratify: bool = False  # 是否自动分层


@router.get("/patient/{patient_id}")
async def get_patient_risk(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取患者最新风险评估"""
    result = await db.execute(
        select(PatientRiskAssessment)
        .where(PatientRiskAssessment.patient_id == patient_id)
        .order_by(desc(PatientRiskAssessment.assessed_at))
        .limit(1)
    )
    ra = result.scalar_one_or_none()

    # 同时获取患者基本信息
    p_result = await db.execute(
        select(Patient).where(Patient.patient_id == patient_id)
    )
    p = p_result.scalar_one_or_none()

    if not ra:
        return {
            "patient_id": patient_id,
            "has_assessment": False,
            "patient_name": p.name_enc if p else None,
            "current_risk_level": p.risk_level if p else None,
            "message": "尚未进行风险评估",
        }

    # 获取评估医生姓名
    assessor_name = None
    if ra.assessed_by:
        u_result = await db.execute(
            select(SysUser).where(SysUser.user_id == ra.assessed_by)
        )
        u = u_result.scalar_one_or_none()
        if u:
            assessor_name = u.real_name

    return {
        "patient_id": patient_id,
        "patient_name": p.name_enc if p else None,
        "has_assessment": True,
        "assessment_id": ra.assessment_id,
        "risk_score": ra.risk_score,
        "risk_level": ra.risk_level,
        "risk_factors": ra.risk_factors,
        "manage_level": ra.manage_level,
        "recommended_org": ra.recommended_org,
        "assigned_org": ra.assigned_org,
        "assigned_doctor": ra.assigned_doctor,
        "bp_assessment": ra.bp_assessment,
        "bg_assessment": ra.bg_assessment,
        "lipid_assessment": ra.lipid_assessment,
        "kidney_assessment": ra.kidney_assessment,
        "compliance_assessment": ra.compliance_assessment,
        "followup_frequency": ra.followup_frequency,
        "need_up_referral": ra.need_up_referral,
        "referral_note": ra.referral_note,
        "assessment_note": ra.assessment_note,
        "assessor_name": assessor_name,
        "assessed_at": str(ra.assessed_at) if ra.assessed_at else None,
        "valid_until": str(ra.valid_until) if ra.valid_until else None,
        "next_assessment_date": str(ra.next_assessment_date) if ra.next_assessment_date else None,
    }


@router.post("")
async def create_risk_assessment(
    data: RiskAssessmentCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建/更新患者风险评估与分级标记"""
    # 检查患者存在
    p_result = await db.execute(
        select(Patient).where(Patient.patient_id == data.patient_id)
    )
    p = p_result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="患者不存在")

    ra = PatientRiskAssessment(**data.model_dump())
    db.add(ra)

    # 同步更新患者的 risk_level
    if data.risk_level:
        p.risk_level = data.risk_level

    await db.commit()
    await db.refresh(ra)

    return {
        "assessment_id": ra.assessment_id,
        "patient_id": data.patient_id,
        "risk_level": data.risk_level,
        "manage_level": data.manage_level,
        "message": "风险评估完成，已标记分级诊疗方案",
    }


@router.post("/batch")
async def batch_assess(
    data: BatchAssessRequest,
    db: AsyncSession = Depends(get_db),
):
    """批量风险评估与自动分层"""
    results = []
    for pid in data.patient_ids:
        p_result = await db.execute(
            select(Patient).where(Patient.patient_id == pid)
        )
        p = p_result.scalar_one_or_none()
        if not p:
            results.append({"patient_id": pid, "status": "NOT_FOUND"})
            continue

        if data.auto_stratify:
            # 自动分层逻辑: 基于风险等级
            risk_map = {"LOW": "VILLAGE", "MEDIUM": "TOWNSHIP", "HIGH": "COUNTY", "CRITICAL": "REFERRAL"}
            manage_level = risk_map.get(p.risk_level or "MEDIUM", "TOWNSHIP")

            # 简单的自动风险评分 (基于已有疾病数量)
            diseases = p.disease_list or []
            base_score = len(diseases) * 15
            risk_level = "LOW" if base_score <= 15 else "MEDIUM" if base_score <= 30 else "HIGH" if base_score <= 50 else "CRITICAL"

            ra = PatientRiskAssessment(
                patient_id=pid, risk_score=base_score, risk_level=risk_level,
                manage_level=manage_level, risk_factors=diseases,
                assessed_at=datetime.utcnow(),
                valid_until=date.today() + timedelta(days=90),
                next_assessment_date=date.today() + timedelta(days=90),
            )
            db.add(ra)
            p.risk_level = risk_level
            results.append({
                "patient_id": pid, "status": "ASSESSED",
                "risk_score": base_score, "risk_level": risk_level,
                "manage_level": manage_level,
            })
        else:
            results.append({"patient_id": pid, "status": "SKIPPED", "reason": "auto_stratify=False"})

    await db.commit()
    return {"processed": len(data.patient_ids), "results": results}


@router.get("/list")
async def list_assessments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    risk_level: Optional[str] = None,
    manage_level: Optional[str] = None,
    assigned_org: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """风险评估列表 — 按风险等级/管理分层/机构筛选"""
    conditions = []
    if risk_level:
        conditions.append(PatientRiskAssessment.risk_level == risk_level)
    if manage_level:
        conditions.append(PatientRiskAssessment.manage_level == manage_level)
    if assigned_org:
        conditions.append(PatientRiskAssessment.assigned_org == assigned_org)

    subq = select(
        PatientRiskAssessment.patient_id,
        func.max(PatientRiskAssessment.assessed_at).label("max_at")
    ).group_by(PatientRiskAssessment.patient_id).subquery()

    base = select(PatientRiskAssessment).join(
        subq, and_(
            PatientRiskAssessment.patient_id == subq.c.patient_id,
            PatientRiskAssessment.assessed_at == subq.c.max_at,
        )
    )
    if conditions:
        base = base.where(and_(*conditions))
    base = base.order_by(desc(PatientRiskAssessment.risk_score))

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    rows = (await db.execute(
        base.offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

    items = []
    for ra in rows:
        p_result = await db.execute(select(Patient).where(Patient.patient_id == ra.patient_id))
        p = p_result.scalar_one_or_none()
        items.append({
            "assessment_id": ra.assessment_id, "patient_id": ra.patient_id,
            "patient_name": p.name_enc if p else None,
            "risk_score": ra.risk_score, "risk_level": ra.risk_level,
            "manage_level": ra.manage_level,
            "assigned_org": ra.assigned_org,
            "bp_assessment": ra.bp_assessment,
            "bg_assessment": ra.bg_assessment,
            "compliance_assessment": ra.compliance_assessment,
            "followup_frequency": ra.followup_frequency,
            "need_up_referral": ra.need_up_referral,
            "assessed_at": str(ra.assessed_at) if ra.assessed_at else None,
            "valid_until": str(ra.valid_until) if ra.valid_until else None,
        })

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/dashboard")
async def get_risk_dashboard(
    org_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """风险分层驾驶舱 — 全量纳管可视化"""
    q = select(Patient)
    if org_code:
        q = q.where(Patient.manage_org_code == org_code)

    patients = (await db.execute(q)).scalars().all()

    risk_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0, "UNASSESSED": 0}
    total = len(patients)
    for p in patients:
        level = p.risk_level if p.risk_level else "UNASSESSED"
        risk_dist[level] = risk_dist.get(level, 0) + 1

    unassessed_rate = round(risk_dist["UNASSESSED"] / max(total, 1) * 100, 1)

    return {
        "total_patients": total,
        "org_code": org_code,
        "risk_distribution": risk_dist,
        "unassessed_rate": unassessed_rate,
        "high_risk_count": risk_dist.get("HIGH", 0) + risk_dist.get("CRITICAL", 0),
        "high_risk_rate": round(
            (risk_dist.get("HIGH", 0) + risk_dist.get("CRITICAL", 0)) / max(total, 1) * 100, 1
        ),
        "status": "WARNING" if unassessed_rate > 20 else "OK",
        "message": f"尚有{risk_dist['UNASSESSED']}名患者未评估风险" if risk_dist["UNASSESSED"] > 0 else "所有患者已分层",
    }