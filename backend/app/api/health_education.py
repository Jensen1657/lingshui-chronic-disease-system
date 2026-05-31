"""
健康宣教模板 & 推送 API — 内科陈丹：生成模板，一键发送至患者微信
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, update
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app.models.meeting_models import HealthEducationTemplate, HealthEducationRecord
from app.dependencies.auth import get_current_active_user
from app.models import Patient, PatientWechat
from app.services.wechat_push_service import push_health_edu

router = APIRouter(tags=["健康宣教"])


# ===== Schemas =====
class TemplateCreate(BaseModel):
    title: str
    category: str  # DIET/EXERCISE/MEDICATION/MONITORING/LIFESTYLE/GENERAL
    disease_code: Optional[str] = None
    risk_level: Optional[str] = None
    content_text: str
    content_rich: Optional[str] = None
    media_urls: Optional[list] = None
    tags: Optional[list] = None


class TemplateUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content_text: Optional[str] = None
    content_rich: Optional[str] = None
    media_urls: Optional[list] = None
    tags: Optional[list] = None
    risk_level: Optional[str] = None
    is_active: Optional[bool] = None


class SendRequest(BaseModel):
    patient_id: str
    template_id: str
    sent_channel: str = "WECHAT"  # WECHAT/SMS/APP/PRINT


class BatchSendRequest(BaseModel):
    patient_ids: list[str]
    template_id: str
    sent_channel: str = "WECHAT"


# ===== Templates CRUD =====
@router.get("/templates")
async def list_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    category: Optional[str] = None,
    disease_code: Optional[str] = None,
    is_active: Optional[bool] = True,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """宣教模板列表"""
    conditions = []
    if category:
        conditions.append(HealthEducationTemplate.category == category)
    if disease_code:
        conditions.append(HealthEducationTemplate.disease_code == disease_code)
    if is_active is not None:
        conditions.append(HealthEducationTemplate.is_active == is_active)
    if keyword:
        conditions.append(HealthEducationTemplate.title.ilike(f"%{keyword}%"))

    base = select(HealthEducationTemplate)
    if conditions:
        base = base.where(and_(*conditions))
    base = base.order_by(desc(HealthEducationTemplate.usage_count))

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    rows = (await db.execute(
        base.offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

    items = [{
        "template_id": t.template_id, "title": t.title,
        "category": t.category, "disease_code": t.disease_code,
        "risk_level": t.risk_level, "content_text": t.content_text[:200],
        "content_rich": t.content_rich[:500] if t.content_rich else None,
        "media_urls": t.media_urls, "tags": t.tags,
        "usage_count": t.usage_count, "is_active": t.is_active,
        "created_at": str(t.created_at) if t.created_at else None,
    } for t in rows]

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/templates")
async def create_template(
    data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建宣教模板"""
    t = HealthEducationTemplate(**data.model_dump())
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return {"template_id": t.template_id, "title": t.title, "message": "模板创建成功"}


@router.put("/templates/{template_id}")
async def update_template(
    template_id: str,
    data: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新宣教模板"""
    result = await db.execute(
        select(HealthEducationTemplate).where(
            HealthEducationTemplate.template_id == template_id
        )
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="模板不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    await db.commit()
    return {"message": "更新成功", "template_id": template_id}


@router.get("/templates/{template_id}")
async def get_template(template_id: str, db: AsyncSession = Depends(get_db)):
    """获取模板详情（含完整内容）"""
    result = await db.execute(
        select(HealthEducationTemplate).where(
            HealthEducationTemplate.template_id == template_id
        )
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="模板不存在")
    return {
        "template_id": t.template_id, "title": t.title,
        "category": t.category, "disease_code": t.disease_code,
        "risk_level": t.risk_level,
        "content_text": t.content_text, "content_rich": t.content_rich,
        "media_urls": t.media_urls, "tags": t.tags,
        "usage_count": t.usage_count, "is_active": t.is_active,
        "created_at": str(t.created_at) if t.created_at else None,
    }


# ===== Send Records =====
@router.post("/send")
async def send_education(
    data: SendRequest,
    db: AsyncSession = Depends(get_db),
):
    """一键发送宣教内容至患者"""
    # 验证模板
    t_result = await db.execute(
        select(HealthEducationTemplate).where(
            HealthEducationTemplate.template_id == data.template_id,
            HealthEducationTemplate.is_active == True,
        )
    )
    template = t_result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在或已禁用")

    # 创建发送记录
    record = HealthEducationRecord(
        patient_id=data.patient_id,
        template_id=data.template_id,
        sent_channel=data.sent_channel,
    )
    db.add(record)

    # 更新模板使用次数
    await db.execute(
        update(HealthEducationTemplate)
        .where(HealthEducationTemplate.template_id == data.template_id)
        .values(usage_count=HealthEducationTemplate.usage_count + 1)
    )

    await db.commit()
    await db.refresh(record)

    # 调用微信推送（模拟模式，配置 WECHAT_APP_ID 后切换真实发送）
    wx_result = None
    if data.sent_channel == "WECHAT":
        try:
            # 查找患者 openid
            pw = (await db.execute(
                select(PatientWechat).where(
                    PatientWechat.patient_id == data.patient_id,
                    PatientWechat.is_active == True,
                )
            )).scalar_one_or_none()
            if pw and pw.openid:
                wx_result = await push_health_edu(
                    patient_id=data.patient_id,
                    openid=pw.openid,
                    title=template.title,
                    content=template.content_text,
                )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"微信推送失败（不影响记录）: {e}")

    return {
        "record_id": record.record_id,
        "message": "宣教内容已推送",
        "channel": data.sent_channel,
        "template_title": template.title,
        "wechat_result": wx_result,
    }


@router.post("/send/batch")
async def batch_send_education(
    data: BatchSendRequest,
    db: AsyncSession = Depends(get_db),
):
    """批量推送宣教内容"""
    t_result = await db.execute(
        select(HealthEducationTemplate).where(
            HealthEducationTemplate.template_id == data.template_id,
            HealthEducationTemplate.is_active == True,
        )
    )
    template = t_result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    records = []
    for pid in data.patient_ids:
        record = HealthEducationRecord(
            patient_id=pid, template_id=data.template_id,
            sent_channel=data.sent_channel,
        )
        db.add(record)
        records.append(record)

    await db.execute(
        update(HealthEducationTemplate)
        .where(HealthEducationTemplate.template_id == data.template_id)
        .values(usage_count=HealthEducationTemplate.usage_count + len(data.patient_ids))
    )

    await db.commit()
    return {
        "sent_count": len(records),
        "message": f"已向{len(records)}位患者推送宣教内容",
        "template_title": template.title,
    }


@router.get("/records")
async def list_send_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    patient_id: Optional[str] = None,
    template_id: Optional[str] = None,
    is_read: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """推送记录列表"""
    conditions = []
    if patient_id:
        conditions.append(HealthEducationRecord.patient_id == patient_id)
    if template_id:
        conditions.append(HealthEducationRecord.template_id == template_id)
    if is_read is not None:
        conditions.append(HealthEducationRecord.is_read == is_read)

    base = select(HealthEducationRecord)
    if conditions:
        base = base.where(and_(*conditions))
    base = base.order_by(desc(HealthEducationRecord.sent_at))

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    rows = (await db.execute(
        base.offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

    items = [{
        "record_id": r.record_id, "patient_id": r.patient_id,
        "template_id": r.template_id, "sent_channel": r.sent_channel,
        "sent_at": str(r.sent_at) if r.sent_at else None,
        "is_read": r.is_read, "read_at": str(r.read_at) if r.read_at else None,
        "patient_feedback": r.patient_feedback,
    } for r in rows]

    return {"items": items, "total": total, "page": page, "page_size": page_size}


# ===== Categories =====
@router.get("/categories")
async def get_categories():
    """宣教模板分类"""
    return {
        "categories": [
            {"code": "DIET", "name": "饮食指导"},
            {"code": "EXERCISE", "name": "运动指导"},
            {"code": "MEDICATION", "name": "用药教育"},
            {"code": "MONITORING", "name": "自我监测"},
            {"code": "LIFESTYLE", "name": "生活方式"},
            {"code": "GENERAL", "name": "综合宣教"},
        ]
    }


@router.get("/stats")
async def get_health_edu_stats(
    org_code: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_active_user),
):
    """健康宣教效果统计：推送渠道分布、阅读率、反馈率、Top模板"""
    # 总推送量
    total_result = await db.execute(select(func.count(HealthEducationRecord.record_id)))
    total_sends = total_result.scalar() or 0

    # 渠道分布
    channel_result = await db.execute(
        select(
            HealthEducationRecord.sent_channel,
            func.count(HealthEducationRecord.record_id)
        ).group_by(HealthEducationRecord.sent_channel)
    )
    channel_stats = {row[0]: row[1] for row in channel_result.fetchall()}

    # 阅读率
    read_count = (await db.execute(
        select(func.count(HealthEducationRecord.record_id)).where(
            HealthEducationRecord.is_read == True
        )
    )).scalar() or 0
    read_rate = round(read_count / total_sends * 100, 1) if total_sends > 0 else 0

    # 反馈率
    feedback_count = (await db.execute(
        select(func.count(HealthEducationRecord.record_id)).where(
            HealthEducationRecord.patient_feedback.isnot(None),
            HealthEducationRecord.patient_feedback != ''
        )
    )).scalar() or 0
    feedback_rate = round(feedback_count / total_sends * 100, 1) if total_sends > 0 else 0

    # 月度推送趋势
    monthly_trend = []
    try:
        trend_result = await db.execute(
            text("""
                SELECT strftime('%Y-%m', sent_at) as mon, count(*) as cnt
                FROM health_education_record
                WHERE sent_at >= date('now', '-6 months')
                GROUP BY mon ORDER BY mon
            """)
        )
        monthly_trend = [{"month": row[0], "count": row[1]} for row in trend_result.fetchall()]
    except Exception:
        pass

    # 热门模板 Top5
    top_templates = []
    try:
        tpl_result = await db.execute(
            select(
                HealthEducationTemplate.template_id,
                HealthEducationTemplate.title,
                HealthEducationTemplate.category,
                HealthEducationTemplate.usage_count,
            ).where(HealthEducationTemplate.is_active == True)
             .order_by(HealthEducationTemplate.usage_count.desc())
             .limit(5)
        )
        top_templates = [
            {"template_id": row[0], "title": row[1], "category": row[2], "usage_count": row[3]}
            for row in tpl_result.fetchall()
        ]
    except Exception:
        pass

    # 分类统计
    cat_result = await db.execute(
        select(
            HealthEducationTemplate.category,
            func.count(HealthEducationTemplate.template_id),
            func.sum(HealthEducationTemplate.usage_count)
        ).where(HealthEducationTemplate.is_active == True)
         .group_by(HealthEducationTemplate.category)
    )
    category_stats = [
        {"category": row[0], "template_count": row[1], "usage_count": row[2] or 0}
        for row in cat_result.fetchall()
    ]

    return {
        "total_sends": total_sends,
        "channel_stats": channel_stats,
        "read_rate": read_rate,
        "read_count": read_count,
        "feedback_rate": feedback_rate,
        "feedback_count": feedback_count,
        "monthly_trend": monthly_trend,
        "top_templates": top_templates,
        "category_stats": category_stats,
    }