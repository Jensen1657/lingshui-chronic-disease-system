"""
年度评估管理路由 - CRUD 操作
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from app.utils.constants import enc, ORG_NAME_MAP
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.db.session import get_db
from app.dependencies.auth import require_roles, get_current_active_user
from app.models import AnnualAssessment, Patient, SysUser  # 从 models/__init__.py 导入
from app.schemas.assessment import (
    AssessmentCreate, AssessmentUpdate, AssessmentResponse,
    AssessmentSearchParams, AssessmentStats, AssessmentReport, PaginatedAssessmentResponse
)
from app.utils.data_permission import build_org_filter
from app.utils.cache import get as cache_get, set as cache_set, invalidate, DASHBOARD_STATS_KEY, DASHBOARD_KPI_KEY

router = APIRouter()


@router.post("/", response_model=AssessmentResponse, status_code=201)
async def create_assessment(
        assessment: AssessmentCreate,
        current_user: SysUser = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
):
    """
    创建年度评估记录
    - 检查患者是否存在
    - 检查是否已存在同年度的评估记录
    - 创建评估记录
    """
    # 检查患者是否存在
    patient_result = await db.execute(
        select(Patient).where(Patient.patient_id == assessment.patient_id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # 检查是否已存在同年度的评估记录
    existing_result = await db.execute(
        select(AnnualAssessment).where(
            AnnualAssessment.patient_id == assessment.patient_id,
            AnnualAssessment.disease_code == assessment.disease_code,
            AnnualAssessment.assessment_year == assessment.assessment_year
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该患者该疾病在同一年度已有评估记录")

    # 创建评估记录
    db_assessment = AnnualAssessment(
        patient_id=assessment.patient_id,
        disease_code=assessment.disease_code,
        assessment_year=assessment.assessment_year,
        bp_controlled_rate=assessment.bp_controlled_rate,
        bg_controlled_rate=assessment.bg_controlled_rate,
        lipid_controlled_rate=assessment.lipid_controlled_rate,
        followup_completion_rate=assessment.followup_completion_rate,
        eye_exam_done=assessment.eye_exam_done,
        foot_exam_done=assessment.foot_exam_done,
        echo_done=assessment.echo_done,
        report_content=assessment.report_content,
        report_url=assessment.report_url,
        assessed_by=current_user.username,
    )

    db.add(db_assessment)
    await db.commit()

    # 清除仪表盘缓存
    invalidate(DASHBOARD_STATS_KEY)
    await db.refresh(db_assessment)

    return db_assessment


@router.get("/")
async def list_assessments(
        patient_id: Optional[str] = Query(None),
        disease_code: Optional[str] = Query(None),
        assessment_year: Optional[int] = Query(None),
        org_code: Optional[str] = Query(None),
        min_bp_controlled_rate: Optional[float] = Query(None),
        max_bp_controlled_rate: Optional[float] = Query(None),
        eye_exam_done: Optional[bool] = Query(None),
        foot_exam_done: Optional[bool] = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        current_user: SysUser = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
):
    """
    查询年度评估记录列表（支持多条件筛选，分页返回）
    """
    # 构建基础查询 - JOIN Patient 获取 org_code
    base_query = select(AnnualAssessment).join(Patient, AnnualAssessment.patient_id == Patient.patient_id)
    count_query = select(func.count(AnnualAssessment.assessment_id)).join(
        Patient, AnnualAssessment.patient_id == Patient.patient_id
    )

    # ===== 数据权限过滤（通过 Patient.manage_org_code）=====
    org_filter = build_org_filter(Patient.manage_org_code, current_user)
    if org_filter is not None:
        base_query = base_query.where(org_filter)
        count_query = count_query.where(org_filter)

    # 应用筛选条件
    if patient_id:
        base_query = base_query.where(AnnualAssessment.patient_id == patient_id)
        count_query = count_query.where(AnnualAssessment.patient_id == patient_id)
    if disease_code:
        base_query = base_query.where(AnnualAssessment.disease_code == disease_code)
        count_query = count_query.where(AnnualAssessment.disease_code == disease_code)
    if assessment_year:
        base_query = base_query.where(AnnualAssessment.assessment_year == assessment_year)
        count_query = count_query.where(AnnualAssessment.assessment_year == assessment_year)
    if min_bp_controlled_rate is not None:
        base_query = base_query.where(AnnualAssessment.bp_controlled_rate >= min_bp_controlled_rate)
        count_query = count_query.where(AnnualAssessment.bp_controlled_rate >= min_bp_controlled_rate)
    if max_bp_controlled_rate is not None:
        base_query = base_query.where(AnnualAssessment.bp_controlled_rate <= max_bp_controlled_rate)
        count_query = count_query.where(AnnualAssessment.bp_controlled_rate <= max_bp_controlled_rate)
    if eye_exam_done is not None:
        base_query = base_query.where(AnnualAssessment.eye_exam_done == eye_exam_done)
        count_query = count_query.where(AnnualAssessment.eye_exam_done == eye_exam_done)
    if foot_exam_done is not None:
        base_query = base_query.where(AnnualAssessment.foot_exam_done == foot_exam_done)
        count_query = count_query.where(AnnualAssessment.foot_exam_done == foot_exam_done)
    
    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页
    skip = (page - 1) * page_size
    query = select(AnnualAssessment, Patient.name_enc.label("patient_name_enc"), Patient.manage_org_code.label("manage_org_code"))\
        .outerjoin(Patient, AnnualAssessment.patient_id == Patient.patient_id)\
        .offset(skip).limit(page_size).order_by(AnnualAssessment.created_at.desc())
    
    result = await db.execute(query)
    rows = result.all()
    

    items = []
    for row in rows:
        assessment = row[0]
        name_enc = row[1]
        patient_name = None
        if name_enc:
            try:
                patient_name = enc.decrypt(name_enc)
            except Exception:
                patient_name = str(assessment.patient_id)
        else:
            patient_name = str(assessment.patient_id)
        org_code = row[2] or ""
        org_name = ORG_NAME_MAP.get(org_code, org_code or "-") if org_code else "-"
        data = {**{k: v for k, v in assessment.__dict__.items() if not k.startswith('_')},
                "patient_name": patient_name, "org_name": org_name}
        items.append(data)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
        assessment_id: str,
        db: AsyncSession = Depends(get_db)
):
    """
    根据 ID 获取年度评估记录详情（带缓存）
    """
    cache_key = f"assessment:{assessment_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    
    result = await db.execute(
        select(AnnualAssessment).where(AnnualAssessment.assessment_id == assessment_id)
    )
    assessment = result.scalar_one_or_none()

    if not assessment:
        raise HTTPException(status_code=404, detail="年度评估记录不存在")

    data = {k: v for k, v in assessment.__dict__.items() if not k.startswith('_')}
    cache_set(cache_key, data, ttl=60)
    return data


@router.put("/{assessment_id}", response_model=AssessmentResponse)
async def update_assessment(
        assessment_id: str,
        assessment_update: AssessmentUpdate,
        db: AsyncSession = Depends(get_db)
):
    """
    更新年度评估记录
    """
    result = await db.execute(
        select(AnnualAssessment).where(AnnualAssessment.assessment_id == assessment_id)
    )
    db_assessment = result.scalar_one_or_none()

    if not db_assessment:
        raise HTTPException(status_code=404, detail="年度评估记录不存在")

    # 更新非空字段
    update_data = assessment_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_assessment, field, value)

    # 如果更新了评估数据，设置评估时间
    if 'assessed_at' not in update_data:
        db_assessment.assessed_at = func.now()

    await db.commit()

    # 清除仪表盘缓存
    invalidate(DASHBOARD_STATS_KEY)
    invalidate(f"assessment:{assessment_id}")
    await db.refresh(db_assessment)

    return db_assessment


@router.post("/{assessment_id}/generate-report")
async def generate_assessment_report(
        assessment_id: str,
        db: AsyncSession = Depends(get_db)
):
    """
    生成年度评估报告
    """
    result = await db.execute(
        select(AnnualAssessment).where(AnnualAssessment.assessment_id == assessment_id)
    )
    db_assessment = result.scalar_one_or_none()

    if not db_assessment:
        raise HTTPException(status_code=404, detail="年度评估记录不存在")

    # TODO: 实际实现需要生成评估报告内容
    # 临时返回示例数据
    report_content = f"患者年度评估报告（{db_assessment.assessment_year}年度）\n\n"
    report_content += "评估指标：\n"
    report_content += f"1. 血压控制率：{db_assessment.bp_controlled_rate}%\n"
    report_content += f"2. 血糖监测率：{db_assessment.bg_controlled_rate}%\n"
    report_content += f"3. 血脂控制率：{db_assessment.lipid_controlled_rate}%\n"
    report_content += f"4. 随访完成率：{db_assessment.followup_completion_rate}%\n"

    # 更新报告内容
    db_assessment.report_content = report_content
    db_assessment.assessed_at = func.now()

    await db.commit()

    # 清除仪表盘缓存
    invalidate(DASHBOARD_STATS_KEY)
    invalidate(f"assessment:{assessment_id}")

    return {"message": "评估报告已生成", "report_content": report_content}


@router.get("/stats/summary", response_model=AssessmentStats)
async def get_assessment_stats(
        org_code: Optional[str] = Query(None),
        assessment_year: Optional[int] = Query(None),
        db: AsyncSession = Depends(get_db)
):
    """
    获取年度评估统计信息
    """
    # 构建筛选条件
    filters = []
    if assessment_year:
        filters.append(AnnualAssessment.assessment_year == assessment_year)
    
    # 如果有 org_code 筛选，需要 JOIN Patient 表
    if org_code:
        # 需要先获取该机构的患者ID列表
        patient_result = await db.execute(
            select(Patient.patient_id).where(Patient.manage_org_code == org_code)
        )
        patient_ids = [row[0] for row in patient_result.all()]
        if patient_ids:
            filters.append(AnnualAssessment.patient_id.in_(patient_ids))
        else:
            # 没有该机构的患者，直接返回空统计
            return {
                "total_assessments": 0,
                "by_year": {},
                "by_disease": {},
                "by_org": {},
                "avg_bp_controlled_rate": None,
                "avg_bg_controlled_rate": None,
                "avg_lipid_controlled_rate": None,
                "avg_followup_completion_rate": None,
                "eye_exam_rate": None,
                "foot_exam_rate": None,
                "echo_done_rate": None
            }
    
    # total_assessments: 总评估数
    total_result = await db.execute(
        select(func.count(AnnualAssessment.assessment_id)).where(and_(*filters) if filters else True)
    )
    total_assessments = total_result.scalar() or 0
    
    # by_year: 按年度分组
    year_result = await db.execute(
        select(AnnualAssessment.assessment_year, func.count(AnnualAssessment.assessment_id))
        .where(and_(*filters) if filters else True)
        .group_by(AnnualAssessment.assessment_year)
    )
    by_year = {str(row[0]): row[1] for row in year_result.all() if row[0] is not None}
    
    # by_disease: 按疾病分组
    disease_result = await db.execute(
        select(AnnualAssessment.disease_code, func.count(AnnualAssessment.assessment_id))
        .where(and_(*filters) if filters else True)
        .group_by(AnnualAssessment.disease_code)
    )
    by_disease = {row[0]: row[1] for row in disease_result.all() if row[0]}
    
    # by_org: 按机构分组（需要JOIN Patient）
    by_org = {}
    if not org_code:  # 只有在没有指定 org_code 时才计算 by_org
        # JOIN Patient 获取机构信息
        org_stats_result = await db.execute(
            select(Patient.manage_org_code, func.count(AnnualAssessment.assessment_id))
            .join(Patient, AnnualAssessment.patient_id == Patient.patient_id)
            .where(and_(*filters) if filters else True)
            .group_by(Patient.manage_org_code)
        )
        by_org = {row[0]: row[1] for row in org_stats_result.all() if row[0]}
    
    # avg_bp_controlled_rate: 平均血压控制率
    avg_bp_result = await db.execute(
        select(func.avg(AnnualAssessment.bp_controlled_rate))
        .where(and_(*filters) if filters else True)
        .where(AnnualAssessment.bp_controlled_rate.isnot(None))
    )
    avg_bp_controlled_rate = avg_bp_result.scalar()
    
    # avg_bg_controlled_rate: 平均血糖监测率
    avg_bg_result = await db.execute(
        select(func.avg(AnnualAssessment.bg_controlled_rate))
        .where(and_(*filters) if filters else True)
        .where(AnnualAssessment.bg_controlled_rate.isnot(None))
    )
    avg_bg_controlled_rate = avg_bg_result.scalar()
    
    # avg_lipid_controlled_rate: 平均血脂控制率
    avg_lipid_result = await db.execute(
        select(func.avg(AnnualAssessment.lipid_controlled_rate))
        .where(and_(*filters) if filters else True)
        .where(AnnualAssessment.lipid_controlled_rate.isnot(None))
    )
    avg_lipid_controlled_rate = avg_lipid_result.scalar()
    
    # avg_followup_completion_rate: 平均随访完成率
    avg_followup_result = await db.execute(
        select(func.avg(AnnualAssessment.followup_completion_rate))
        .where(and_(*filters) if filters else True)
        .where(AnnualAssessment.followup_completion_rate.isnot(None))
    )
    avg_followup_completion_rate = avg_followup_result.scalar()
    
    # eye_exam_rate: 眼底检查完成率
    eye_exam_result = await db.execute(
        select(
            func.avg(case((AnnualAssessment.eye_exam_done == True, 1), else_=0))
        ).where(and_(*filters) if filters else True)
    )
    eye_exam_rate = eye_exam_result.scalar()
    
    # foot_exam_rate: 足病检查完成率
    foot_exam_result = await db.execute(
        select(
            func.avg(case((AnnualAssessment.foot_exam_done == True, 1), else_=0))
        ).where(and_(*filters) if filters else True)
    )
    foot_exam_rate = foot_exam_result.scalar()
    
    # echo_done_rate: 超声心动图完成率
    echo_result = await db.execute(
        select(
            func.avg(case((AnnualAssessment.echo_done == True, 1), else_=0))
        ).where(and_(*filters) if filters else True)
    )
    echo_done_rate = echo_result.scalar()
    
    return {
        "total_assessments": total_assessments,
        "by_year": by_year,
        "by_disease": by_disease,
        "by_org": by_org,
        "avg_bp_controlled_rate": float(avg_bp_controlled_rate) if avg_bp_controlled_rate else None,
        "avg_bg_controlled_rate": float(avg_bg_controlled_rate) if avg_bg_controlled_rate else None,
        "avg_lipid_controlled_rate": float(avg_lipid_controlled_rate) if avg_lipid_controlled_rate else None,
        "avg_followup_completion_rate": float(avg_followup_completion_rate) if avg_followup_completion_rate else None,
        "eye_exam_rate": float(eye_exam_rate) if eye_exam_rate else None,
        "foot_exam_rate": float(foot_exam_rate) if foot_exam_rate else None,
        "echo_done_rate": float(echo_done_rate) if echo_done_rate else None
    }


@router.get("/patient/{patient_id}/latest")
async def get_latest_assessment(
        patient_id: str,
        disease_code: Optional[str] = Query(None),
        db: AsyncSession = Depends(get_db)
):
    """
    获取患者最新一次年度评估记录
    """
    query = select(AnnualAssessment).where(AnnualAssessment.patient_id == patient_id)

    if disease_code:
        query = query.where(AnnualAssessment.disease_code == disease_code)

    query = query.order_by(AnnualAssessment.assessment_year.desc()).limit(1)

    result = await db.execute(query)
    assessment = result.scalar_one_or_none()

    if not assessment:
        raise HTTPException(status_code=404, detail="该患者无年度评估记录")

    return assessment
