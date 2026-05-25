"""
随访提醒管理路由 - CRUD 操作
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime, timedelta

from app.db.session import get_db
from app.dependencies.auth import require_roles
from app.models import FollowupReminder, Patient
from app.schemas.reminder import (
    ReminderCreate, ReminderUpdate, ReminderResponse,
    ReminderSearchParams, ReminderStats, PaginatedReminderResponse
)

router = APIRouter()


def format_reminder(reminder):
    """Convert database model to dict matching schema fields"""
    return {
        "reminder_id": str(reminder.reminder_id),
        "patient_id": str(reminder.patient_id),
        "disease_code": None,  # 数据库模型没有这个字段
        "plan_date": reminder.remind_at.date() if reminder.remind_at else None,
        "plan_type": reminder.reminder_type,
        "channel": "WECHAT",  # 默认渠道
        "status": "SENT" if reminder.is_sent else "PENDING",
        "is_sent": reminder.is_sent,
        "sent_at": reminder.sent_at,
        "created_at": reminder.created_at
    }


@router.post("/", status_code=201)
async def create_reminder(
        reminder: ReminderCreate,
        db: AsyncSession = Depends(get_db)
):
    """
    创建随访提醒记录
    - 检查患者是否存在
    - 创建随访提醒记录
    """
    # 检查患者是否存在
    patient_result = await db.execute(
        select(Patient).where(Patient.patient_id == reminder.patient_id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # 创建随访提醒记录 - 映射schema字段到数据库字段
    db_reminder = FollowupReminder(
        patient_id=reminder.patient_id,
        reminder_type=reminder.plan_type,
        remind_at=datetime.combine(reminder.plan_date, datetime.min.time()),
        is_sent=False
    )

    db.add(db_reminder)
    await db.commit()
    await db.refresh(db_reminder)

    return format_reminder(db_reminder)


@router.get("/")
async def list_reminders(
        patient_id: Optional[UUID] = Query(None),
        disease_code: Optional[str] = Query(None),
        plan_type: Optional[str] = Query(None),
        channel: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        is_sent: Optional[bool] = Query(None),
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        db: AsyncSession = Depends(get_db)
):
    """
    查询随访提醒记录列表（支持多条件筛选，分页返回）
    """
    # 构建基础查询
    base_query = select(FollowupReminder)
    count_query = select(func.count(FollowupReminder.reminder_id))

    # 应用筛选条件
    if patient_id:
        base_query = base_query.where(FollowupReminder.patient_id == patient_id)
        count_query = count_query.where(FollowupReminder.patient_id == patient_id)
    if plan_type:
        base_query = base_query.where(FollowupReminder.reminder_type == plan_type)
        count_query = count_query.where(FollowupReminder.reminder_type == plan_type)
    if is_sent is not None:
        base_query = base_query.where(FollowupReminder.is_sent == is_sent)
        count_query = count_query.where(FollowupReminder.is_sent == is_sent)
    if start_date:
        base_query = base_query.where(FollowupReminder.remind_at >= datetime.combine(start_date, datetime.min.time()))
        count_query = count_query.where(FollowupReminder.remind_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        base_query = base_query.where(FollowupReminder.remind_at <= datetime.combine(end_date, datetime.max.time()))
        count_query = count_query.where(FollowupReminder.remind_at <= datetime.combine(end_date, datetime.max.time()))

    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    offset = (page - 1) * page_size
    query = base_query.offset(offset).limit(page_size)

    result = await db.execute(query)
    reminders = result.scalars().all()

    return {
        "items": [format_reminder(r) for r in reminders],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{reminder_id}")
async def get_reminder(
        reminder_id: str,
        db: AsyncSession = Depends(get_db)
):
    """
    根据 ID 获取随访提醒记录详情
    """
    result = await db.execute(
        select(FollowupReminder).where(FollowupReminder.reminder_id == reminder_id)
    )
    reminder = result.scalar_one_or_none()

    if not reminder:
        raise HTTPException(status_code=404, detail="随访提醒记录不存在")

    return format_reminder(reminder)


@router.put("/{reminder_id}")
async def update_reminder(
        reminder_id: str,
        reminder_update: ReminderUpdate,
        db: AsyncSession = Depends(get_db)
):
    """
    更新随访提醒记录
    """
    result = await db.execute(
        select(FollowupReminder).where(FollowupReminder.reminder_id == reminder_id)
    )
    db_reminder = result.scalar_one_or_none()

    if not db_reminder:
        raise HTTPException(status_code=404, detail="随访提醒记录不存在")

    # 更新非空字段
    update_data = reminder_update.model_dump(exclude_unset=True)
    # 映射schema字段到数据库字段
    if "plan_date" in update_data:
        db_reminder.remind_at = datetime.combine(update_data["plan_date"], datetime.min.time())
    if "plan_type" in update_data:
        db_reminder.reminder_type = update_data["plan_type"]
    if "is_sent" in update_data:
        db_reminder.is_sent = update_data["is_sent"]
    if "sent_at" in update_data:
        db_reminder.sent_at = update_data["sent_at"]

    await db.commit()
    await db.refresh(db_reminder)

    return format_reminder(db_reminder)


@router.post("/{reminder_id}/send")
async def send_reminder(
        reminder_id: str,
        db: AsyncSession = Depends(get_db)
):
    """
    发送随访提醒
    """
    result = await db.execute(
        select(FollowupReminder).where(FollowupReminder.reminder_id == reminder_id)
    )
    db_reminder = result.scalar_one_or_none()

    if not db_reminder:
        raise HTTPException(status_code=404, detail="随访提醒记录不存在")

    if db_reminder.is_sent:
        raise HTTPException(status_code=400, detail="该提醒已发送")

    # 标记为已发送
    db_reminder.is_sent = True
    db_reminder.sent_at = datetime.now()

    await db.commit()

    return {"message": "随访提醒已发送"}


@router.post("/{reminder_id}/cancel")
async def cancel_reminder(
        reminder_id: str,
        cancel_reason: Optional[str] = None,
        db: AsyncSession = Depends(get_db)
):
    """
    取消随访提醒
    """
    result = await db.execute(
        select(FollowupReminder).where(FollowupReminder.reminder_id == reminder_id)
    )
    db_reminder = result.scalar_one_or_none()

    if not db_reminder:
        raise HTTPException(status_code=404, detail="随访提醒记录不存在")

    if db_reminder.is_sent:
        raise HTTPException(status_code=400, detail="已发送的提醒无法取消")

    # 删除提醒记录
    await db.delete(db_reminder)
    await db.commit()

    return {"message": "随访提醒已取消"}


@router.get("/stats/summary")
async def get_reminder_stats(
        org_code: Optional[str] = Query(None),
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        db: AsyncSession = Depends(get_db)
):
    """
    获取随访提醒统计信息
    """
    from sqlalchemy import case
    
    # 构建筛选条件
    filters = []
    if start_date:
        filters.append(FollowupReminder.remind_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        filters.append(FollowupReminder.remind_at <= datetime.combine(end_date, datetime.max.time()))
    
    # 如果有 org_code 筛选，需要 JOIN Patient 表获取机构信息
    if org_code:
        # 需要先获取该机构的患者ID列表
        patient_result = await db.execute(
            select(Patient.patient_id).where(Patient.manage_org_code == org_code)
        )
        patient_ids = [row[0] for row in patient_result.all()]
        if patient_ids:
            filters.append(FollowupReminder.patient_id.in_(patient_ids))
        else:
            # 没有该机构的患者，直接返回空统计
            return {
                "total_reminders": 0,
                "by_type": {},
                "by_channel": {},
                "by_status": {},
                "sent_count": 0,
                "pending_count": 0,
                "failed_count": 0,
                "sent_rate": 0.0
            }
    
    # total_reminders: 总提醒数
    total_result = await db.execute(
        select(func.count(FollowupReminder.reminder_id)).where(and_(*filters) if filters else True)
    )
    total_reminders = total_result.scalar() or 0
    
    # by_type: 按提醒类型分组
    type_result = await db.execute(
        select(FollowupReminder.reminder_type, func.count(FollowupReminder.reminder_id))
        .where(and_(*filters) if filters else True)
        .group_by(FollowupReminder.reminder_type)
    )
    by_type = {row[0]: row[1] for row in type_result.all() if row[0]}
    
    # by_channel: 按渠道分组（数据库中可能没有此字段，默认返回空）
    by_channel = {}
    
    # by_status: 按状态分组（已发送/待发送）
    status_result = await db.execute(
        select(FollowupReminder.is_sent, func.count(FollowupReminder.reminder_id))
        .where(and_(*filters) if filters else True)
        .group_by(FollowupReminder.is_sent)
    )
    by_status = {}
    for row in status_result.all():
        status_key = "SENT" if row[0] else "PENDING"
        by_status[status_key] = row[1]
    
    # sent_count: 已发送数量
    sent_result = await db.execute(
        select(func.count(FollowupReminder.reminder_id))
        .where(and_(*filters) if filters else True)
        .where(FollowupReminder.is_sent == True)
    )
    sent_count = sent_result.scalar() or 0
    
    # pending_count: 待发送数量
    pending_result = await db.execute(
        select(func.count(FollowupReminder.reminder_id))
        .where(and_(*filters) if filters else True)
        .where(FollowupReminder.is_sent == False)
    )
    pending_count = pending_result.scalar() or 0
    
    # failed_count: 失败数量（数据库可能没有此字段，默认为0）
    failed_count = 0
    
    # sent_rate: 发送率
    sent_rate = (sent_count / total_reminders * 100) if total_reminders > 0 else 0.0
    
    return {
        "total_reminders": total_reminders,
        "by_type": by_type,
        "by_channel": by_channel,
        "by_status": by_status,
        "sent_count": sent_count,
        "pending_count": pending_count,
        "failed_count": failed_count,
        "sent_rate": round(sent_rate, 2)
    }


@router.get("/patient/{patient_id}/upcoming")
async def get_upcoming_reminders(
        patient_id: str,
        days: int = Query(7, ge=1, le=30, description="未来天数"),
        db: AsyncSession = Depends(get_db)
):
    """
    获取患者即将到来的随访提醒
    """
    today = date.today()
    end_date = today + timedelta(days=days)

    query = select(FollowupReminder).where(
        FollowupReminder.patient_id == patient_id,
        FollowupReminder.remind_at >= datetime.combine(today, datetime.min.time()),
        FollowupReminder.remind_at <= datetime.combine(end_date, datetime.max.time()),
        FollowupReminder.is_sent == False
    ).order_by(FollowupReminder.remind_at.asc())

    result = await db.execute(query)
    reminders = result.scalars().all()

    return [format_reminder(r) for r in reminders]
