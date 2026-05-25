"""质控校验 API"""
from fastapi import APIRouter, Depends
from typing import List, Optional
from pydantic import BaseModel, Field
from app.dependencies.auth import get_current_active_user
from app.services.quality_control import QualityControlService

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
