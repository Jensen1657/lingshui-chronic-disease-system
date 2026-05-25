"""
微信绑定业务逻辑服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime

from app.models import PatientWechat, Patient
from app.schemas.wechat import WechatCreate, WechatUpdate


class WechatService:
    """微信绑定服务类"""

    @staticmethod
    async def get_wechat_bindings(
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100,
            patient_id: Optional[UUID] = None,
            openid: Optional[str] = None,
            nickname: Optional[str] = None,
            is_active: Optional[bool] = None,
            bind_date_start: Optional[date] = None,
            bind_date_end: Optional[date] = None
    ) -> tuple[List[PatientWechat], int]:
        """
        获取微信绑定列表（支持筛选和分页）
        """
        # 构建查询
        query = select(PatientWechat)

        # 应用筛选条件
        if patient_id:
            query = query.where(PatientWechat.patient_id == patient_id)
        if openid:
            query = query.where(PatientWechat.openid == openid)
        if nickname:
            query = query.where(PatientWechat.nickname.like(f"%{nickname}%"))
        if is_active is not None:
            query = query.where(PatientWechat.is_active == is_active)
        if bind_date_start:
            query = query.where(PatientWechat.bind_date >= bind_date_start)
        if bind_date_end:
            query = query.where(PatientWechat.bind_date <= bind_date_end)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.execute(count_query)
        total = total.scalar_one()

        # 分页
        query = query.offset(skip).limit(limit)

        # 执行查询
        result = await db.execute(query)
        wechat_bindings = result.scalars().all()

        return wechat_bindings, total

    @staticmethod
    async def get_wechat_by_id(db: AsyncSession, wechat_id: UUID) -> Optional[PatientWechat]:
        """根据 ID 获取微信绑定记录"""
        result = await db.execute(
            select(PatientWechat).where(PatientWechat.wechat_id == wechat_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_wechat_binding(db: AsyncSession, wechat: WechatCreate) -> PatientWechat:
        """创建微信绑定记录"""
        # 检查患者是否存在
        patient_result = await db.execute(
            select(Patient).where(Patient.patient_id == wechat.patient_id)
        )
        if not patient_result.scalar_one_or_none():
            raise ValueError(f"患者 {wechat.patient_id} 不存在")

        # 检查openid是否已绑定
        existing_result = await db.execute(
            select(PatientWechat).where(
                PatientWechat.openid == wechat.openid,
                PatientWechat.is_active == True
            )
        )
        if existing_result.scalar_one_or_none():
            raise ValueError(f"该微信已绑定其他患者")

        # 检查患者是否已有活跃绑定
        patient_wechat_result = await db.execute(
            select(PatientWechat).where(
                PatientWechat.patient_id == wechat.patient_id,
                PatientWechat.is_active == True
            )
        )
        if patient_wechat_result.scalar_one_or_none():
            raise ValueError(f"该患者已有活跃的微信绑定")

        # 创建微信绑定记录
        db_wechat = PatientWechat(
            **wechat.model_dump()
        )

        db.add(db_wechat)
        await db.commit()
        await db.refresh(db_wechat)

        return db_wechat

    @staticmethod
    async def update_wechat_binding(
            db: AsyncSession,
            wechat_id: UUID,
            wechat_update: WechatUpdate
    ) -> Optional[PatientWechat]:
        """更新微信绑定记录"""
        result = await db.execute(
            select(PatientWechat).where(PatientWechat.wechat_id == wechat_id)
        )
        db_wechat = result.scalar_one_or_none()

        if not db_wechat:
            return None

        # 更新非空字段
        update_data = wechat_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_wechat, field, value)

        await db.commit()
        await db.refresh(db_wechat)

        return db_wechat

    @staticmethod
    async def delete_wechat_binding(db: AsyncSession, wechat_id: UUID) -> bool:
        """删除微信绑定记录"""
        result = await db.execute(
            select(PatientWechat).where(PatientWechat.wechat_id == wechat_id)
        )
        db_wechat = result.scalar_one_or_none()

        if not db_wechat:
            return False

        # 软删除（标记为不活跃）
        db_wechat.is_active = False
        db_wechat.unbind_date = date.today()

        await db.commit()

        return True

    @staticmethod
    async def unbind_wechat(
            db: AsyncSession,
            wechat_id: UUID
    ) -> Optional[PatientWechat]:
        """解绑微信"""
        result = await db.execute(
            select(PatientWechat).where(PatientWechat.wechat_id == wechat_id)
        )
        db_wechat = result.scalar_one_or_none()

        if not db_wechat:
            return None

        if not db_wechat.is_active:
            raise ValueError("该微信已解绑")

        # 标记为不活跃
        db_wechat.is_active = False
        db_wechat.unbind_date = date.today()

        await db.commit()
        await db.refresh(db_wechat)

        return db_wechat

    @staticmethod
    async def get_active_wechat_binding(
            db: AsyncSession,
            patient_id: UUID
    ) -> Optional[PatientWechat]:
        """获取患者活跃的微信绑定记录"""
        result = await db.execute(
            select(PatientWechat).where(
                PatientWechat.patient_id == patient_id,
                PatientWechat.is_active == True
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_wechat_by_openid(
            db: AsyncSession,
            openid: str
    ) -> Optional[PatientWechat]:
        """根据 openid 获取微信绑定记录"""
        result = await db.execute(
            select(PatientWechat).where(PatientWechat.openid == openid)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_wechat_stats(
            db: AsyncSession,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """获取微信绑定统计信息"""
        # TODO: 实现微信绑定统计逻辑
        return {
            "total_bindings": 0,
            "active_bindings": 0,
            "inactive_bindings": 0,
            "by_month": {},
            "avg_bindings_per_month": 0.0
        }
