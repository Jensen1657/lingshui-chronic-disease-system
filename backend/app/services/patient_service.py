"""
患者业务逻辑服务（集成数据加密）
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.models import Patient, RegionCode, DiseaseType
from app.schemas.patient import PatientCreate, PatientUpdate
from app.services.encryption_service import get_encryption_service


class PatientService:
    """患者服务类"""

    @staticmethod
    async def get_patients(
            db: AsyncSession,
            skip: int = 0,
            limit: int = 100,
            name: Optional[str] = None,
            id_card: Optional[str] = None,
            region_code: Optional[str] = None,
            disease_code: Optional[str] = None,
            risk_level: Optional[str] = None,
            is_active: Optional[bool] = None
    ) -> tuple[List[Patient], int]:
        """
        获取患者列表（支持筛选和分页）
        注意：加密字段无法直接筛选，需在应用层处理
        """
        # 构建查询
        query = select(Patient)

        # 应用筛选条件（加密字段无法在数据库层筛选）
        if region_code:
            query = query.where(Patient.village_code == region_code)
        if risk_level:
            query = query.where(Patient.risk_level == risk_level)
        if is_active is not None:
            query = query.where(Patient.is_active == is_active)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.execute(count_query)
        total = total.scalar_one()

        # 分页
        query = query.offset(skip).limit(limit)

        # 执行查询
        result = await db.execute(query)
        patients = result.scalars().all()

        # 解密敏感字段（供返回使用）
        encryption_service = get_encryption_service()
        for patient in patients:
            try:
                if patient.name_enc:
                    patient._decrypted_name = encryption_service.decrypt(patient.name_enc)
            except Exception:
                patient._decrypted_name = '[解密失败]'
            try:
                if patient.id_card_enc:
                    patient._decrypted_id_card = encryption_service.decrypt(patient.id_card_enc)
            except Exception:
                patient._decrypted_id_card = '[解密失败]'

        return patients, total

    @staticmethod
    async def get_patient_by_id(db: AsyncSession, patient_id: UUID) -> Optional[Patient]:
        """根据 ID 获取患者（自动解密敏感字段）"""
        result = await db.execute(
            select(Patient).where(Patient.patient_id == patient_id)
        )
        patient = result.scalar_one_or_none()
        
        if patient:
            # 解密敏感字段
            encryption_service = get_encryption_service()
            try:
                if patient.name_enc:
                    patient._decrypted_name = encryption_service.decrypt(patient.name_enc)
            except Exception:
                patient._decrypted_name = '[解密失败]'
            try:
                if patient.id_card_enc:
                    patient._decrypted_id_card = encryption_service.decrypt(patient.id_card_enc)
            except Exception:
                patient._decrypted_id_card = '[解密失败]'
            try:
                if patient.phone_enc:
                    patient._decrypted_phone = encryption_service.decrypt(patient.phone_enc)
            except Exception:
                patient._decrypted_phone = '[解密失败]'
        
        return patient

    @staticmethod
    async def create_patient(db: AsyncSession, patient: PatientCreate) -> Patient:
        """创建患者（自动加密敏感字段）"""
        # 获取加密服务
        encryption_service = get_encryption_service()
        
        # 检查身份证号哈希是否已存在
        import hashlib
        id_card_hash = hashlib.sha256(patient.id_card.encode()).hexdigest()
        existing = await db.execute(
            select(Patient).where(Patient.id_card_hash == id_card_hash)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"身份证号已存在")

        # 检查区域编码是否存在
        region_result = await db.execute(
            select(RegionCode).where(RegionCode.code == patient.region_code)
        )
        if not region_result.scalar_one_or_none():
            raise ValueError(f"区域编码 {patient.region_code} 不存在")

        # 加密敏感字段
        name_enc = encryption_service.encrypt(patient.name)
        id_card_enc = encryption_service.encrypt(patient.id_card)
        phone_enc = encryption_service.encrypt(patient.phone) if patient.phone else None

        # 计算身份证哈希（用于唯一性检查）
        import hashlib
        id_card_hash = hashlib.sha256(patient.id_card.encode()).hexdigest()

        # 创建患者
        db_patient = Patient(
            patient_id=patient.patient_id if hasattr(patient, 'patient_id') and patient.patient_id else None,
            name_enc=name_enc,
            id_card_enc=id_card_enc,
            id_card_hash=id_card_hash,
            phone_enc=phone_enc,
            gender=patient.gender,
            birth_date=patient.birth_date,
            region_code=patient.region_code,
            village_code=getattr(patient, 'village_code', None),
            disease_list=patient.disease_list if hasattr(patient, 'disease_list') else None,
            risk_level=getattr(patient, 'risk_level', None),
            manage_group=getattr(patient, 'manage_group', None),
            establish_date=getattr(patient, 'establish_date', None),
            is_active=True,
        )

        db.add(db_patient)
        await db.commit()
        await db.refresh(db_patient)

        return db_patient

    @staticmethod
    async def update_patient(
            db: AsyncSession,
            patient_id: UUID,
            patient_update: PatientUpdate
    ) -> Optional[Patient]:
        """更新患者信息（自动加密敏感字段）"""
        result = await db.execute(
            select(Patient).where(Patient.patient_id == patient_id)
        )
        db_patient = result.scalar_one_or_none()

        if not db_patient:
            return None

        # 获取加密服务
        encryption_service = get_encryption_service()

        # 更新非空字段
        update_data = patient_update.model_dump(exclude_unset=True)
        
        # 对敏感字段进行加密
        sensitive_fields = ['id_card', 'name', 'phone']
        encrypted_fields = encryption_service.encrypt_dict(update_data, sensitive_fields)
        
        for field, value in encrypted_fields.items():
            setattr(db_patient, field + '_enc', value)
        
        # 如果更新了 id_card，重新计算哈希
        if 'id_card' in update_data:
            db_patient.id_card_hash = encryption_service.encrypt(update_data['id_card'])

        await db.commit()
        await db.refresh(db_patient)

        return db_patient

    @staticmethod
    async def delete_patient(db: AsyncSession, patient_id: UUID) -> bool:
        """删除患者（软删除）"""
        result = await db.execute(
            select(Patient).where(Patient.patient_id == patient_id)
        )
        db_patient = result.scalar_one_or_none()

        if not db_patient:
            return False

        # 软删除
        db_patient.is_active = False
        await db.commit()

        return True

    @staticmethod
    async def get_patient_stats(db: AsyncSession, region_code: Optional[str] = None) -> dict:
        """获取患者统计信息"""
        # TODO: 实现患者统计逻辑
        return {
            "total_patients": 0,
            "active_patients": 0,
            "by_disease": {},
            "by_region": {},
            "by_risk_level": {}
        }
