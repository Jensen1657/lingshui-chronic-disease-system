"""患者管理路由 - CRUD 操作"""
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.db.session import get_db
from app.models import Patient  # 从 models/__init__.py 导入
from app.schemas.patient import (
    PatientCreate, PatientUpdate, PatientResponse,
    PatientSearchParams, PatientDiseaseSummary, PatientStats,
    PatientPaginatedResponse
)
from app.dependencies.auth import get_current_active_user, require_roles
from app.services.encryption_service import get_encryption_service
from app.utils.constants import enc, ORG_NAME_MAP, DISEASE_NAME_MAP, decrypt_patient_name, decrypt_patient_phone, get_org_name
from app.utils.cache import get as cache_get, set as cache_set, invalidate, invalidate_pattern, DASHBOARD_STATS_KEY, DASHBOARD_KPI_KEY

router = APIRouter()


@router.post("")
@router.post("/", response_model=PatientResponse, status_code=201, dependencies=[Depends(require_roles('ADMIN', 'DOCTOR', 'NURSE'))])
async def create_patient(
        patient: PatientCreate,
        db: AsyncSession = Depends(get_db)
):
    """
    创建新患者
    - 接收明文数据，自动加密敏感字段
    - 检查身份证哈希是否已存在
    """
    encryption_service = enc
    
    # 计算身份证哈希（用于去重）
    import hashlib
    id_card_hash = hashlib.sha256(patient.id_card.encode()).hexdigest()
    
    # 检查身份证哈希是否已存在
    result = await db.execute(
        select(Patient).where(Patient.id_card_hash == id_card_hash)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该患者已存在（身份证号重复）")

    # 加密敏感字段
    name_enc = enc.encrypt(patient.name)
    id_card_enc = enc.encrypt(patient.id_card)
    phone_enc = enc.encrypt(patient.phone) if patient.phone else None

    # 创建新患者
    db_patient = Patient(
        id_card_enc=id_card_enc,
        id_card_hash=id_card_hash,
        name_enc=name_enc,
        gender=patient.gender,
        birth_date=patient.birth_date,
        age=calculate_age(patient.birth_date),
        phone_enc=phone_enc,
        address=patient.address,
        village_code=patient.village_code,
        manage_org_code=patient.manage_org_code,
        disease_list=patient.disease_list,
        risk_level="LOW",
        is_active=True,
        empi_status="ACTIVE"
    )

    db.add(db_patient)
    await db.commit()
    await db.refresh(db_patient)

    # 清除仪表盘缓存
    invalidate(DASHBOARD_STATS_KEY)

    return db_patient


@router.get("")
@router.get("/", response_model=PatientPaginatedResponse, dependencies=[Depends(require_roles('ADMIN', 'DOCTOR', 'NURSE'))])
async def list_patients(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        search: Optional[str] = Query(None, description="搜索关键词（姓名/身份证号/手机号）"),
        village_code: Optional[str] = Query(None),
        manage_org_code: Optional[str] = Query(None),
        disease_code: Optional[str] = Query(None),
        risk_level: Optional[str] = Query(None),
        is_active: Optional[bool] = Query(True),
        min_age: Optional[int] = Query(None, ge=0),
        max_age: Optional[int] = Query(None, ge=0),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_active_user)
):
    """
    查询患者列表（支持分页和多条件筛选）
    数据权限：根据用户机构层级自动过滤，上级可查看下级数据
    注意：search 参数由于加密存储，需要在应用层解密后过滤
    对于大数据量，建议使用专门的搜索引擎（如 Elasticsearch）
    """
    # 构建基础查询
    base_query = select(Patient)
    
    # ===== 数据权限：机构层级过滤 =====
    from app.utils.data_permission import build_org_filter
    _org_filter = build_org_filter(Patient.manage_org_code, current_user)
    if _org_filter is not None:
        base_query = base_query.where(_org_filter)

    # 应用筛选条件（数据库层面）
    if village_code:
        base_query = base_query.where(Patient.village_code == village_code)
    if manage_org_code:
        base_query = base_query.where(Patient.manage_org_code == manage_org_code)
    if disease_code:
        # disease_list 是 PostgreSQL ARRAY 类型，使用 ANY
        base_query = base_query.where(Patient.disease_list.any(disease_code))
    if risk_level:
        base_query = base_query.where(Patient.risk_level == risk_level)
    if is_active is not None:
        base_query = base_query.where(Patient.is_active == is_active)
    if min_age is not None:
        base_query = base_query.where(Patient.age >= min_age)
    if max_age is not None:
        base_query = base_query.where(Patient.age <= max_age)

    # 执行查询
    result = await db.execute(base_query)
    patients = result.scalars().all()

    # 如果有关键词搜索，需要在应用层解密后过滤
    if search:
        encryption_service = enc
        search_lower = search.lower()
        filtered_patients = []
        
        for patient in patients:
            # 解密敏感字段并搜索
            try:
                name = enc.decrypt(patient.name_enc) if patient.name_enc else ""
                id_card = enc.decrypt(patient.id_card_enc) if patient.id_card_enc else ""
                phone = enc.decrypt(patient.phone_enc) if patient.phone_enc else ""
                
                # 检查是否匹配搜索关键词
                if (search_lower in name.lower() or 
                    search_lower in id_card or 
                    search_lower in phone):
                    filtered_patients.append(patient)
            except Exception as e:
                # 解密失败，跳过该患者
                continue
        
        patients = filtered_patients

    # 计算总数
    total = len(patients)

    # 分页
    paginated_patients = patients[skip:skip + limit]

    # 计算页码
    page = (skip // limit) + 1 if limit > 0 else 1

    # 解密敏感字段后返回（使用共享加密服务单例）
    result_items = []
    for p in paginated_patients:
        pdict = {
            'patient_id': p.patient_id,
            'id_card_hash': p.id_card_hash,
            'name': enc.decrypt(p.name_enc) if p.name_enc else '',
            'gender': p.gender,
            'birth_date': p.birth_date,
            'age': p.age,
            'phone': enc.decrypt(p.phone_enc) if p.phone_enc else '',
            'address': p.address,
            'village_code': p.village_code,
            'manage_org_code': p.manage_org_code,
            'manage_org_name': ORG_NAME_MAP.get(p.manage_org_code, p.manage_org_code or '-') if p.manage_org_code else '-',
            'disease_list': p.disease_list or [],
            'disease_names': [DISEASE_NAME_MAP.get(d.upper(), d) for d in (json.loads(p.disease_list) if isinstance(p.disease_list, str) else (p.disease_list or []))],
            'risk_level': p.risk_level,
            'is_active': p.is_active,
            'empi_status': p.empi_status,
            'created_at': p.created_at,
            'updated_at': p.updated_at,
        }
        result_items.append(pdict)

    return PatientPaginatedResponse(
        items=result_items,
        total=total,
        page=page,
        page_size=limit
    )


@router.get("/export")
async def export_patients(
        village_code: Optional[str] = Query(None),
        manage_org_code: Optional[str] = Query(None),
        disease_code: Optional[str] = Query(None),
        risk_level: Optional[str] = Query(None),
        is_active: Optional[bool] = Query(True),
        min_age: Optional[int] = Query(None, ge=0),
        max_age: Optional[int] = Query(None, ge=0),
        search: Optional[str] = Query(None, description="搜索关键词（姓名/身份证号/手机号）"),
        _=Depends(require_roles('ADMIN', 'DOCTOR', 'NURSE')),
        db: AsyncSession = Depends(get_db)
):
    """
    导出患者列表（CSV格式）
    """
    from datetime import datetime
    
    # 构建基础查询（复用 list_patients 的逻辑）
    base_query = select(Patient)

    # 应用筛选条件
    if village_code:
        base_query = base_query.where(Patient.village_code == village_code)
    if manage_org_code:
        base_query = base_query.where(Patient.manage_org_code == manage_org_code)
    if disease_code:
        base_query = base_query.where(Patient.disease_list.any(disease_code))
    if risk_level:
        base_query = base_query.where(Patient.risk_level == risk_level)
    if is_active is not None:
        base_query = base_query.where(Patient.is_active == is_active)
    if min_age is not None:
        base_query = base_query.where(Patient.age >= min_age)
    if max_age is not None:
        base_query = base_query.where(Patient.age <= max_age)

    # 执行查询
    result = await db.execute(base_query)
    patients = result.scalars().all()

    # 如果有关键词搜索，需要在应用层解密后过滤
    if search:
        encryption_service = enc
        search_lower = search.lower()
        filtered_patients = []
        
        for patient in patients:
            try:
                name = enc.decrypt(patient.name_enc) if patient.name_enc else ""
                id_card = enc.decrypt(patient.id_card_enc) if patient.id_card_enc else ""
                phone = enc.decrypt(patient.phone_enc) if patient.phone_enc else ""
                
                if (search_lower in name.lower() or 
                    search_lower in id_card or 
                    search_lower in phone):
                    filtered_patients.append(patient)
            except Exception as e:
                continue
        
        patients = filtered_patients

    # 获取加密服务
    encryption_service = enc

    # 生成 CSV
    csv_lines = [
        "患者ID,姓名,性别,年龄,身份证号,手机号,地址,行政村,管理机构,疾病列表,风险等级,状态,创建时间"
    ]
    
    for patient in patients:
        # 解密敏感字段
        name = ""
        id_card = ""
        phone = ""
        try:
            if patient.name_enc:
                name = enc.decrypt(patient.name_enc)
        except:
            name = "[解密失败]"
        
        try:
            if patient.id_card_enc:
                id_card = enc.decrypt(patient.id_card_enc)
        except:
            id_card = "[解密失败]"
        
        try:
            if patient.phone_enc:
                phone = enc.decrypt(patient.phone_enc)
        except:
            phone = "[解密失败]"
        
        # 处理疾病列表
        disease_list = ",".join(patient.disease_list) if patient.disease_list else ""
        
        # 处理状态
        status = "活跃" if patient.is_active else "停用"
        
        gender_text = "男" if patient.gender == "M" else "女"
        
        # 构建 CSV 行（正确处理 CSV 转义）
        csv_row = ",".join([
            patient.patient_id or "",
            f'"{name}"' if ',' in name or '"' in name else name,
            gender_text,
            str(patient.age or ""),
            f'"{id_card}"' if ',' in id_card or '"' in id_card else id_card,
            phone or "",
            f'"{patient.address or ""}"' if patient.address and (',' in patient.address or '"' in patient.address) else (patient.address or ""),
            patient.village_code or "",
            patient.manage_org_code or "",
            disease_list,
            patient.risk_level or "",
            status,
            str(patient.created_at or "")
        ])
        csv_lines.append(csv_row)

    return {
        "reportText": "\n".join(csv_lines),
        "format": "csv",
        "totalRecords": len(patients),
        "exportTime": datetime.now().isoformat()
    }


@router.get("/{patient_id}", response_model=PatientResponse, dependencies=[Depends(require_roles('ADMIN', 'DOCTOR', 'NURSE'))])
async def get_patient(
        patient_id: str,
        db: AsyncSession = Depends(get_db)
):
    """
    根据 ID 获取患者详情（带缓存）
    """
    # 检查缓存
    cache_key = f"patient:{patient_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return PatientResponse(**cached)
    
    result = await db.execute(
        select(Patient).where(Patient.patient_id == patient_id)
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # 解密敏感字段
    encryption_service = enc
    decrypted_data = decrypt_patient_data(patient, encryption_service)

    # 缓存结果（60秒）
    cache_set(cache_key, decrypted_data, ttl=60)

    return PatientResponse(**decrypted_data)


@router.put("/{patient_id}", response_model=PatientResponse, dependencies=[Depends(require_roles('ADMIN', 'DOCTOR', 'NURSE'))])
async def update_patient(
        patient_id: str,
        patient_update: PatientUpdate,
        db: AsyncSession = Depends(get_db)
):
    """
    更新患者信息
    """
    result = await db.execute(
        select(Patient).where(Patient.patient_id == patient_id)
    )
    db_patient = result.scalar_one_or_none()

    if not db_patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # 获取加密服务
    encryption_service = enc

    # 更新非空字段
    update_data = patient_update.model_dump(exclude_unset=True)
    
    # 对敏感字段进行加密
    update_data = encrypt_patient_data(update_data, encryption_service)
    
    for field, value in update_data.items():
        setattr(db_patient, field, value)

    # 如果更新了生日，重新计算年龄
    if 'birth_date' in update_data:
        db_patient.age = calculate_age(db_patient.birth_date)

    await db.commit()
    await db.refresh(db_patient)

    # 清除相关缓存
    invalidate(DASHBOARD_STATS_KEY)
    invalidate(f"patient:{patient_id}")
    invalidate_pattern("patient:stats:*")  # 统计信息已变更

    # 解密后返回
    decrypted_data = decrypt_patient_data(db_patient, encryption_service)
    return PatientResponse(**decrypted_data)


@router.delete("/{patient_id}", dependencies=[Depends(require_roles('ADMIN'))])
async def deactivate_patient(
        patient_id: str,
        db: AsyncSession = Depends(get_db)
):
    """
    停用患者（软删除）
    """
    result = await db.execute(
        select(Patient).where(Patient.patient_id == patient_id)
    )
    db_patient = result.scalar_one_or_none()

    if not db_patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    db_patient.is_active = False
    db_patient.empi_status = "INACTIVE"

    await db.commit()

    # 清除相关缓存
    invalidate(DASHBOARD_STATS_KEY)
    invalidate(f"patient:{patient_id}")
    invalidate_pattern("patient:stats:*")  # 统计信息已变更

    return {"message": "患者已停用"}


@router.get("/stats/summary", response_model=PatientStats)
async def get_patient_stats(
        manage_org_code: Optional[str] = Query(None),
        db: AsyncSession = Depends(get_db)
):
    """
    获取患者统计信息（优化版 - 合并查询，减少数据库往返）
    """
    # 检查缓存
    cache_key = f"patient:stats:{manage_org_code or 'all'}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    
    from sqlalchemy import literal_column, union_all
    
    # 构建基础查询条件
    base_filter = [Patient.is_active == True]
    if manage_org_code:
        base_filter.append(Patient.manage_org_code == manage_org_code)
    
    # ===== 优化：使用 UNION ALL 合并分组查询 =====
    # 查询 1：总数（单独查询，因为不需要 GROUP BY）
    total_result = await db.execute(
        select(func.count(Patient.patient_id)).where(and_(*base_filter))
    )
    total_patients = total_result.scalar() or 0
    active_patients = total_patients
    
    # 查询 2：使用 UNION ALL 合并 risk_level 和 village_code 分组查询
    grouped_query = (
        select(
            literal_column("'risk'").label('group_type'),
            Patient.risk_level.label('group_key'),
            func.count(Patient.patient_id).label('count')
        )
        .where(and_(*base_filter))
        .where(Patient.risk_level.isnot(None))
        .group_by(Patient.risk_level)
    ).union_all(
        select(
            literal_column("'village'").label('group_type'),
            Patient.village_code.label('group_key'),
            func.count(Patient.patient_id).label('count')
        )
        .where(and_(*base_filter))
        .where(Patient.village_code.isnot(None))
        .group_by(Patient.village_code)
    )
    
    grouped_result = await db.execute(grouped_query)
    
    # 解析分组结果
    by_risk_level = {}
    by_village = {}
    for row in grouped_result:
        if row.group_type == 'risk':
            by_risk_level[row.group_key] = row.count
        elif row.group_type == 'village':
            by_village[row.group_key] = row.count
    
    # 查询 3：疾病分组（需要特殊处理 JSON/ARRAY 字段）
    # SQLite 不支持 unnest，需要手动展开
    by_disease = {}
    try:
        # 尝试 PostgreSQL 语法 (unnest)
        disease_query = (
            select(
                func.unnest(Patient.disease_list).label('disease'),
                func.count(Patient.patient_id).label('cnt')
            )
            .where(and_(*base_filter))
            .group_by(func.unnest(Patient.disease_list))
        )
        disease_result = await db.execute(disease_query)
        by_disease = {row[0]: row[1] for row in disease_result.all() if row[0]}
    except Exception:
        # SQLite 回退：获取所有患者的 disease_list 字段
        patients_result = await db.execute(
            select(Patient.disease_list).where(and_(*base_filter))
        )
        disease_count = {}
        for row in patients_result.all():
            disease_list = row[0]
            if disease_list:
                # SQLite 可能返回 JSON 字符串或 Python list
                if isinstance(disease_list, str):
                    import json
                    disease_list = json.loads(disease_list)
                for disease in disease_list:
                    disease_count[disease] = disease_count.get(disease, 0) + 1
        by_disease = disease_count
    
    result = {
        "total_patients": total_patients,
        "active_patients": active_patients,
        "by_disease": by_disease,
        "by_risk_level": by_risk_level,
        "by_village": by_village
    }
    
    # 缓存结果（60秒）
    cache_set(cache_key, result, ttl=60)
    
    return result


# 辅助函数
def calculate_age(birth_date: date) -> int:
    """根据生日计算年龄"""
    from datetime import date as date_cls
    today = date_cls.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def encrypt_patient_data(patient_data, encryption_service):
    """加密患者敏感数据（更新时使用）"""
    encrypted_data = patient_data.copy()
    
    # 加密姓名
    if 'name' in encrypted_data and encrypted_data['name']:
        encrypted_data['name_enc'] = enc.encrypt(encrypted_data['name'])
        del encrypted_data['name']
    
    # 加密身份证号
    if 'id_card' in encrypted_data and encrypted_data['id_card']:
        encrypted_data['id_card_enc'] = enc.encrypt(encrypted_data['id_card'])
        # 同时更新身份证哈希
        import hashlib
        encrypted_data['id_card_hash'] = hashlib.sha256(encrypted_data['id_card'].encode()).hexdigest()
        del encrypted_data['id_card']
    
    # 加密手机号
    if 'phone' in encrypted_data and encrypted_data['phone']:
        encrypted_data['phone_enc'] = enc.encrypt(encrypted_data['phone'])
        del encrypted_data['phone']
    
    return encrypted_data


def decrypt_patient_data(patient: Patient, encryption_service) -> dict:
    """解密患者敏感数据，同时保留加密字段以兼容 schema"""
    import logging
    from datetime import datetime as dt
    
    # 基础字段
    data = {
        'patient_id': patient.patient_id,
        'name_enc': patient.name_enc,  # 保留加密字段
        'id_card_enc': patient.id_card_enc,  # 保留加密字段
        'id_card_hash': patient.id_card_hash,
        'phone_enc': patient.phone_enc,  # 保留加密字段
        'gender': patient.gender,
        'birth_date': patient.birth_date,
        'age': patient.age,
        'address': patient.address,
        'village_code': patient.village_code,
        'manage_org_code': patient.manage_org_code,
        'manage_org_name': ORG_NAME_MAP.get(patient.manage_org_code, patient.manage_org_code or '-') if patient.manage_org_code else '-',
        'disease_list': patient.disease_list or [],
        'disease_names': [DISEASE_NAME_MAP.get(d, d) for d in (patient.disease_list or [])],
        'risk_level': patient.risk_level,
        'is_active': patient.is_active,
        'empi_status': patient.empi_status,
        'created_at': patient.created_at or dt.now(),
        'updated_at': patient.updated_at or dt.now(),
    }
    
    # 解密敏感字段（供返回给前端使用）
    try:
        if patient.name_enc:
            data['name'] = enc.decrypt(patient.name_enc)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"解密姓名失败: {e}")
        data['name'] = None
    
    try:
        if patient.id_card_enc:
            data['id_card'] = enc.decrypt(patient.id_card_enc)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"解密身份证号失败: {e}")
        data['id_card'] = None
    
    try:
        if patient.phone_enc:
            data['phone'] = enc.decrypt(patient.phone_enc)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"解密手机号失败: {e}")
        data['phone'] = None
    
    return data
