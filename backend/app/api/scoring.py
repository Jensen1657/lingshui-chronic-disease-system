"""临床评分 API - 6类慢病风险评估工具"""
from fastapi import APIRouter, Depends
from typing import Optional
from pydantic import BaseModel, Field
from app.dependencies.auth import get_current_active_user
from app.services.scoring_tools import (
    hypertension_risk_stratification,
    diabetes_risk_assessment,
    timi_score_for_acs,
    grace_score_v2,
    fast_assessment,
    calculate_nihss_simplified,
    mmrc_dyspnea_scale,
    cat_assessment,
    gold_classification,
    calculate_egfr_ckd_epi,
    unified_scoring,
)

router = APIRouter(tags=["临床评分工具"])  # prefix 由 main.py 添加


# === 请求模型 ===

class HypertensionScoringRequest(BaseModel):
    sbp: int = Field(..., description="收缩压(mmHg)")
    dbp: int = Field(..., description="舒张压(mmHg)")
    age: int = Field(..., description="年龄")
    has_diabetes: bool = False
    has_chd: bool = False
    has_stroke: bool = False
    has_ckd: bool = False
    smoking: bool = False
    dyslipidemia: bool = False
    target_organ_damage: bool = False


class DiabetesScoringRequest(BaseModel):
    fasting_glucose: Optional[float] = None
    hba1c: Optional[float] = None
    postprandial_glucose: Optional[float] = None
    age: int = 0
    bmi: Optional[float] = None
    disease_duration_years: float = 0
    has_hypertension: bool = False
    has_dyslipidemia: bool = False
    has_retinopathy: bool = False
    has_nephropathy: bool = False
    has_neuropathy: bool = False
    has_chd: bool = False
    smoking: bool = False


class TimiRequest(BaseModel):
    age: int
    risk_factors_count: int = 0
    has_prior_aspirin: bool = False
    recent_severe_angina: bool = False
    elevated_cardiac_markers: bool = False
    st_deviation: bool = False
    anginal_events_24h_ge_2: bool = False


class GraceRequest(BaseModel):
    age: int
    heart_rate: int
    sbp: int
    creatinine: float
    cardiac_arrest_at_entry: bool = False
    st_deviation: bool = False
    elevated_enzymes: bool = False


class FastStrokeRequest(BaseModel):
    face_droop: bool
    arm_weakness: bool
    speech_difficulty: bool
    time_onset_known: bool
    symptom_duration_minutes: int = 0


class NihssRequest(BaseModel):
    level_of_consciousness: int = 0
    gaze: int = 0
    visual_field: int = 0
    facial_palsy: int = 0
    motor_arm_l: int = 0
    motor_arm_r: int = 0
    motor_leg_l: int = 0
    motor_leg_r: int = 0
    limb_ataxia: int = 0
    sensory: int = 0
    language: int = 0
    dysarthria: int = 0
    extinction: int = 0


class MmrcRequest(BaseModel):
    grade: int = Field(..., ge=0, le=4, description="mMRC分级(0-4)")


class CatRequest(BaseModel):
    cough_score: int = Field(0, ge=0, le=5)
    sputum_score: int = Field(0, ge=0, le=5)
    chest_tightness: int = Field(0, ge=0, le=5)
    breathlessness: int = Field(0, ge=0, le=5)
    activity_limitation: int = Field(0, ge=0, le=5)
    confidence: int = Field(0, ge=0, le=5)
    sleep_disturbance: int = Field(0, ge=0, le=5)
    energy: int = Field(0, ge=0, le=5)


class GoldRequest(BaseModel):
    fev1_percent: float = Field(..., description="FEV1占预计值%")
    exacerbations_per_year: int = 0
    has_hospitalization: bool = False


class EgfrRequest(BaseModel):
    serum_creatinine: float = Field(..., description="血清肌酐(μmol/L)")
    age: int
    gender: str = "male"
    is_black: bool = False


class UnifiedScoringRequest(BaseModel):
    disease_type: str = Field(..., description="hypertension|diabetes|coronary_heart_disease|stroke|copd|ckd")
    params: dict = {}


# === API 端点 ===

@router.post("/hypertension")
async def score_hypertension(
    req: HypertensionScoringRequest,
    _=Depends(get_current_active_user),
):
    """高血压心血管风险分层 (WHO/ISH)"""
    return hypertension_risk_stratification(
        sbp=req.sbp, dbp=req.dbp, age=req.age,
        has_diabetes=req.has_diabetes, has_chd=req.has_chd,
        has_stroke=req.has_stroke, has_ckd=req.has_ckd,
        smoking=req.smoking, dyslipidemia=req.dyslipidemia,
        target_organ_damage=req.target_organ_damage,
    )


@router.post("/diabetes")
async def score_diabetes(
    req: DiabetesScoringRequest,
    _=Depends(get_current_active_user),
):
    """糖尿病综合风险评估 (ADA 2024 + 中国指南2024)"""
    return diabetes_risk_assessment(
        fasting_glucose=req.fasting_glucose, hba1c=req.hba1c,
        postprandial_glucose=req.postprandial_glucose, age=req.age,
        bmi=req.bmi, disease_duration_years=req.disease_duration_years,
        has_hypertension=req.has_hypertension,
        has_dyslipidemia=req.has_dyslipidemia,
        has_retinopathy=req.has_retinopathy,
        has_nephropathy=req.has_nephropathy,
        has_neuropathy=req.has_neuropathy,
        has_chd=req.has_chd, smoking=req.smoking,
    )


@router.post("/coronary/timi")
async def score_timi(req: TimiRequest, _=Depends(get_current_active_user)):
    """TIMI ACS 风险评分"""
    return timi_score_for_acs(
        age=req.age, risk_factors_count=req.risk_factors_count,
        has_prior_aspirin=req.has_prior_aspirin,
        recent_severe_angina=req.recent_severe_angina,
        elevated_cardiac_markers=req.elevated_cardiac_markers,
        st_deviation=req.st_deviation,
        anginal_events_24h_ge_2=req.anginal_events_24h_ge_2,
    )


@router.post("/coronary/grace")
async def score_grace(req: GraceRequest, _=Depends(get_current_active_user)):
    """GRACE 2.0 院内死亡风险评分"""
    return grace_score_v2(
        age=req.age, heart_rate=req.heart_rate, sbp=req.sbp,
        creatinine=req.creatinine,
        cardiac_arrest_at_entry=req.cardiac_arrest_at_entry,
        st_deviation=req.st_deviation,
        elevated_enzymes=req.elevated_enzymes,
    )


@router.post("/stroke/fast")
async def stroke_fast(req: FastStrokeRequest, _=Depends(get_current_active_user)):
    """FAST 卒中快速筛查"""
    return fast_assessment(
        face_droop=req.face_droop, arm_weakness=req.arm_weakness,
        speech_difficulty=req.speech_difficulty,
        time_onset_known=req.time_onset_known,
        symptom_duration_minutes=req.symptom_duration_minutes,
    )


@router.post("/stroke/nihss")
async def stroke_nihss(req: NihssRequest, _=Depends(get_current_active_user)):
    """NIHSS 卒中严重程度量表"""
    return calculate_nihss_simplified(
        level_of_consciousness=req.level_of_consciousness,
        gaze=req.gaze, visual_field=req.visual_field,
        facial_palsy=req.facial_palsy,
        motor_arm_l=req.motor_arm_l, motor_arm_r=req.motor_arm_r,
        motor_leg_l=req.motor_leg_l, motor_leg_r=req.motor_leg_r,
        limb_ataxia=req.limb_ataxia, sensory=req.sensory,
        language=req.language, dysarthria=req.dysarthria,
        extinction=req.extinction,
    )


@router.post("/copd/mmrc")
async def copd_mmrc(req: MmrcRequest, _=Depends(get_current_active_user)):
    """mMRC 呼吸困难分级"""
    return mmrc_dyspnea_scale(req.grade)


@router.post("/copd/cat")
async def copd_cat(req: CatRequest, _=Depends(get_current_active_user)):
    """CAT (COPD Assessment Test) 量表"""
    return cat_assessment(
        cough_score=req.cough_score, sputum_score=req.sputum_score,
        chest_tightness=req.chest_tightness, breathlessness=req.breathlessness,
        activity_limitation=req.activity_limitation,
        confidence=req.confidence, sleep_disturbance=req.sleep_disturbance,
        energy=req.energy,
    )


@router.post("/copd/gold")
async def copd_gold(req: GoldRequest, _=Depends(get_current_active_user)):
    """GOLD 分级（慢阻肺气流受限严重程度）"""
    return gold_classification(
        fev1_percent=req.fev1_percent,
        exacerbations_per_year=req.exacerbations_per_year,
        has_hospitalization=req.has_hospitalization,
    )


@router.post("/ckd/egfr")
async def ckd_egfr(req: EgfrRequest, _=Depends(get_current_active_user)):
    """eGFR 计算 (CKD-EPI 2021) + CKD分期"""
    return calculate_egfr_ckd_epi(
        serum_creatinine=req.serum_creatinine, age=req.age,
        gender=req.gender, is_black=req.is_black,
    )


@router.post("/unified")
async def unified_score(req: UnifiedScoringRequest, _=Depends(get_current_active_user)):
    """统一评分入口（按疾病类型自动路由到对应评分工具）"""
    return unified_scoring(disease_type=req.disease_type, params=req.params)


@router.get("/tools")
async def list_scoring_tools(_=Depends(get_current_active_user)):
    """列出所有可用的评分工具"""
    return [
        {"disease": "高血压", "tool": "心血管风险分层(WHO/ISH)", "endpoint": "/api/scoring/hypertension",
         "params": ["sbp", "dbp", "age", "合并症"]},
        {"disease": "糖尿病", "tool": "综合风险评估(ADA+中国2024)", "endpoint": "/api/scoring/diabetes",
         "params": ["fasting_glucose", "hba1c", "并发症"]},
        {"disease": "冠心病", "tool": "TIMI ACS评分", "endpoint": "/api/scoring/coronary/timi",
         "params": ["age", "危险因素数", "心电图改变"]},
        {"disease": "冠心病", "tool": "GRACE 2.0评分", "endpoint": "/api/scoring/coronary/grace",
         "params": ["age", "心率", "血压", "肌酐"]},
        {"disease": "脑卒中", "tool": "FAST快速筛查", "endpoint": "/api/scoring/stroke/fast",
         "params": ["face_droop", "arm_weakness", "speech_difficulty"]},
        {"disease": "脑卒中", "tool": "NIHSS严重程度量表", "endpoint": "/api/scoring/stroke/nihss",
         "params": ["12项神经功能检查"]},
        {"disease": "慢阻肺", "tool": "mMRC呼吸困难分级", "endpoint": "/api/scoring/copd/mmrc",
         "params": ["grade(0-4)"]},
        {"disease": "慢阻肺", "tool": "CAT量表", "endpoint": "/api/scoring/copd/cat",
         "params": ["8项症状评分(0-5)"]},
        {"disease": "慢阻肺", "tool": "GOLD分级", "endpoint": "/api/scoring/copd/gold",
         "params": ["fev1_percent", "急性加重次数"]},
        {"disease": "慢性肾脏病", "tool": "eGFR(CKD-EPI 2021)", "endpoint": "/api/scoring/ckd/egfr",
         "params": ["serum_creatinine(μmol/L)", "age", "gender"]},
    ]
