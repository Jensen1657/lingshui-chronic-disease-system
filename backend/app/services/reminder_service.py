"""
随访提醒业务逻辑服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime, timedelta

from app.models import FollowupReminder, Patient
from app.schemas.reminder import ReminderCreate, ReminderUpdate


class ReminderService:
    """随访提醒服务类"""

    @staticmethod
    async def get_reminders(
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100,
            patient_id: Optional[UUID] = None,
            disease_code: Optional[str] = None,
            plan_type: Optional[str] = None,
            channel: Optional[str] = None,
            status: Optional[str] = None,
            is_sent: Optional[bool] = None,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None
    ) -> tuple[List[FollowupReminder], int]:
        """
        获取随访提醒列表（支持筛选和分页）
        """
        # 构建查询
        query = select(FollowupReminder)

        # 应用筛选条件
        if patient_id:
            query = query.where(FollowupReminder.patient_id == patient_id)
        if disease_code:
            query = query.where(FollowupReminder.disease_code == disease_code)
        if plan_type:
            query = query.where(FollowupReminder.plan_type == plan_type)
        if channel:
            query = query.where(FollowupReminder.channel == channel)
        if status:
            query = query.where(FollowupReminder.status == status)
        if is_sent is not None:
            query = query.where(FollowupReminder.is_sent == is_sent)
        if start_date:
            query = query.where(FollowupReminder.plan_date >= start_date)
        if end_date:
            query = query.where(FollowupReminder.plan_date <= end_date)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.execute(count_query)
        total = total.scalar_one()

        # 分页
        query = query.offset(skip).limit(limit)

        # 执行查询
        result = await db.execute(query)
        reminders = result.scalars().all()

        return reminders, total

    @staticmethod
    async def get_reminder_by_id(db: AsyncSession, reminder_id: UUID) -> Optional[FollowupReminder]:
        """根据 ID 获取随访提醒记录"""
        result = await db.execute(
            select(FollowupReminder).where(FollowupReminder.reminder_id == reminder_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_reminder(db: AsyncSession, reminder: ReminderCreate) -> FollowupReminder:
        """创建随访提醒记录"""
        # 检查患者是否存在
        patient_result = await db.execute(
            select(Patient).where(Patient.patient_id == reminder.patient_id)
        )
        if not patient_result.scalar_one_or_none():
            raise ValueError(f"患者 {reminder.patient_id} 不存在")

        # 创建随访提醒记录
        db_reminder = FollowupReminder(
            **reminder.model_dump()
        )

        db.add(db_reminder)
        await db.commit()
        await db.refresh(db_reminder)

        return db_reminder

    @staticmethod
    async def update_reminder(
            db: AsyncSession,
            reminder_id: UUID,
            reminder_update: ReminderUpdate
    ) -> Optional[FollowupReminder]:
        """更新随访提醒记录"""
        result = await db.execute(
            select(FollowupReminder).where(FollowupReminder.reminder_id == reminder_id)
        )
        db_reminder = result.scalar_one_or_none()

        if not db_reminder:
            return None

        # 更新非空字段
        update_data = reminder_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_reminder, field, value)

        await db.commit()
        await db.refresh(db_reminder)

        return db_reminder

    @staticmethod
    async def delete_reminder(db: AsyncSession, reminder_id: UUID) -> bool:
        """删除随访提醒记录"""
        result = await db.execute(
            select(FollowupReminder).where(FollowupReminder.reminder_id == reminder_id)
        )
        db_reminder = result.scalar_one_or_none()

        if not db_reminder:
            return False

        # 硬删除
        await db.delete(db_reminder)
        await db.commit()

        return True

    @staticmethod
    async def send_reminder(
            db: AsyncSession,
            reminder_id: UUID
    ) -> Optional[FollowupReminder]:
        """发送随访提醒"""
        result = await db.execute(
            select(FollowupReminder).where(FollowupReminder.reminder_id == reminder_id)
        )
        db_reminder = result.scalar_one_or_none()

        if not db_reminder:
            return None

        if db_reminder.is_sent:
            raise ValueError("该提醒已发送")

        # TODO: 实际实现需要调用短信/微信等渠道发送提醒
        # 临时标记为已发送
        db_reminder.is_sent = True
        db_reminder.sent_at = datetime.now()
        db_reminder.status = "SENT"

        await db.commit()
        await db.refresh(db_reminder)

        return db_reminder

    @staticmethod
    async def cancel_reminder(
            db: AsyncSession,
            reminder_id: UUID
    ) -> Optional[FollowupReminder]:
        """取消随访提醒"""
        result = await db.execute(
            select(FollowupReminder).where(FollowupReminder.reminder_id == reminder_id)
        )
        db_reminder = result.scalar_one_or_none()

        if not db_reminder:
            return None

        if db_reminder.is_sent:
            raise ValueError("已发送的提醒无法取消")

        # 更新状态为已取消
        db_reminder.status = "CANCELLED"

        await db.commit()
        await db.refresh(db_reminder)

        return db_reminder

    @staticmethod
    async def get_upcoming_reminders(
            db: AsyncSession,
            patient_id: Optional[UUID] = None,
            days: int = 7
    ) -> List[FollowupReminder]:
        """获取即将到来的随访提醒"""
        today = date.today()
        end_date = today + timedelta(days=days)

        query = select(FollowupReminder).where(
            FollowupReminder.plan_date >= today,
            FollowupReminder.plan_date <= end_date,
            FollowupReminder.status == "PENDING"
        )

        if patient_id:
            query = query.where(FollowupReminder.patient_id == patient_id)

        query = query.order_by(FollowupReminder.plan_date.asc())

        result = await db.execute(query)
        reminders = result.scalars().all()

        return reminders

    @staticmethod
    async def get_reminder_stats(
            db: AsyncSession,
            org_code: Optional[str] = None,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """获取随访提醒统计信息"""
        # TODO: 实现随访提醒统计逻辑
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
