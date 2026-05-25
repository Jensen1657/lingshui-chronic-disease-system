"""
中医管理业务逻辑服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime, timedelta

from app.models import TcmRecord, Patient
from app.schemas.tcm import TcmCreate, TcmUpdate


class TcmService:
    """中医管理服务类"""

    @staticmethod
    async def get_tcm_records(
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100,
            patient_id: Optional[UUID] = None,
            tcm_type: Optional[str] = None,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None
    ) -> tuple[List[TcmRecord], int]:
        """
        获取中医管理记录列表（支持筛选和分页）
        """
        # 构建查询
        query = select(TcmRecord)

        # 应用筛选条件
        if patient_id:
            query = query.where(TcmRecord.patient_id == patient_id)
        if tcm_type:
            query = query.where(TcmRecord.tcm_type == tcm_type)
        if start_date:
            query = query.where(TcmRecord.record_date >= start_date)
        if end_date:
            query = query.where(TcmRecord.record_date <= end_date)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.execute(count_query)
        total = total.scalar_one()

        # 分页
        query = query.offset(skip).limit(limit)

        # 执行查询
        result = await db.execute(query)
        records = result.scalars().all()

        return records, total

    @staticmethod
    async def get_tcm_by_id(db: AsyncSession, tcm_id: UUID) -> Optional[TcmRecord]:
        """根据 ID 获取中医管理记录"""
        result = await db.execute(
            select(TcmRecord).where(TcmRecord.tcm_id == tcm_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_tcm_record(db: AsyncSession, tcm: TcmCreate) -> TcmRecord:
        """创建中医管理记录"""
        # 检查患者是否存在
        patient_result = await db.execute(
            select(Patient).where(Patient.patient_id == tcm.patient_id)
        )
        if not patient_result.scalar_one_or_none():
            raise ValueError(f"患者 {tcm.patient_id} 不存在")

        # 创建中医管理记录
        db_tcm = TcmRecord(
            **tcm.model_dump()
        )

        db.add(db_tcm)
        await db.commit()
        await db.refresh(db_tcm)

        return db_tcm

    @staticmethod
    async def update_tcm_record(
            db: AsyncSession,
            tcm_id: UUID,
            tcm_update: TcmUpdate
    ) -> Optional[TcmRecord]:
        """更新中医管理记录"""
        result = await db.execute(
            select(TcmRecord).where(TcmRecord.tcm_id == tcm_id)
        )
        db_tcm = result.scalar_one_or_none()

        if not db_tcm:
            return None

        # 更新非空字段
        update_data = tcm_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_tcm, field, value)

        await db.commit()
        await db.refresh(db_tcm)

        return db_tcm

    @staticmethod
    async def delete_tcm_record(db: AsyncSession, tcm_id: UUID) -> bool:
        """删除中医管理记录"""
        result = await db.execute(
            select(TcmRecord).where(TcmRecord.tcm_id == tcm_id)
        )
        db_tcm = result.scalar_one_or_none()

        if not db_tcm:
            return False

        # 硬删除
        await db.delete(db_tcm)
        await db.commit()

        return True

    @staticmethod
    async def get_tcm_stats(
            db: AsyncSession,
            org_code: Optional[str] = None,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """获取中医管理统计信息"""
        # TODO: 实现中医管理统计逻辑
        return {
            "total_records": 0,
            "by_type": {},
            "by_org": {},
            "avg_per_patient": 0.0
        }
