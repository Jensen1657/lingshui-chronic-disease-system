"""质控校验 API"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.auth import get_current_active_user
from app.services.quality_control import QualityControlService
from app.db.session import get_db
from app.models import (
    Patient, FollowupRecord, FollowupReminder, PatientMedication
)

router = APIRouter(tags=["质控校验"])  # prefix 由 main.py 添加


# === 请求模型 ===

class RequiredFieldsCheckRequest(BaseModel):
    module: str = Field(..., description="patient_profile | hypertension_followup | diabetes_followup | referral | annual_assessment")
    data: dict = {}


class LogicCheckRequest(BaseModel):
    category: str = Field(..., description="vital_signs | glucose | bmi")
    data: dict = {}


class DrugInteractionCheckRequest(BaseModel):
    drugs: List[str] = []
    conditions: Optional[List[str]] = None


class ReferralValidationRequest(BaseModel):
    referral_type: str = Field(..., description="UP | DOWN")
    disease_type: str = Field(..., description="hypertension | diabetes | stroke | general")
    patient_data: dict = {}


class AlertEvaluationRequest(BaseModel):
    data: dict = {}


class FullQcCheckRequest(BaseModel):
    module: str
    data: dict
    extra_checks: Optional[dict] = None


# === API 端点 ===

@router.post("/required-fields")
async def check_required_fields(
    req: RequiredFieldsCheckRequest,
    _=Depends(get_current_active_user),
):
    """必填项校验"""
    return QualityControlService.check_required_fields(req.module, req.data)


@router.post("/logic")
async def check_logic(req: LogicCheckRequest, _=Depends(get_current_active_user)):
    """逻辑校验（数值范围、医学逻辑）"""
    return QualityControlService.validate_logic(req.category, req.data)


@router.post("/drug-interactions")
async def check_drug_interactions(
    req: DrugInteractionCheckRequest,
    _=Depends(get_current_active_user),
):
    """药物相互作用检查"""
    return QualityControlService.check_drug_interactions(req.drugs, req.conditions)


@router.post("/referral-validate")
async def validate_referral(
    req: ReferralValidationRequest,
    _=Depends(get_current_active_user),
):
    """转诊标准校验（上转/下转条件匹配）"""
    return QualityControlService.validate_referral(
        req.referral_type, req.disease_type, req.patient_data
    )


@router.post("/alerts")
async def evaluate_alerts(
    req: AlertEvaluationRequest,
    _=Depends(get_current_active_user),
):
    """预警规则引擎评估"""
    return QualityControlService.evaluate_alert_rules(req.data)


@router.post("/full-check")
async def full_qc_check(
    req: FullQcCheckRequest,
    _=Depends(get_current_active_user),
):
    """综合质控检查（必填+逻辑+预警一次性执行）"""
    return QualityControlService.full_quality_check(
        req.module, req.data, req.extra_checks
    )


@router.get("/rules/required-fields/{module}")
async def get_required_fields_rules(
    module: str,
    _=Depends(get_current_active_user),
):
    """获取某模块的必填字段定义"""
    fields = QualityControlService.REQUIRED_FIELDS.get(module, {})
    if not fields:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"未知模块: {module}")
    return {"module": module, "requiredFields": fields}


@router.get("/rules/alert-rules")
async def get_alert_rules(_=Depends(get_current_active_user)):
    """获取所有预警规则定义"""
    return [
        {
            "code": r["alertCode"],
            "name": r["alertName"],
            "category": r["category"],
            "severity": r["severity"],
        }
        for r in QualityControlService.ALERT_RULES
    ]


@router.get("/rules")
async def get_all_rules(_=Depends(get_current_active_user)):
    """获取所有质控规则（必填字段+预警规则+转诊标准）"""
    return {
        "requiredFields": QualityControlService.REQUIRED_FIELDS,
        "alertRules": [
            {
                "code": r["alertCode"],
                "name": r["alertName"],
                "category": r["category"],
                "severity": r["severity"],
            }
            for r in QualityControlService.ALERT_RULES
        ],
        "referralCriteria": QualityControlService.REFERRAL_CRITERIA,
    }


@router.get("/rules/referral-criteria")
async def get_referral_criteria(
    referral_type: Optional[str] = None,
    disease_type: Optional[str] = None,
    _=Depends(get_current_active_user),
):
    """获取转诊标准"""
    criteria = QualityControlService.REFERRAL_CRITERIA
    if referral_type:
        criteria = {referral_type: criteria.get(referral_type, {})}
    if disease_type:
        result = {}
        for rt, rc in criteria.items():
            if disease_type in rc:
                result[rt] = {disease_type: rc[disease_type]}
        criteria = result
    return criteria


# ===== 会议纪要：质控指标体系 =====
@router.get("/metrics/followup-rate")
async def get_followup_rate_metrics(
    org_code: Optional[str] = None,
    period_type: Optional[str] = "month",
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_active_user),
):
    """随访率考核指标"""
    q = select(func.count(FollowupRecord.followup_id))
    planned_q = select(func.count(FollowupReminder.reminder_id))
    if org_code:
        q = q.where(FollowupRecord.org_code == org_code)
        planned_q = planned_q.where(FollowupReminder.patient_id.in_(
            select(Patient.patient_id).where(Patient.manage_org_code == org_code)
        ))
    done = (await db.execute(q)).scalar() or 0
    planned = (await db.execute(planned_q)).scalar() or 0
    return {
        "metric": "followup_rate", "org_code": org_code,
        "followup_done": done, "followup_planned": planned,
        "rate": round(done / max(planned, 1) * 100, 1),
    }


@router.get("/metrics/medication-compliance")
async def get_medication_compliance_metrics(
    org_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_active_user),
):
    """用药依从率考核指标"""
    q = select(func.count(PatientMedication.medication_id))
    if org_code:
        q = q.where(PatientMedication.prescribed_org == org_code)
    total = (await db.execute(q)).scalar() or 0
    good_q = select(func.count(PatientMedication.medication_id)).where(
        PatientMedication.adherence_status == "GOOD"
    )
    if org_code:
        good_q = good_q.where(PatientMedication.prescribed_org == org_code)
    good = (await db.execute(good_q)).scalar() or 0
    return {
        "metric": "medication_compliance", "org_code": org_code,
        "total_prescriptions": total, "good_adherence": good,
        "compliance_rate": round(good / max(total, 1) * 100, 1),
    }


@router.get("/metrics/followup-quality")
async def get_followup_quality_metrics(
    org_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_active_user),
):
    """随访质量率考核指标 - 6个月内规范随访比例"""
    # 统计有随访的患者数
    q_total = select(func.count(func.distinct(FollowupRecord.patient_id)))
    if org_code:
        q_total = q_total.where(FollowupRecord.org_code == org_code)
    patients_with_fu = (await db.execute(q_total)).scalar() or 0

    # 统计近6个月有随访 + 12个月内有年度评估的患者 = 规范随访
    try:
        q_quality = text("""
            SELECT COUNT(DISTINCT fr.patient_id)
            FROM followup_record fr
            WHERE fr.followup_date >= date('now', '-6 months')
            AND fr.patient_id IN (
                SELECT patient_id FROM annual_assessment
                WHERE assessed_at >= date('now', '-12 months')
            )
        """)
        if org_code:
            q_quality = text("""
                SELECT COUNT(DISTINCT fr.patient_id)
                FROM followup_record fr
                WHERE fr.followup_date >= date('now', '-6 months')
                AND fr.org_code = :org_code
                AND fr.patient_id IN (
                    SELECT patient_id FROM annual_assessment
                    WHERE assessed_at >= date('now', '-12 months')
                )
            """)
            quality_count = (await db.execute(q_quality, {"org_code": org_code})).scalar() or 0
        else:
            quality_count = (await db.execute(q_quality)).scalar() or 0
    except Exception:
        quality_count = patients_with_fu  # 降级: 有随访即算

    return {
        "metric": "followup_quality", "org_code": org_code,
        "patients_with_followup": patients_with_fu,
        "quality_followup_patients": quality_count,
        "quality_rate": round(quality_count / max(patients_with_fu, 1) * 100, 1),
    }
