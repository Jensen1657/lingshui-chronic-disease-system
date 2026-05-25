"""
随访业务逻辑服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime, timedelta

from app.models import FollowupRecord, Patient
from app.schemas.followup import FollowupCreate, FollowupUpdate


class FollowupService:
    """随访服务类"""

    @staticmethod
    async def get_followups(
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100,
            patient_id: Optional[UUID] = None,
            followup_type: Optional[str] = None,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None,
            is_completed: Optional[bool] = None
    ) -> tuple[List[FollowupRecord], int]:
        """
        获取随访列表（支持筛选和分页）
        """
        # 构建查询
        query = select(FollowupRecord)

        # 应用筛选条件
        if patient_id:
            query = query.where(FollowupRecord.patient_id == patient_id)
        if followup_type:
            query = query.where(FollowupRecord.followup_type == followup_type)
        if start_date:
            query = query.where(FollowupRecord.followup_date >= start_date)
        if end_date:
            query = query.where(FollowupRecord.followup_date <= end_date)
        if is_completed is not None:
            query = query.where(FollowupRecord.is_completed == is_completed)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.execute(count_query)
        total = total.scalar_one()

        # 分页
        query = query.offset(skip).limit(limit)

        # 执行查询
        result = await db.execute(query)
        followups = result.scalars().all()

        return followups, total

    @staticmethod
    async def get_followup_by_id(db: AsyncSession, followup_id: UUID) -> Optional[FollowupRecord]:
        """根据 ID 获取随访记录"""
        result = await db.execute(
            select(FollowupRecord).where(FollowupRecord.followup_id == followup_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_followup(db: AsyncSession, followup: FollowupCreate) -> FollowupRecord:
        """创建随访记录"""
        # 检查患者是否存在
        patient_result = await db.execute(
            select(Patient).where(Patient.patient_id == followup.patient_id)
        )
        if not patient_result.scalar_one_or_none():
            raise ValueError(f"患者 {followup.patient_id} 不存在")

        # 创建随访记录
        db_followup = FollowupRecord(
            **followup.model_dump()
        )

        db.add(db_followup)
        await db.commit()
        await db.refresh(db_followup)

        return db_followup

    @staticmethod
    async def update_followup(
            db: AsyncSession,
            followup_id: UUID,
            followup_update: FollowupUpdate
    ) -> Optional[FollowupRecord]:
        """更新随访记录"""
        result = await db.execute(
            select(FollowupRecord).where(FollowupRecord.followup_id == followup_id)
        )
        db_followup = result.scalar_one_or_none()

        if not db_followup:
            return None

        # 更新非空字段
        update_data = followup_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_followup, field, value)

        await db.commit()
        await db.refresh(db_followup)

        return db_followup

    @staticmethod
    async def delete_followup(db: AsyncSession, followup_id: UUID) -> bool:
        """删除随访记录"""
        result = await db.execute(
            select(FollowupRecord).where(FollowupRecord.followup_id == followup_id)
        )
        db_followup = result.scalar_one_or_none()

        if not db_followup:
            return False

        # 硬删除
        await db.delete(db_followup)
        await db.commit()

        return True

    @staticmethod
    async def complete_followup(
            db: AsyncSession,
            followup_id: UUID,
            completion_note: Optional[str] = None
    ) -> Optional[FollowupRecord]:
        """完成随访"""
        result = await db.execute(
            select(FollowupRecord).where(FollowupRecord.followup_id == followup_id)
        )
        db_followup = result.scalar_one_or_none()

        if not db_followup:
            return None

        if db_followup.is_completed:
            raise ValueError("该随访已完成")

        # 标记为已完成
        db_followup.is_completed = True
        db_followup.completion_note = completion_note
        db_followup.completed_at = datetime.now()

        await db.commit()
        await db.refresh(db_followup)

        return db_followup

    @staticmethod
    async def get_upcoming_followups(
            db: AsyncSession,
            days: int = 7,
            region_code: Optional[str] = None
    ) -> List[FollowupRecord]:
        """获取即将到来的随访"""
        today = date.today()
        end_date = today + timedelta(days=days)

        query = select(FollowupRecord).where(
            FollowupRecord.followup_date >= today,
            FollowupRecord.followup_date <= end_date,
            FollowupRecord.is_completed == False
        )

        # 如果指定了区域，需要关联患者表进行筛选
        if region_code:
            query = query.join(Patient).where(Patient.region_code == region_code)

        query = query.order_by(FollowupRecord.followup_date.asc())

        result = await db.execute(query)
        followups = result.scalars().all()

        return followups

    @staticmethod
    async def get_followup_stats(
            db: AsyncSession,
            region_code: Optional[str] = None,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """获取随访统计信息"""
        # TODO: 实现随访统计逻辑
        return {
            "total_followups": 0,
            "completed_followups": 0,
            "pending_followups": 0,
            "by_type": {},
            "by_region": {},
            "completion_rate": 0.0
        }
