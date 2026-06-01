"""
处方审核指导 API — 叶胜业：总院医生线上指导基层处方优化
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app.models.meeting_models import PrescriptionReview, PatientMedication
from app.dependencies.auth import get_current_active_user
from app.models import Patient, SysUser, FollowupRecord

router = APIRouter(tags=["处方审核"])


class ReviewCreate(BaseModel):
    medication_id: str
    patient_id: str
    review_type: str = "MANUAL"
    suggested_dosage: Optional[str] = None
    suggested_frequency: Optional[str] = None
    suggested_drug: Optional[str] = None
    review_reason: Optional[str] = None
    review_result: str  # APPROVED/ADJUSTED/REJECTED
    prescribed_by: Optional[str] = None
    notes: Optional[str] = None


class ReviewUpdate(BaseModel):
    is_applied: Optional[bool] = None  # 基层是否已采用
    notes: Optional[str] = None


class ReviewListResponse(BaseModel):
    items: list[dict]
    total: int
    page: int
    page_size: int


@router.get("")
async def list_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    patient_id: Optional[str] = None,
    review_result: Optional[str] = None,
    is_applied: Optional[bool] = None,
    prescribed_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """处方审核记录列表"""
    conditions = []
    if patient_id:
        conditions.append(PrescriptionReview.patient_id == patient_id)
    if review_result:
        conditions.append(PrescriptionReview.review_result == review_result)
    if is_applied is not None:
        conditions.append(PrescriptionReview.is_applied == is_applied)
    if prescribed_by:
        conditions.append(PrescriptionReview.prescribed_by == prescribed_by)

    base = select(PrescriptionReview)
    if conditions:
        base = base.where(and_(*conditions))
    base = base.order_by(desc(PrescriptionReview.reviewed_at))

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    rows = (await db.execute(
        base.offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

    items = []
    for r in rows:
        # Join names
        patient_name = None
        reviewer_name = None
        prescriber_name = None

        p_result = await db.execute(select(Patient).where(Patient.patient_id == r.patient_id))
        p = p_result.scalar_one_or_none()
        if p:
            patient_name = p.name_enc

        u_result = await db.execute(select(SysUser).where(SysUser.user_id == r.reviewed_by))
        u = u_result.scalar_one_or_none()
        if u:
            reviewer_name = u.real_name

        if r.prescribed_by:
            pres_result = await db.execute(select(SysUser).where(SysUser.user_id == r.prescribed_by))
            pres = pres_result.scalar_one_or_none()
            if pres:
                prescriber_name = pres.real_name

        items.append({
            "review_id": r.review_id, "medication_id": r.medication_id,
            "patient_id": r.patient_id, "patient_name": patient_name,
            "review_type": r.review_type,
            "original_dosage": r.original_dosage, "original_frequency": r.original_frequency,
            "original_drug": r.original_drug,
            "suggested_dosage": r.suggested_dosage,
            "suggested_frequency": r.suggested_frequency,
            "suggested_drug": r.suggested_drug,
            "review_reason": r.review_reason, "review_result": r.review_result,
            "reviewed_by": r.reviewed_by, "reviewer_name": reviewer_name,
            "reviewed_org": r.reviewed_org,
            "prescribed_by": r.prescribed_by, "prescriber_name": prescriber_name,
            "is_applied": r.is_applied,
            "applied_at": str(r.applied_at) if r.applied_at else None,
            "reviewed_at": str(r.reviewed_at) if r.reviewed_at else None,
            "notes": r.notes,
        })

    return ReviewListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("")
async def create_review(
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
):
    """总院医生审核基层处方"""
    # 获取原始用药记录
    med_result = await db.execute(
        select(PatientMedication).where(
            PatientMedication.medication_id == data.medication_id
        )
    )
    med = med_result.scalar_one_or_none()
    if not med:
        raise HTTPException(status_code=404, detail="用药记录不存在")

    # 获取审核者所属机构
    reviewed_org = None
    if data.prescribed_by:
        u_result = await db.execute(
            select(SysUser).where(SysUser.user_id == data.prescribed_by)
        )
        u = u_result.scalar_one_or_none()
        if u:
            reviewed_org = u.org_code

    review = PrescriptionReview(
        medication_id=data.medication_id,
        patient_id=data.patient_id,
        review_type=data.review_type,
        original_dosage=med.dosage,
        original_frequency=med.frequency,
        original_drug=med.drug_name,
        suggested_dosage=data.suggested_dosage or med.dosage,
        suggested_frequency=data.suggested_frequency or med.frequency,
        suggested_drug=data.suggested_drug or med.drug_name,
        review_reason=data.review_reason,
        review_result=data.review_result,
        prescribed_by=data.prescribed_by,
        reviewed_org=reviewed_org,
        notes=data.notes,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    return {
        "review_id": review.review_id,
        "review_result": review.review_result,
        "message": f"处方审核完成: {review.review_result}",
    }


@router.put("/{review_id}/apply")
async def apply_review(
    review_id: str,
    db: AsyncSession = Depends(get_db),
):
    """基层医生采用总院审核建议，同步更新用药记录"""
    result = await db.execute(
        select(PrescriptionReview).where(PrescriptionReview.review_id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="审核记录不存在")

    review.is_applied = True
    review.applied_at = datetime.utcnow()

    # 同步更新用药记录
    med_result = await db.execute(
        select(PatientMedication).where(
            PatientMedication.medication_id == review.medication_id
        )
    )
    med = med_result.scalar_one_or_none()
    if med:
        if review.suggested_dosage:
            med.dosage = review.suggested_dosage
            med.adjust_reason = f"总院审核建议: {review.review_reason or '优化方案'}"
        if review.suggested_frequency:
            med.frequency = review.suggested_frequency
        if review.suggested_drug:
            med.drug_name = review.suggested_drug

    await db.commit()

    return {
        "message": "已采用审核建议并更新处方",
        "review_id": review_id,
        "updated_dosage": review.suggested_dosage,
        "updated_drug": review.suggested_drug,
    }


@router.get("/stats")
async def get_prescription_review_stats(
    org_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """处方审核统计 — 驾驶舱指标"""
    q = select(PrescriptionReview)
    if org_code:
        q = q.where(PrescriptionReview.reviewed_org == org_code)

    rows = (await db.execute(q)).scalars().all()

    total = len(rows)
    approved = sum(1 for r in rows if r.review_result == "APPROVED")
    adjusted = sum(1 for r in rows if r.review_result == "ADJUSTED")
    rejected = sum(1 for r in rows if r.review_result == "REJECTED")
    applied = sum(1 for r in rows if r.is_applied)

    return {
        "total_reviews": total,
        "approved": approved,
        "adjusted": adjusted,
        "rejected": rejected,
        "applied_count": applied,
        "adoption_rate": round(applied / max(approved + adjusted, 1) * 100, 1),
        "org_code": org_code,
    }


# ==================== AI 处方推荐 ====================

AI_DRUG_DB = [
    {"disease": "HYPERTENSION", "classes": [
        {"class": "CCB", "class_cn": "CCB类", "examples": ["硝苯地平", "氨氯地平", "左旋氨氯地平"], "first_line": True},
        {"class": "ACEI", "class_cn": "ACEI类", "examples": ["依那普利", "贝那普利", "培哚普利"], "first_line": True},
        {"class": "ARB", "class_cn": "ARB类", "examples": ["缬沙坦", "厄贝沙坦", "坎地沙坦"], "first_line": True},
        {"class": "β-blocker", "class_cn": "β受体阻滞剂", "examples": ["美托洛尔", "比索洛尔"], "first_line": False},
        {"class": "Diuretics", "class_cn": "利尿剂", "examples": ["氢氯噻嗪", "吲达帕胺"], "first_line": False},
    ]},
    {"disease": "DIABETES", "classes": [
        {"class": "Metformin", "class_cn": "双胍类", "examples": ["二甲双胍"], "first_line": True},
        {"class": "Sulfonylurea", "class_cn": "磺脲类", "examples": ["格列美脲", "格列齐特", "格列吡嗪"], "first_line": True},
        {"class": "DPP-4i", "class_cn": "DPP-4抑制剂", "examples": ["西格列汀", "沙格列汀"], "first_line": True},
        {"class": "SGLT2i", "class_cn": "SGLT-2抑制剂", "examples": ["达格列净", "恩格列净"], "first_line": True},
        {"class": "GLP-1RA", "class_cn": "GLP-1受体激动剂", "examples": ["利拉鲁肽", "司美格鲁肽"], "first_line": False},
        {"class": "Insulin", "class_cn": "胰岛素", "examples": ["甘精胰岛素", "门冬胰岛素"], "first_line": False},
    ]},
    {"disease": "CHD", "classes": [
        {"class": "Statin", "class_cn": "他汀类", "examples": ["阿托伐他汀", "瑞舒伐他汀", "辛伐他汀"], "first_line": True},
        {"class": "Antiplatelet", "class_cn": "抗血小板", "examples": ["阿司匹林", "氯吡格雷"], "first_line": True},
        {"class": "Beta-blocker", "class_cn": "β受体阻滞剂", "examples": ["美托洛尔"], "first_line": True},
        {"class": "ACEI/ARB", "class_cn": "ACEI/ARB类", "examples": ["培哚普利", "缬沙坦"], "first_line": True},
        {"class": "Nitrate", "class_cn": "硝酸酯类", "examples": ["单硝酸异山梨酯"], "first_line": False},
    ]},
    {"disease": "STROKE", "classes": [
        {"class": "Antiplatelet", "class_cn": "抗血小板", "examples": ["阿司匹林", "氯吡格雷"], "first_line": True},
        {"class": "Statin", "class_cn": "他汀类", "examples": ["阿托伐他汀", "瑞舒伐他汀"], "first_line": True},
        {"class": "ACEI/ARB", "class_cn": "ACEI/ARB类", "examples": ["培哚普利", "缬沙坦"], "first_line": True},
        {"class": "Neuroprotective", "class_cn": "神经保护剂", "examples": ["胞磷胆碱", "丁苯酞", "依达拉奉"], "first_line": True},
    ]},
    {"disease": "COPD", "classes": [
        {"class": "LAMA", "class_cn": "长效抗胆碱药", "examples": ["噻托溴铵"], "first_line": True},
        {"class": "LABA+ICS", "class_cn": "长效β激动剂+激素", "examples": ["沙美特罗替卡松", "布地奈德福莫特罗"], "first_line": True},
        {"class": "SABA", "class_cn": "短效β激动剂(急救)", "examples": ["沙丁胺醇"], "first_line": True},
        {"class": "Theophylline", "class_cn": "茶碱类", "examples": ["氨茶碱", "多索茶碱"], "first_line": False},
    ]},
    {"disease": "CKD", "classes": [
        {"class": "ACEI/ARB", "class_cn": "ACEI/ARB类(肾保护)", "examples": ["缬沙坦", "厄贝沙坦"], "first_line": True},
        {"class": "SGLT2i", "class_cn": "SGLT-2抑制剂(肾保护)", "examples": ["达格列净", "恩格列净"], "first_line": True},
        {"class": "Erythropoietin", "class_cn": "促红细胞生成素", "examples": ["重组人促红细胞生成素"], "first_line": False},
        {"class": "Iron", "class_cn": "铁剂", "examples": ["琥珀酸亚铁", "蔗糖铁"], "first_line": False},
        {"class": "PhosphateBinder", "class_cn": "磷结合剂", "examples": ["碳酸钙", "司维拉姆"], "first_line": False},
    ]},
]

DRUG_CONTRAINDICATIONS = {
    "二甲双胍": {"condition": "eGFR < 30 (CKD 4-5期)", "severity": "HIGH", "disease": "CKD"},
    "ACEI": {"condition": "血钾>5.5mmol/L 或双侧肾动脉狭窄", "severity": "HIGH"},
    "ARB": {"condition": "血钾>5.5mmol/L 或双侧肾动脉狭窄", "severity": "HIGH"},
    "阿司匹林": {"condition": "活动性消化道溃疡", "severity": "MEDIUM"},
    "华法林": {"condition": "未监测INR", "severity": "HIGH"},
    "β受体阻滞剂": {"condition": "慢阻肺急性加重期可能诱发支气管痉挛", "severity": "MEDIUM", "disease": "COPD"},
    "NSAIDs": {"condition": "CKD患者可能加重肾损伤", "severity": "HIGH", "disease": "CKD"},
    "氨茶碱": {"condition": "严重肝病/心力衰竭需减量", "severity": "LOW"},
}

SAME_CLASS_WARN = [("ACEI", "ARB"), ("CCB", "Diuretics")]


class AIRecommendationResponse(BaseModel):
    patient_id: str
    current_medications: list
    recommendations: list
    warnings: list
    summary: str


@router.post("/ai/recommend")
async def ai_prescription_recommend(
    patient_id: str = Query(..., description="患者ID"),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_active_user),
):
    """AI处方审核推荐：分析当前用药，给出建议和警告"""
    # 获取患者
    patient = (await db.execute(select(Patient).where(Patient.patient_id == patient_id))).scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # 获取当前用药
    meds_result = await db.execute(
        select(PatientMedication).where(
            PatientMedication.patient_id == patient_id,
            PatientMedication.is_active == True
        )
    )
    medications = meds_result.scalars().all()

    current_meds = [
        {
            "medication_id": m.medication_id,
            "drug_name": m.drug_name,
            "drug_class": m.drug_class,
            "dosage": m.dosage,
            "frequency": m.frequency,
            "disease_code": m.disease_code,
            "is_ai_recommended": m.is_ai_recommended,
        }
        for m in medications
    ]

    # 获取疾病列表
    disease_list = patient.disease_list or []
    if isinstance(disease_list, str):
        import json
        disease_list = json.loads(disease_list)

    # 获取最新随访数据
    latest_fu = (await db.execute(
        select(FollowupRecord).where(
            FollowupRecord.patient_id == patient_id
        ).order_by(FollowupRecord.followup_date.desc()).limit(1)
    )).scalar_one_or_none()

    recommendations = []
    warnings = []

    # 1. 检查是否有疾病遗漏了核心用药
    for disease in disease_list:
        matching_class = None
        for entry in AI_DRUG_DB:
            if entry["disease"] == disease:
                matching_class = entry
                break

        if matching_class:
            used_classes = [m["drug_class"] for m in current_meds if m.get("drug_class")]
            used_drug_names_lower = [m["drug_name"].lower() for m in current_meds] if current_meds else []
            first_line = [c for c in matching_class["classes"] if c["first_line"]]
            # 同时匹配英文类名、中文类名、以及药物名
            missing = [
                c for c in first_line
                if c["class"] not in used_classes
                and c.get("class_cn") not in used_classes
                and not any(e.lower() in un for e in c["examples"] for un in used_drug_names_lower)
            ]

            if missing:
                for m_cls in missing:
                    cn_label = m_cls.get("class_cn", m_cls["class"])
                    confidence = 0.85 if len(disease_list) == 1 else 0.70
                    recommendations.append({
                        "type": "ADD",
                        "disease_code": disease,
                        "drug_class": m_cls["class"],
                        "class_cn": cn_label,
                        "suggested_drugs": m_cls["examples"],
                        "reason": f"{disease} 核心治疗推荐，当前未使用{cn_label}药物",
                        "confidence": confidence,
                        "evidence_level": "A" if m_cls["first_line"] else "B",
                    })

    # 2. 检查药物相互作用警告
    used_drug_names = [m["drug_name"] for m in current_meds]
    used_drug_classes = [m.get("drug_class", "") for m in current_meds]
    dl = disease_list
    for drug_name, info in DRUG_CONTRAINDICATIONS.items():
        # match drug name OR drug class
        name_match = drug_name in used_drug_names
        class_match = any(drug_name in cls for cls in used_drug_classes)
        if name_match or class_match:
            restriction_disease = info.get("disease", "")
            # If drug restricted for a disease that patient has, warn
            if restriction_disease and restriction_disease in dl:
                warnings.append({
                    "type": "CONTRAINDICATION",
                    "drug": drug_name,
                    "condition": restriction_disease,
                    "severity": info["severity"],
                    "message": f"患者合并{restriction_disease}，{drug_name}需谨慎: {info['condition']}",
                })

    # 3. 检查血压/血糖达标情况
    if latest_fu:
        if latest_fu.bp_systolic and latest_fu.bp_diastolic:
            if latest_fu.bp_systolic >= 160 or latest_fu.bp_diastolic >= 100:
                warnings.append({
                    "type": "UNCONTROLLED",
                    "metric": "BP",
                    "value": f"{latest_fu.bp_systolic}/{latest_fu.bp_diastolic}",
                    "severity": "HIGH",
                    "message": f"血压{latest_fu.bp_systolic}/{latest_fu.bp_diastolic}mmHg未达标，建议调整降压方案",
                })
            elif latest_fu.bp_systolic >= 140 or latest_fu.bp_diastolic >= 90:
                warnings.append({
                    "type": "BORDERLINE",
                    "metric": "BP",
                    "value": f"{latest_fu.bp_systolic}/{latest_fu.bp_diastolic}",
                    "severity": "MEDIUM",
                    "message": f"血压{latest_fu.bp_systolic}/{latest_fu.bp_diastolic}mmHg临界值，建议调整生活方式或加用小剂量药物",
                })

        if latest_fu.fbg and latest_fu.fbg >= 7.0:
            warnings.append({
                "type": "UNCONTROLLED",
                "metric": "FBG",
                "value": str(latest_fu.fbg),
                "severity": "HIGH",
                "message": f"空腹血糖{latest_fu.fbg}mmol/L未达标(<7.0)",
            })

    # 4. 检查同类重复用药
    used_classes_list = [m.get("drug_class") for m in current_meds if m.get("drug_class")]
    for pair in SAME_CLASS_WARN:
        if pair[0] in used_classes_list and pair[1] in used_classes_list:
            warnings.append({
                "type": "DUPLICATE",
                "drugs": f"{pair[0]} + {pair[1]}",
                "severity": "LOW",
                "message": f"{pair[0]}+{pair[1]}联用需监测血压/电解质，注意低血压风险",
            })

    # 生成总结
    if not recommendations and not warnings:
        summary = "✅ 当前用药方案合理，各项指标达标，继续维持"
    elif recommendations and not warnings:
        summary = f"💡 建议补充 {len(recommendations)} 类核心用药，完善治疗方案"
    elif warnings and not recommendations:
        high_warn = [w for w in warnings if w["severity"] == "HIGH"]
        summary = f"⚠️ 发现 {len(warnings)} 个警示（{len(high_warn)}个高风险），建议人工审核"
    else:
        summary = f"🔍 检测到 {len(recommendations)} 个用药建议和 {len(warnings)} 个风险提示，建议综合评估"

    return {
        "patient_id": patient_id,
        "current_medications": current_meds,
        "recommendations": recommendations,
        "warnings": warnings,
        "summary": summary,
        "total_warnings": len(warnings),
        "total_recommendations": len(recommendations),
    }


# ============ 手动评估 + 一键发送处方 (P0 — 会议纪要需求) ============

from pydantic import BaseModel, Field

class ManualPrescriptionCreate(BaseModel):
    patient_id: str = Field(..., description="患者ID")
    drug_name: str = Field(..., description="药品名称")
    dosage: str = Field(..., description="用量 eg. '5mg'")
    frequency: str = Field(..., description="频次 eg. '每日1次'")
    duration: str = Field("", description="疗程 eg. '30天'")
    notes: str = Field("", description="备注/医嘱")
    review_reason: str = Field("", description="评估理由")


@router.post("/manual/assess")
async def manual_assess(
    body: ManualPrescriptionCreate,
    current_user: dict = Depends(get_current_active_user),
):
    """医生手动评估患者并创建处方"""
    import uuid
    from app.db.session import get_db
    from sqlalchemy import text as sa_text

    review_id = f"rv_{uuid.uuid4().hex[:10]}"
    now = datetime.now().isoformat()

    async for db in get_db():
        try:
            # 查询患者姓名
            from app.models import Patient as PatientModel
            from sqlalchemy import select as sa_select

            result = await db.execute(
                sa_select(PatientModel).where(PatientModel.patient_id == body.patient_id)
            )
            patient = result.scalar_one_or_none()
            patient_name = patient.name_enc if patient else ""

            # 插入处方审核记录
            med_id = f"med_{uuid.uuid4().hex[:8]}"
            await db.execute(
                sa_text("""
                    INSERT INTO prescription_review 
                    (review_id, medication_id, patient_id, review_type, original_drug, original_dosage,
                     suggested_drug, suggested_dosage, suggested_frequency,
                     review_reason, review_result, reviewed_by, reviewed_org,
                     prescribed_by, notes, created_at, is_applied)
                    VALUES (:rid, :mid, :pid, 'manual',
                     :drug, :dosage,
                     :drug, :dosage, :freq,
                     :reason, 'approved', :rby, :rorg,
                     :rby, :notes, :now, 0)
                """),
                {
                    "rid": review_id, "mid": med_id, "pid": body.patient_id,
                    "drug": body.drug_name, "dosage": body.dosage,
                    "freq": body.frequency, "reason": body.review_reason or "医生手动评估",
                    "rby": current_user.username, "rorg": getattr(current_user, "manage_org_code", "") or getattr(current_user, "org_code", "") or "",
                    "notes": body.notes, "now": now,
                }
            )
            await db.commit()

            return {
                "success": True,
                "review_id": review_id,
                "patient_id": body.patient_id,
                "patient_name": patient_name,
                "drug_name": body.drug_name,
                "dosage": body.dosage,
                "frequency": body.frequency,
                "created_at": now,
                "message": "处方已创建，可发送至患者微信",
            }
        except Exception as e:
            await db.rollback()
            return {"success": False, "error": str(e)}


@router.post("/{review_id}/send-wechat")
async def send_prescription_wechat(
    review_id: str,
    current_user: dict = Depends(get_current_active_user),
):
    """一键将处方发送至患者微信"""
    from app.db.session import get_db
    from sqlalchemy import text as sa_text

    async for db in get_db():
        try:
            # 查询处方记录
            result = await db.execute(
                sa_text("""
                    SELECT pr.*, p.name_enc AS patient_name, p.phone_enc AS phone
                    FROM prescription_review pr
                    JOIN patient p ON pr.patient_id = p.patient_id
                    WHERE pr.review_id = :rid
                """),
                {"rid": review_id}
            )
            row = result.fetchone()
            if not row:
                return {"success": False, "error": "处方记录不存在"}

            row_dict = dict(row._mapping)

            # 发送微信推送（开发环境模拟）
            from app.services.wechat_push_service import push_prescription
            openid = row_dict.get("phone", "") or "DEV_" + row_dict.get("patient_id", "unknown")
            push_result = await push_prescription(
                patient_id=row_dict["patient_id"],
                openid=openid,
                drug_name=row_dict.get("suggested_drug", "") or row_dict.get("original_drug", ""),
                dosage=row_dict.get("suggested_dosage", "") or row_dict.get("original_dosage", ""),
                frequency=row_dict.get("suggested_frequency", "") or "",
                duration=row_dict.get("review_reason", ""),
                notes=row_dict.get("notes", ""),
                prescriber=current_user.username,
            )

            # 标记已发送
            await db.execute(
                sa_text("UPDATE prescription_review SET is_applied = 1, applied_at = :now WHERE review_id = :rid"),
                {"now": datetime.now().isoformat(), "rid": review_id}
            )
            await db.commit()

            return {
                "success": True,
                "review_id": review_id,
                "patient_name": row_dict.get("patient_name", ""),
                "wechat_status": push_result,
                "message": "处方已发送至患者微信",
            }
        except Exception as e:
            await db.rollback()
            return {"success": False, "error": str(e)}
