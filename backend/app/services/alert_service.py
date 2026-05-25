"""
预警业务逻辑服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime, timedelta

from app.models import AlertRecord, Patient, SysUser
from app.schemas.alert import AlertCreate, AlertUpdate


class AlertService:
    """预警服务类"""

    @staticmethod
    async def get_alerts(
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100,
            patient_id: Optional[UUID] = None,
            alert_type: Optional[str] = None,
            is_processed: Optional[bool] = None,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None
    ) -> tuple[List[AlertRecord], int]:
        """
        获取预警列表（支持筛选和分页）
        """
        # 构建查询
        query = select(AlertRecord)

        # 应用筛选条件
        if patient_id:
            query = query.where(AlertRecord.patient_id == patient_id)
        if alert_type:
            query = query.where(AlertRecord.alert_type == alert_type)
        if is_processed is not None:
            query = query.where(AlertRecord.is_processed == is_processed)
        if start_date:
            query = query.where(AlertRecord.alert_time >= start_date)
        if end_date:
            query = query.where(AlertRecord.alert_time <= end_date)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.execute(count_query)
        total = total.scalar_one()

        # 分页
        query = query.offset(skip).limit(limit)

        # 执行查询
        result = await db.execute(query)
        alerts = result.scalars().all()

        return alerts, total

    @staticmethod
    async def get_alert_by_id(db: AsyncSession, alert_id: UUID) -> Optional[AlertRecord]:
        """根据 ID 获取预警记录"""
        result = await db.execute(
            select(AlertRecord).where(AlertRecord.alert_id == alert_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_alert(db: AsyncSession, alert: AlertCreate) -> AlertRecord:
        """创建预警记录"""
        # 检查患者是否存在
        patient_result = await db.execute(
            select(Patient).where(Patient.patient_id == alert.patient_id)
        )
        if not patient_result.scalar_one_or_none():
            raise ValueError(f"患者 {alert.patient_id} 不存在")

        # 创建预警记录
        db_alert = AlertRecord(
            **alert.model_dump()
        )

        db.add(db_alert)
        await db.commit()
        await db.refresh(db_alert)

        return db_alert

    @staticmethod
    async def update_alert(
            db: AsyncSession,
            alert_id: UUID,
            alert_update: AlertUpdate
    ) -> Optional[AlertRecord]:
        """更新预警记录"""
        result = await db.execute(
            select(AlertRecord).where(AlertRecord.alert_id == alert_id)
        )
        db_alert = result.scalar_one_or_none()

        if not db_alert:
            return None

        # 更新非空字段
        update_data = alert_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_alert, field, value)

        await db.commit()
        await db.refresh(db_alert)

        return db_alert

    @staticmethod
    async def delete_alert(db: AsyncSession, alert_id: UUID) -> bool:
        """删除预警记录"""
        result = await db.execute(
            select(AlertRecord).where(AlertRecord.alert_id == alert_id)
        )
        db_alert = result.scalar_one_or_none()

        if not db_alert:
            return False

        # 硬删除
        await db.delete(db_alert)
        await db.commit()

        return True

    @staticmethod
    async def process_alert(
            db: AsyncSession,
            alert_id: UUID,
            current_user: SysUser,
            process_note: Optional[str] = None
    ) -> Optional[AlertRecord]:
        """处理预警"""
        result = await db.execute(
            select(AlertRecord).where(AlertRecord.alert_id == alert_id)
        )
        db_alert = result.scalar_one_or_none()

        if not db_alert:
            return None

        if db_alert.is_handled:
            raise ValueError("该预警已处理")

        # 标记为已处理
        db_alert.is_handled = True
        db_alert.handled_by = current_user.username  # 从 JWT token 获取当前用户
        db_alert.handled_at = datetime.now()
        db_alert.handle_note = process_note

        await db.commit()
        await db.refresh(db_alert)

        return db_alert

    @staticmethod
    async def get_alert_stats(
            db: AsyncSession,
            org_code: Optional[str] = None,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """获取预警统计信息"""
        # TODO: 实现预警统计逻辑
        return {
            "total_alerts": 0,
            "processed_alerts": 0,
            "unprocessed_alerts": 0,
            "by_type": {},
            "by_org": {},
            "processing_rate": 0.0
        }

    @staticmethod
    async def get_unprocessed_alerts(
            db: AsyncSession,
            days: int = 7,
            org_code: Optional[str] = None
    ) -> List[AlertRecord]:
        """获取未处理的预警（紧急）"""
        cutoff_time = datetime.now() - timedelta(days=days)

        query = select(AlertRecord).where(
            AlertRecord.is_processed == False,
            AlertRecord.alert_time >= cutoff_time
        )

        # 如果指定了机构，需要关联患者表进行筛选
        if org_code:
            query = query.join(Patient).where(Patient.region_code == org_code)

        query = query.order_by(AlertRecord.alert_time.asc())

        result = await db.execute(query)
        alerts = result.scalars().all()

        return alerts
