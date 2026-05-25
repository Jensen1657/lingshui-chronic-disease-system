"""
年度评估业务逻辑服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime, timedelta

from app.models import AnnualAssessment, Patient
from app.schemas.assessment import AssessmentCreate, AssessmentUpdate


class AssessmentService:
    """年度评估服务类"""

    @staticmethod
    async def get_assessments(
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100,
            patient_id: Optional[UUID] = None,
            disease_code: Optional[str] = None,
            assessment_year: Optional[int] = None,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None,
            is_completed: Optional[bool] = None
    ) -> tuple[List[AnnualAssessment], int]:
        """
        获取年度评估列表（支持筛选和分页）
        """
        # 构建查询
        query = select(AnnualAssessment)

        # 应用筛选条件
        if patient_id:
            query = query.where(AnnualAssessment.patient_id == patient_id)
        if disease_code:
            query = query.where(AnnualAssessment.disease_code == disease_code)
        if assessment_year:
            query = query.where(AnnualAssessment.assessment_year == assessment_year)
        if start_date:
            query = query.where(AnnualAssessment.assessment_date >= start_date)
        if end_date:
            query = query.where(AnnualAssessment.assessment_date <= end_date)
        if is_completed is not None:
            query = query.where(AnnualAssessment.is_completed == is_completed)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.execute(count_query)
        total = total.scalar_one()

        # 分页
        query = query.offset(skip).limit(limit)

        # 执行查询
        result = await db.execute(query)
        assessments = result.scalars().all()

        return assessments, total

    @staticmethod
    async def get_assessment_by_id(db: AsyncSession, assessment_id: UUID) -> Optional[AnnualAssessment]:
        """根据 ID 获取年度评估记录"""
        result = await db.execute(
            select(AnnualAssessment).where(AnnualAssessment.assessment_id == assessment_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_assessment(db: AsyncSession, assessment: AssessmentCreate) -> AnnualAssessment:
        """创建年度评估记录"""
        # 检查患者是否存在
        patient_result = await db.execute(
            select(Patient).where(Patient.patient_id == assessment.patient_id)
        )
        if not patient_result.scalar_one_or_none():
            raise ValueError(f"患者 {assessment.patient_id} 不存在")

        # 创建年度评估记录
        db_assessment = AnnualAssessment(
            **assessment.model_dump()
        )

        db.add(db_assessment)
        await db.commit()
        await db.refresh(db_assessment)

        return db_assessment

    @staticmethod
    async def update_assessment(
            db: AsyncSession,
            assessment_id: UUID,
            assessment_update: AssessmentUpdate
    ) -> Optional[AnnualAssessment]:
        """更新年度评估记录"""
        result = await db.execute(
            select(AnnualAssessment).where(AnnualAssessment.assessment_id == assessment_id)
        )
        db_assessment = result.scalar_one_or_none()

        if not db_assessment:
            return None

        # 更新非空字段
        update_data = assessment_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_assessment, field, value)

        await db.commit()
        await db.refresh(db_assessment)

        return db_assessment

    @staticmethod
    async def delete_assessment(db: AsyncSession, assessment_id: UUID) -> bool:
        """删除年度评估记录"""
        result = await db.execute(
            select(AnnualAssessment).where(AnnualAssessment.assessment_id == assessment_id)
        )
        db_assessment = result.scalar_one_or_none()

        if not db_assessment:
            return False

        # 硬删除
        await db.delete(db_assessment)
        await db.commit()

        return True

    @staticmethod
    async def complete_assessment(
            db: AsyncSession,
            assessment_id: UUID,
            completion_note: Optional[str] = None
    ) -> Optional[AnnualAssessment]:
        """完成年度评估"""
        result = await db.execute(
            select(AnnualAssessment).where(AnnualAssessment.assessment_id == assessment_id)
        )
        db_assessment = result.scalar_one_or_none()

        if not db_assessment:
            return None

        if db_assessment.is_completed:
            raise ValueError("该年度评估已完成")

        # 标记为已完成
        db_assessment.is_completed = True
        db_assessment.completion_note = completion_note
        db_assessment.completed_at = datetime.now()

        await db.commit()
        await db.refresh(db_assessment)

        return db_assessment

    @staticmethod
    async def generate_annual_tasks(
            db: AsyncSession,
            year: int,
            org_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成年度评估任务
        - 根据患者档案和疾病类型生成年度评估任务
        - 返回生成的任务数和详情
        """
        # TODO: 实现生成年度评估任务的逻辑
        return {
            "generated_count": 0,
            "tasks": []
        }

    @staticmethod
    async def get_assessment_stats(
            db: AsyncSession,
            org_code: Optional[str] = None,
            year: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取年度评估统计信息"""
        # TODO: 实现年度评估统计逻辑
        return {
            "total_assessments": 0,
            "completed_assessments": 0,
            "pending_assessments": 0,
            "by_disease": {},
            "by_org": {},
            "completion_rate": 0.0
        }
