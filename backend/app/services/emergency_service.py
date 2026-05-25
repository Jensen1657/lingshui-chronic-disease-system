"""
急救联动业务逻辑服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime, timedelta

from app.models import EmergencyAlert, Patient, SysUser
from app.schemas.emergency import EmergencyAlertCreate, EmergencyAlertUpdate


class EmergencyService:
    """急救联动服务类"""

    @staticmethod
    async def get_emergencies(
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100,
            patient_id: Optional[UUID] = None,
            status: Optional[str] = None,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None
    ) -> tuple[List[EmergencyAlert], int]:
        """
        获取急救联动列表（支持筛选和分页）
        """
        # 构建查询
        query = select(EmergencyAlert)

        # 应用筛选条件
        if patient_id:
            query = query.where(EmergencyAlert.patient_id == patient_id)
        if status:
            query = query.where(EmergencyAlert.status == status)
        if start_date:
            query = query.where(EmergencyAlert.alert_time >= start_date)
        if end_date:
            query = query.where(EmergencyAlert.alert_time <= end_date)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.execute(count_query)
        total = total.scalar_one()

        # 分页
        query = query.offset(skip).limit(limit)

        # 执行查询
        result = await db.execute(query)
        emergencies = result.scalars().all()

        return emergencies, total

    @staticmethod
    async def get_emergency_by_id(db: AsyncSession, emergency_id: UUID) -> Optional[EmergencyAlert]:
        """根据 ID 获取急救联动记录"""
        result = await db.execute(
            select(EmergencyAlert).where(EmergencyAlert.emergency_id == emergency_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_emergency(db: AsyncSession, emergency: EmergencyAlertCreate) -> EmergencyAlert:
        """创建急救联动记录"""
        # 检查患者是否存在
        patient_result = await db.execute(
            select(Patient).where(Patient.patient_id == emergency.patient_id)
        )
        if not patient_result.scalar_one_or_none():
            raise ValueError(f"患者 {emergency.patient_id} 不存在")

        # 创建急救联动记录
        db_emergency = EmergencyAlert(
            **emergency.model_dump()
        )

        db.add(db_emergency)
        await db.commit()
        await db.refresh(db_emergency)

        return db_emergency

    @staticmethod
    async def update_emergency(
            db: AsyncSession,
            emergency_id: UUID,
            emergency_update: EmergencyAlertUpdate
    ) -> Optional[EmergencyAlert]:
        """更新急救联动记录"""
        result = await db.execute(
            select(EmergencyAlert).where(EmergencyAlert.emergency_id == emergency_id)
        )
        db_emergency = result.scalar_one_or_none()

        if not db_emergency:
            return None

        # 更新非空字段
        update_data = emergency_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_emergency, field, value)

        await db.commit()
        await db.refresh(db_emergency)

        return db_emergency

    @staticmethod
    async def delete_emergency(db: AsyncSession, emergency_id: UUID) -> bool:
        """删除急救联动记录"""
        result = await db.execute(
            select(EmergencyAlert).where(EmergencyAlert.emergency_id == emergency_id)
        )
        db_emergency = result.scalar_one_or_none()

        if not db_emergency:
            return False

        # 硬删除
        await db.delete(db_emergency)
        await db.commit()

        return True

    @staticmethod
    async def process_emergency(
            db: AsyncSession,
            emergency_id: UUID,
            current_user: SysUser,
            process_note: Optional[str] = None
    ) -> Optional[EmergencyAlert]:
        """处理急救联动"""
        result = await db.execute(
            select(EmergencyAlert).where(EmergencyAlert.emergency_id == emergency_id)
        )
        db_emergency = result.scalar_one_or_none()

        if not db_emergency:
            return None

        if db_emergency.status == "PROCESSED":
            raise ValueError("该急救联动已处理")

        # 标记为已处理
        db_emergency.status = "PROCESSED"
        db_emergency.processed_by = current_user.username  # 从 JWT token 获取当前用户
        db_emergency.processed_at = datetime.now()
        db_emergency.process_note = process_note

        await db.commit()
        await db.refresh(db_emergency)

        return db_emergency

    @staticmethod
    async def get_emergency_stats(
            db: AsyncSession,
            org_code: Optional[str] = None,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """获取急救联动统计信息"""
        # TODO: 实现急救联动统计逻辑
        return {
            "total_emergencies": 0,
            "processed_emergencies": 0,
            "pending_emergencies": 0,
            "by_type": {},
            "by_org": {},
            "processing_rate": 0.0
        }

    @staticmethod
    async def get_active_emergencies(
            db: AsyncSession,
            hours: int = 24,
            org_code: Optional[str] = None
    ) -> List[EmergencyAlert]:
        """获取活跃急救联动（未处理）"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        query = select(EmergencyAlert).where(
            EmergencyAlert.status == "PENDING",
            EmergencyAlert.alert_time >= cutoff_time
        )

        # 如果指定了机构，需要关联患者表进行筛选
        if org_code:
            query = query.join(Patient).where(Patient.region_code == org_code)

        query = query.order_by(EmergencyAlert.alert_time.asc())

        result = await db.execute(query)
        emergencies = result.scalars().all()

        return emergencies
