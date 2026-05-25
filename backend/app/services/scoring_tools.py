"""
临床评分工具集 - 6类慢病风险评估与分级
对应评估报告要求：
- 高血压：心血管风险分层 (WHO/ISH)
- 糖尿病：风险评分 + 糖化/HbA1c双标准
- 冠心病：TIMI / GRACE 评分
- 脑卒中：FAST 评分 + NIHSS
- 慢阻肺：mMRC / CAT + GOLD 分级
- 慢性肾脏病：eGFR (CKD-EPI) 分期
"""

from typing import Dict, Any, Optional, Tuple
from datetime import date
from math import exp, log


# ============================================================
# 一、高血压 - 心血管风险分层 (WHO/ISH 2018)
# ============================================================

def hypertension_risk_stratification(
    sbp: int, dbp: int,
    age: int,
    has_diabetes: bool = False,
    has_chd: bool = False,
    has_stroke: bool = False,
    has_ckd: bool = False,
    smoking: bool = False,
    dyslipidemia: bool = False,
    target_organ_damage: bool = False,
) -> Dict[str, Any]:
    """
    高血压心血管风险分层

    参数:
        sbp: 收缩压 (mmHg)
        dbp: 舒张压 (mmHg)
        age: 年龄
        has_diabetes: 合并糖尿病
        has_chd: 合并冠心病
        has_stroke: 合并脑卒中
        has_ckd: 合并CKD
        smoking: 吸烟
        dyslipidemia: 血脂异常
        target_organ_damage: 靶器官损害

    返回:
        risk_level: LOW / MODERATE / HIGH / VERY_HIGH
        risk_score: 0-100 综合评分
        recommendations: 管理建议
    """
    # 血压分级
    if sbp < 140 and dbp < 90:
        bp_level = "normal"
    elif sbp < 160 and dbp < 100:
        bp_level = "grade1"
    elif sbp < 180 and dbp < 110:
        bp_level = "grade2"
    else:
        bp_level = "grade3"

    # 危险因素计数
    risk_factors = sum([smoking, dyslipidemia, age >= 55 if True else age >= 65,
                        has_diabetes, has_ckd])
    clinical_conditions = sum([has_chd, has_stroke, target_organ_damage])

    # WHO/ISH 风险分层矩阵
    if clinical_conditions > 0 or bp_level == "grade3" or (has_diabetes and bp_level in ["grade2", "grade3"]):
        risk_level = "VERY_HIGH"
        risk_score = 85 + min(clinical_conditions * 5, 15)
    elif bp_level == "grade3" or (bp_level == "grade2" and risk_factors >= 3):
        risk_level = "HIGH"
        risk_score = 70 + risk_factors * 3
    elif bp_level == "grade2" and risk_factors >= 1:
        risk_level = "MODERATE"
        risk_score = 50 + risk_factors * 5
    elif bp_level == "grade1" and risk_factors >= 3:
        risk_level = "MODERATE"
        risk_score = 45 + risk_factors * 4
    else:
        risk_level = "LOW"
        risk_score = 20 + risk_factors * 5

    # 目标血压
    targets = {
        "VERY_HIGH": {"sbp": 130, "dbp": 80},
        "HIGH": {"sbp": 130, "dbp": 80},
        "MODERATE": {"sbp": 140, "dbp": 90},
        "LOW": {"sbp": 140, "dbp": 90},
    }

    level_names = {
        "VERY_HIGH": "很高危",
        "HIGH": "高危",
        "MODERATE": "中危",
        "LOW": "低危",
    }

    return {
        "riskLevel": risk_level,
        "riskLevelName": level_names.get(risk_level, "未知"),
        "riskScore": min(risk_score, 100),
        "bpLevel": bp_level,
        "bpCategory": _bp_category_name(bp_level),
        "targetSbp": targets[risk_level]["sbp"],
        "targetDbp": targets[risk_level]["dbp"],
        "riskFactorCount": risk_factors,
        "clinicalConditionCount": clinical_conditions,
        "recommendations": _htn_recommendations(risk_level),
    }


def _bp_category_name(level: str) -> str:
    names = {
        "normal": "正常血压",
        "grade1": "1级高血压(轻度)",
        "grade2": "2级高血压(中度)",
        "grade3": "3级高血压(重度)",
    }
    return names.get(level, "未知")


def _htn_recommendations(level: str) -> list:
    recs = {
        "VERY_HIGH": [
            "立即启动药物治疗（ACEI/ARB + CCB）",
            "2周内复查，必要时转诊至县级医院",
            "严格生活方式干预（低盐<5g/d、戒烟限酒）",
            "每月随访，监测心肾功能",
            "合并症联合管理（内分泌/心内科协同）",
        ],
        "HIGH": [
            "启动药物治疗（ACEI/ARB 或 CCB）",
            "1个月内复查血压",
            "生活方式干预 + 药物治疗并行",
            "每2周随访一次，稳定后每月一次",
        ],
        "MODERATE": [
            "考虑药物治疗（评估靶器官损害后决定）",
            "积极生活方式干预1-3个月",
            "每月测量血压，每3个月随访",
            "如未达标则启动药物",
        ],
        "LOW": [
            "以生活方式干预为主",
            "低盐饮食、规律运动、控制体重",
            "每3个月测量血压",
            "定期筛查危险因素",
        ],
    }
    return recs.get(level, [])


# ============================================================
# 二、糖尿病 - 综合风险评估
# ============================================================

def diabetes_risk_assessment(
    fasting_glucose: Optional[float] = None,
    hba1c: Optional[float] = None,
    postprandial_glucose: Optional[float] = None,
    age: int = 0,
    bmi: Optional[float] = None,
    disease_duration_years: float = 0,
    has_hypertension: bool = False,
    has_dyslipidemia: bool = False,
    has_retinopathy: bool = False,
    has_nephropathy: bool = False,
    has_neuropathy: bool = False,
    has_chd: bool = False,
    smoking: bool = False,
) -> Dict[str, Any]:
    """
    糖尿病综合风险评估

    标准：ADA 2024 + 中国2型糖尿病防治指南(2024版)
    """
    score = 0
    warnings = []
    recommendations = []

    # --- 血糖评估 ---
    glucose_status = "unknown"
    if hba1c is not None:
        if hba1c < 6.5:
            glucose_status = "good"
            score += 10
        elif hba1c < 7.0:
            glucose_status = "target"
            score += 20
        elif hba1c < 8.0:
            glucose_status = "elevated"
            score += 10
            warnings.append(f"HbA1c {hba1c}% 偏高，目标<7%")
        else:
            glucose_status = "poor"
            warnings.append(f"HbA1c {hba1c}% 严重偏高，需调整方案")
            score -= 10

    if fasting_glucose is not None:
        if fasting_glucose < 3.9:
            warnings.append(f"空腹血糖 {fasting_glucose} mmol/L，存在低血糖风险！")
            score -= 20
        elif fasting_glucose > 11.0:
            warnings.append(f"空腹血糖 {fasting_glucose} mmol/L 严重超标")
            score -= 10

    if postprandial_glucose is not None:
        if postprandial_glucose > 16.7:
            warnings.append(f"餐后血糖 {postprandial_glucose} mmol/L 严重超标！")
            score -= 15

    # --- 并发症加分 ---
    complications = sum([has_retinopathy, has_nephropathy, has_neuropathy, has_chd])
    score -= complications * 15

    # --- 危险因素 ---
    risk_factors = sum([has_hypertension, has_dyslipidemia, smoking,
                        (bmi or 0) >= 28, disease_duration_years > 10])

    # --- 分级 ---
    if score >= 50:
        risk_level = "LOW"
        level_name = "低风险"
    elif score >= 30:
        risk_level = "MODERATE"
        level_name = "中风险"
    elif score >= 10:
        risk_level = "HIGH"
        level_name = "高风险"
    else:
        risk_level = "VERY_HIGH"
        level_name = "极高风险"

    # --- 用药建议（GLP-1RA/SGLT2i 优先规则）---
    medication_advice = []
    if has_chd or has_nephropathy or has_hypertension:
        medication_advice.append("优先考虑 SGLT2i（心肾保护证据）")
    if bmi and bmi >= 27:
        medication_advice.append("优先考虑 GLP-1RA（减重获益）")
    if hba1c is not None and hba1c >= 9.0 and len(medication_advice) == 0:
        medication_advice.append("HbA1c≥9%，建议起始联合治疗或胰岛素")

    if not medication_advice:
        medication_advice.append("二甲双胍为一线用药，根据个体化调整")

    recommendations = [
        f"当前血糖状态：{glucose_status}",
        f"并发症数量：{complications}项",
        f"危险因素数：{risk_factors}个",
    ] + medication_advice + warnings

    return {
        "riskLevel": risk_level,
        "riskLevelName": level_name,
        "riskScore": max(0, min(100, score + 50)),  # 归一化到0-100
        "glucoseStatus": glucose_status,
        "hba1cTargetMet": (hba1c or 0) < 7.0,
        "fastingGlucoseNormal": (3.9 <= (fasting_glucose or 99) <= 7.0),
        "complicationCount": complications,
        "warnings": warnings,
        "medicationAdvice": medication_advice,
        "recommendations": recommendations,
    }


# ============================================================
# 三、冠心病 - TIMI / GRACE 评分
# ============================================================

def timi_score_for_acs(
    age: int,
    risk_factors_count: int = 0,  # ≥3个CAD危险因素
    has_prior_aspirin: bool = False,
    recent_severe_angina: bool = False,
    elevated_cardiac_markers: bool = False,
    st_deviation: bool = False,
    anginal_events_24h_ge_2: bool = False,
) -> Dict[str, Any]:
    """TIMI 不稳定型心绞痛/非ST段抬高心肌梗死风险评分"""
    score = sum([
        age >= 65,
        risk_factors_count >= 3,
        has_prior_aspirin,
        recent_severe_angina,
        elevated_cardiac_markers,
        st_deviation,
        anginal_events_24h_ge_2,
    ])

    # 重新计算
    criteria = [
        age >= 65,
        risk_factors_count >= 3,
        has_prior_aspirin,
        recent_severe_angina,
        elevated_cardiac_markers,
        st_deviation,
        anginal_events_24h_ge_2,
    ]
    score = sum(int(c) for c in criteria)

    risk_map = {
        (0, 1): ("低危", "14天内死亡/心梗风险 4.7%", "门诊管理"),
        (2, 3): ("中危", "14天内死亡/心梗风险 8.3-13.2%", "住院观察"),
        (4, 7): ("高危", "14天内死亡/心梗风险 19.9-41.4%", "早期侵入性治疗"),
    }

    for (lo, hi), (level, risk_text, mgmt) in risk_map.items():
        if lo <= score <= hi:
            return {
                "scoreName": "TIMI ACS Risk Score",
                "score": score,
                "maxScore": 7,
                "riskLevel": level,
                "riskDescription": risk_text,
                "management": mgmt,
                "criteriaMet": [c for c, met in zip(
                    ["年龄≥65", "≥3个CAD危险因素", "近期阿司匹林使用",
                     "近24h内严重心绞痛", "心脏标志物升高", "ST段偏移",
                     "近24h内≥2次心绞痛发作"],
                    criteria
                ) if met],
            }

    return {"score": score, "maxScore": 7, "riskLevel": "未知"}


def grace_score_v2(
    age: int,
    heart_rate: int,
    sbp: int,
    creatinine: float,
    cardiac_arrest_at_entry: bool = False,
    st_deviation: bool = False,
    elevated_enzymes: bool = False,
) -> Dict[str, Any]:
    """GRACE 2.0 院内死亡风险评分（简化版）"""
    score = 0
    score += (age - 50) * 2.5 if age > 50 else 0
    score += (heart_rate - 60) * 0.5 if heart_rate > 60 else 0
    score += max(0, (120 - sbp) * 1.5)
    score += (creatinine - 1.0) * 20 if creatinine > 1.0 else 0
    if cardiac_arrest_at_entry:
        score += 35
    if st_deviation:
        score += 25
    if elevated_enzymes:
        score = score + 15

    score = int(min(max(score, 0), 300))

    if score <= 109:
        risk = "低危 (<1%)"
    elif score <= 140:
        risk = "中危 (1-3%)"
    elif score <= 180:
        risk = "高危 (3-8%)"
    else:
        risk = "极高危 (>8%)"

    return {
        "scoreName": "GRACE 2.0 In-Hospital Death Risk",
        "score": score,
        "maxScore": 300,
        "riskLevel": risk,
        "recommendation": "低危可保守治疗；中高危需早期冠脉造影" if score <= 140 else "紧急介入治疗",
    }


# ============================================================
# 四、脑卒中 - FAST + NIHSS 简化评估
# ============================================================

def fast_assessment(
    face_droop: bool,           # F - 面部下垂
    arm_weakness: bool,         # A - 手臂无力
    speech_difficulty: bool,    # S - 言语困难
    time_onset_known: bool,     # T - 发作时间明确
    symptom_duration_minutes: int = 0,
) -> Dict[str, Any]:
    """FAST 卒中快速筛查"""
    positive_count = sum([face_droop, arm_weakness, speech_difficulty])

    if positive_count >= 1:
        likely_stroke = True
        urgency = "⚠️ 疑似卒中，立即呼叫急救！"
        if symptom_duration_minutes <= 180 and time_onset_known:
            urgency += " 在溶栓时间窗内（4.5小时），需紧急送医。"
        elif symptom_duration_minutes <= 360:
            urgency += " 可能仍在取栓时间窗内（6小时）。"
        else:
            urgency += " 超过溶栓/取栓时间窗，但仍需紧急评估。"
    else:
        likely_stroke = False
        urgency = "FAST阴性，但不能完全排除卒中，需进一步检查。"

    return {
        "scoreName": "FAST Stroke Screening",
        "positiveCount": positive_count,
        "totalCriteria": 3,
        "likelyStroke": likely_stroke,
        "urgency": urgency,
        "timeWindow": _stroke_time_window(symptom_duration_minutes, time_onset_known),
        "criteria": {
            "Face": ("阳性", "面部不对称/下垂") if face_droop else ("阴性", "正常"),
            "Arm": ("阳性", "单侧肢体无力") if arm_weakness else ("阴性", "正常"),
            "Speech": ("阳性", "言语含糊/困难") if speech_difficulty else ("阴性", "正常"),
            "Time": ("已知", f"发病{symptom_duration_minutes}分钟") if time_onset_known else ("未知", "无法确定"),
        },
    }


def _stroke_time_window(duration_min: int, known: bool) -> str:
    if not known:
        return "发病时间未知，无法判断时间窗"
    if duration_min <= 180:
        return "✅ 溶栓时间窗内（≤4.5小时）"
    elif duration_min <= 360:
        return "⚠️ 取栓时间窗内（≤6小时）"
    elif duration_min <= 720:
        return "可能超出标准时间窗，需影像学评估"
    else:
        return "❌ 超过常规时间窗"


def calculate_nihss_simplified(
    level_of_consciousness: int = 0,   # 0-3
    gaze: int = 0,                      # 0-2
    visual_field: int = 0,              # 0-3
    facial_palsy: int = 0,              # 0-3
    motor_arm_l: int = 0,               # 0-4
    motor_arm_r: int = 0,               # 0-4
    motor_leg_l: int = 0,               # 0-4
    motor_leg_r: int = 0,               # 0-4
    limb_ataxia: int = 0,               # 0-2
    sensory: int = 0,                   # 0-2
    language: int = 0,                  # 0-3
    dysarthria: int = 0,                # 0-2
    extinction: int = 0,                # 0-2
) -> Dict[str, Any]:
    """NIHSS 卒中严重程度量表（简化版）"""
    items = {
        "意识水平": level_of_consciousness,
        "眼球运动": gaze,
        "视野": visual_field,
        "面瘫": facial_palsy,
        "左上肢运动": motor_arm_l,
        "右上肢运动": motor_arm_r,
        "左下肢运动": motor_leg_l,
        "右下肢运动": motor_leg_r,
        "共济失调": limb_ataxia,
        "感觉": sensory,
        "语言": language,
        "构音障碍": dysarthria,
        "忽视": extinction,
    }
    total = sum(items.values())

    if total == 0:
        severity = "正常"
    elif total <= 4:
        severity = "轻度卒中"
    elif total <= 15:
        severity = "中度卒中"
    elif total <= 20:
        severity = "中重度卒中"
    else:
        severity = "重度卒中"

    return {
        "scoreName": "NIHSS Stroke Scale",
        "totalScore": total,
        "maxScore": 42,
        "severity": severity,
        "items": items,
    }


# ============================================================
# 五、慢阻肺 - mMRC / CAT + GOLD 分级
# ============================================================

def mmrc_dyspnea_scale(mmrc_grade: int) -> Dict[str, Any]:
    """mMRC 呼吸困难分级（0-4级）"""
    descriptions = {
        0: "我仅在费力活动时出现呼吸困难",
        1: "我比同龄人易出现呼吸困难，或在平地快走时出现",
        2: "我因呼吸困难而比同龄人走得慢，或因呼吸困难在平地行走时需停下休息",
        3: "我在平地行走100米左右或数分钟后需停下喘气",
        4: "我因呼吸困难严重而不能离开房屋，或在穿衣/脱衣时出现呼吸困难",
    }
    grade = max(0, min(4, mmrc_grade))

    impact_map = {
        0: ("无影响", "无需特殊干预"),
        1: ("轻微", "避免诱发因素，每年接种流感疫苗"),
        2: ("中度", "开始支气管扩张剂治疗"),
        3: ("明显", "三联吸入治疗+肺康复"),
        4: ("严重", "长期氧疗评估+多学科管理"),
    }

    impact, advice = impact_map[grade]

    return {
        "scoreName": "mMRC Dyspnea Scale",
        "grade": grade,
        "description": descriptions.get(grade, "未知"),
        "impact": impact,
        "treatmentAdvice": advice,
    }


def cat_assessment(
    cough_score: int = 0,       # 0-5
    sputum_score: int = 0,      # 0-5
    chest_tightness: int = 0,   # 0-5
    breathlessness: int = 0,    # 0-5
    activity_limitation: int = 0,  # 0-5
    confidence: int = 0,        # 0-5
    sleep_disturbance: int = 0, # 0-5
    energy: int = 0,            # 0-5
) -> Dict[str, Any]:
    """COPD Assessment Test (CAT) 量表"""
    items = {
        "咳嗽": cough_score,
        "咳痰": sputum_score,
        "胸闷": chest_tightness,
        "气促": breathlessness,
        "活动受限": activity_limitation,
        "信心": confidence,
        "睡眠影响": sleep_disturbance,
        "精力": energy,
    }
    total = sum(items.values())
    total = max(0, min(total, 40))

    if total <= 10:
        impact = "轻微影响"
        level = "Mild"
    elif total <= 20:
        impact = "中度影响"
        level = "Moderate"
    elif total <= 30:
        impact = "严重影响"
        level = "Severe"
    else:
        impact = "非常严重影响"
        level = "Very Severe"

    return {
        "scoreName": "CAT (COPD Assessment Test)",
        "totalScore": total,
        "maxScore": 40,
        "impactLevel": impact,
        "impactCode": level,
        "items": items,
    }


def gold_classification(
    fev1_percent: float,  # FEV1占预计值%
    exacerbations_per_year: int = 0,
    has_hospitalization: bool = False,
) -> Dict[str, Any]:
    """GOLD 分级（基于气流受限严重程度）"""
    if fev1_percent >= 80:
        gold_grade = 1
        grade_name = "GOLD I（轻度）"
    elif fev1_percent >= 50:
        gold_grade = 2
        grade_name = "GOLD II（中度）"
    elif fev1_percent >= 30:
        gold_grade = 3
        grade_name = "GOLD III（重度）"
    else:
        gold_grade = 4
        grade_name = "GOLD IV（极重度）"

    # GOLD 2024 ABCD分组
    if exacerbations_per_year == 0 or (exacerbations_per_year <= 1 and not has_hospitalization):
        abcd_group = "A组"
        abcd_desc = "低症状/低风险"
    elif exacerbations_per_year <= 1 and not has_hospitalization:
        abcd_group = "B组"
        abcd_desc = "高症状/低风险"
    elif exacerbations_per_year >= 2 or has_hospitalization:
        abcd_group = "E组"
        abcd_desc = "高急性加重风险"
    else:
        abcd_group = "C组"
        abcd_desc = "低症状/高风险"

    treatment_pathway = {
        "A组": "按需短效支气管扩张剂(SABA/SAMA)",
        "B组": "长效支气管扩张剂(LABA/LAMA)",
        "C组": "LAMA ± ICS（嗜酸粒细胞升高时）",
        "E组": "LABA+LAMA ± ICS（考虑三联吸入）",
    }.get(abcd_group, "LAMA基础治疗")

    return {
        "scoreName": "GOLD Classification",
        "goldGrade": gold_grade,
        "gradeName": grade_name,
        "fev1Percent": fev1_percent,
        "abcdGroup": abcd_group,
        "abcdDescription": abcd_desc,
        "exacerbationsPerYear": exacerbations_per_year,
        "hasHospitalization": has_hospitalization,
        "initialTreatment": treatment_pathway,
    }


# ============================================================
# 六、慢性肾脏病 - eGFR (CKD-EPI 2021)
# ============================================================

def calculate_egfr_ckd_epi(
    serum_creatinine: float,  # μmol/L
    age: int,
    gender: str = "male",      # male / female
    is_black: bool = False,    # 种族校正（中国人群一般不适用）
) -> Dict[str, Any]:
    """
    CKD-EPI 2021 公式计算 eGFR

    参数:
        serum_creatinine: 血清肌酐 (μmol/L)，需转换为 mg/dL (÷88.4)
        age: 年龄
        gender: 性别
        is_black: 是否黑人种族
    """
    # μmol/L → mg/dL
    scr_mgdl = serum_creatinine / 88.4

    if scr_mgdl <= 0:
        return {"error": "肌酐值无效"}

    # CKD-EPI 2021 公式（无种族系数）
    import math
    log_scr = math.log(scr_mgdl)

    if gender.lower() == "female":
        if scr_mgdl <= 0.7:
            eGFR = 142 * (scr_mgdl / 0.7) ** (-0.241) * (age / 39) ** (-1.027) * 1.012 ** (age - 39)
        else:
            eGFR = 142 * (scr_mgdl / 0.7) ** (-1.200) * (age / 39) ** (-1.027) * 1.012 ** (age - 39)
    else:
        if scr_mgdl <= 0.9:
            eGFR = 142 * (scr_mgdl / 0.9) ** (-0.302) * (age / 40) ** (-1.027) * 1.012 ** (age - 40) * 1.0
        else:
            eGFR = 142 * (scr_mgdl / 0.9) ** (-1.200) * (age / 40) ** (-1.027) * 1.012 ** (age - 40) * 1.0

    eGFR = round(eGFR, 1)

    # CKD 分期
    if eGFR >= 90:
        ckd_stage = 1
        stage_name = "G1（正常或增高）"
        description = "eGFR正常，有肾损伤标志"
    elif eGFR >= 60:
        ckd_stage = 2
        stage_name = "G2（轻度下降）"
        description = "轻度肾功能不全"
    elif eGFR >= 45:
        ckd_stage = "3a"
        stage_name = "G3a（轻中度下降）"
        description = "轻中度肾功能不全"
    elif eGFR >= 30:
        ckd_stage = "3b"
        stage_name = "G3b（中重度下降）"
        description = "中重度肾功能不全"
    elif eGFR >= 15:
        ckd_stage = 4
        stage_name = "G4（重度下降）"
        description = "重度肾功能不全（衰竭前期）"
    else:
        ckd_stage = 5
        stage_name = "G5（肾衰竭）"
        description = "终末期肾病，需透析/移植评估"

    # 随访频率
    followup_freq = {
        1: "每年随访1次",
        2: "每6个月随访1次",
        "3a": "每3-6个月随访1次",
        "3b": "每3个月随访1次",
        4: "每1-3个月随访1次",
        5: "立即转诊肾内科，评估透析/移植",
    }

    # 用药注意事项
    med_warnings = []
    if eGFR < 30:
        med_warnings.append("NSAIDs禁用或慎用")
        med_warnings.append("氨基糖苷类抗生素禁用")
        med_warnings.append("对比剂增强CT需充分水化")
    if eGFR < 50:
        metformin_warning = "二甲双胍需减量或停用（eGFR<30禁用）"
        med_warnings.append(metformin_warning)

    return {
        "scoreName": "eGFR (CKD-EPI 2021)",
        "eGFR": eGFR,
        "unit": "ml/min/1.73m²",
        "ckdStage": ckd_stage,
        "stageName": stage_name,
        "stageDescription": description,
        "serumCreatinine": serum_creatinine,
        "followupFrequency": followup_freq.get(ckd_stage, "定期随访"),
        "medicationWarnings": med_warnings,
        "referralNeeded": ckd_stage >= 4,
    }


# ============================================================
# 统一评分入口
# ============================================================

def unified_scoring(disease_type: str, params: dict) -> Dict[str, Any]:
    """
    统一评分入口

    Args:
        disease_type: hypertension | diabetes | coronary_heart_disease | stroke | copd | ckd
        params: 各疾病对应的参数字典

    Returns:
        评分结果字典
    """
    scorers = {
        "hypertension": hypertension_risk_stratification,
        "diabetes": diabetes_risk_assessment,
        "coronary_heart_disease": timi_score_for_acs,
        "stroke": fast_assessment,
        "copd": gold_classification,
        "ckd": calculate_egfr_ckd_epi,
    }

    scorer = scorers.get(disease_type)
    if not scorer:
        return {"error": f"不支持的疾病类型: {disease_type}"}

    try:
        result = scorer(**params)
        result["diseaseType"] = disease_type
        return result
    except Exception as e:
        return {"error": str(e), "diseaseType": disease_type}
