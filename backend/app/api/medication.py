"""
患者用药记录 API — 内科陈丹要求查看患者用药记录 + 叶胜业处方指导
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date, datetime

from app.db.session import get_db
from app.models.meeting_models import PatientMedication
from app.models import Patient

router = APIRouter(tags=["用药记录"])


# ===== Schemas =====
class MedicationCreate(BaseModel):
    patient_id: str
    disease_code: str
    drug_name: str
    drug_class: Optional[str] = None
    specification: Optional[str] = None
    dosage: str
    frequency: str
    route: str = "口服"
    start_date: date
    end_date: Optional[date] = None
    is_long_term: bool = True
    prescribed_org: Optional[str] = None
    notes: Optional[str] = None


class MedicationUpdate(BaseModel):
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    adjust_reason: Optional[str] = None
    side_effects: Optional[str] = None
    adherence_status: Optional[str] = None
    notes: Optional[str] = None


class MedicationResponse(BaseModel):
    medication_id: str
    patient_id: str
    disease_code: str
    drug_name: str
    drug_class: Optional[str] = None
    specification: Optional[str] = None
    dosage: str
    frequency: str
    route: str
    start_date: str
    end_date: Optional[str] = None
    is_long_term: bool
    is_active: bool
    prescribed_org: Optional[str] = None
    adjust_reason: Optional[str] = None
    adherence_status: Optional[str] = None
    side_effects: Optional[str] = None
    notes: Optional[str] = None
    is_ai_recommended: bool = False
    created_at: str
    updated_at: Optional[str] = None
    # joined fields
    patient_name: Optional[str] = None
    drug_class_name: Optional[str] = None


class MedicationListResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    page_size: int


# ===== Helper =====
async def _med_to_dict(m: PatientMedication, db: AsyncSession) -> dict:
    d = {
        "medication_id": m.medication_id, "patient_id": m.patient_id,
        "disease_code": m.disease_code, "drug_name": m.drug_name,
        "drug_class": m.drug_class, "specification": m.specification,
        "dosage": m.dosage, "frequency": m.frequency, "route": m.route,
        "start_date": str(m.start_date) if m.start_date else None,
        "end_date": str(m.end_date) if m.end_date else None,
        "is_long_term": m.is_long_term, "is_active": m.is_active,
        "prescribed_org": m.prescribed_org, "adjust_reason": m.adjust_reason,
        "adherence_status": m.adherence_status, "side_effects": m.side_effects,
        "notes": m.notes, "is_ai_recommended": m.is_ai_recommended or False,
        "created_at": str(m.created_at) if m.created_at else None,
        "updated_at": str(m.updated_at) if m.updated_at else None,
    }
    # Join patient name
    if hasattr(m, 'patient') and m.patient:
        d["patient_name"] = m.patient.name_enc
    else:
        result = await db.execute(
            select(Patient).where(Patient.patient_id == m.patient_id)
        )
        p = result.scalar_one_or_none()
        d["patient_name"] = p.name_enc if p else None
    return d


# ===== Endpoints =====
@router.get("", response_model=MedicationListResponse)
async def list_medications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient_id: Optional[str] = None,
    disease_code: Optional[str] = None,
    is_active: Optional[bool] = None,
    drug_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """用药记录列表 — 支持按患者、疾病、药品筛选"""
    conditions = []
    if patient_id:
        conditions.append(PatientMedication.patient_id == patient_id)
    if disease_code:
        conditions.append(PatientMedication.disease_code == disease_code)
    if is_active is not None:
        conditions.append(PatientMedication.is_active == is_active)
    if drug_name:
        conditions.append(PatientMedication.drug_name.ilike(f"%{drug_name}%"))

    base = select(PatientMedication)
    if conditions:
        base = base.where(and_(*conditions))
    base = base.order_by(desc(PatientMedication.start_date))

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    items_q = base.offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(items_q)).scalars().all()

    items = []
    for m in rows:
        items.append(await _med_to_dict(m, db))

    return MedicationListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/patient/{patient_id}")
async def get_patient_medications(
    patient_id: str,
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """获取单个患者的全部用药记录（支持图表化展示）"""
    q = select(PatientMedication).where(
        PatientMedication.patient_id == patient_id
    )
    if active_only:
        q = q.where(PatientMedication.is_active == True)
    q = q.order_by(desc(PatientMedication.start_date))

    rows = (await db.execute(q)).scalars().all()
    items = []
    for m in rows:
        items.append(await _med_to_dict(m, db))

    # 统计: 用药依从性
    active_count = sum(1 for m in rows if m.is_active)
    good_adherence = sum(1 for m in rows if m.adherence_status == "GOOD")

    return {
        "patient_id": patient_id,
        "items": items,
        "total": len(items),
        "active_count": active_count,
        "adherence_rate": round(good_adherence / max(active_count, 1) * 100, 1),
        "adherence_status": "GOOD" if good_adherence / max(active_count, 1) > 0.8 else "WARNING",
    }


@router.post("")
async def create_medication(
    data: MedicationCreate,
    db: AsyncSession = Depends(get_db),
):
    """添加用药记录 — 村医录入/医生处方"""
    m = PatientMedication(**data.model_dump())
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return await _med_to_dict(m, db)


@router.put("/{medication_id}")
async def update_medication(
    medication_id: str,
    data: MedicationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新用药记录（调整剂量/停药/标注副作用）"""
    result = await db.execute(
        select(PatientMedication).where(PatientMedication.medication_id == medication_id)
    )
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="用药记录不存在")

    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(m, k, v)
    await db.commit()
    await db.refresh(m)
    return await _med_to_dict(m, db)


@router.get("/adherence/stats")
async def get_medication_adherence_stats(
    org_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """用药依从率统计 — 质控指标"""
    q = select(PatientMedication).where(
        PatientMedication.is_active == True
    )
    if org_code:
        q = q.where(PatientMedication.prescribed_org == org_code)

    rows = (await db.execute(q)).scalars().all()
    total = len(rows)
    good = sum(1 for r in rows if r.adherence_status == "GOOD")
    partial = sum(1 for r in rows if r.adherence_status == "PARTIAL")
    poor = sum(1 for r in rows if r.adherence_status == "POOR")
    unknown = total - good - partial - poor

    return {
        "total_active_prescriptions": total,
        "good_adherence": good,
        "partial_adherence": partial,
        "poor_adherence": poor,
        "unknown_status": unknown,
        "adherence_rate": round(good / max(total, 1) * 100, 1),
        "org_code": org_code,
    }