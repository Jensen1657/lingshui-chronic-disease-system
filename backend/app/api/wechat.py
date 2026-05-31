"""
微信绑定管理路由 - CRUD 操作
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.db.session import get_db
from app.dependencies.auth import require_roles
from app.models import PatientWechat, Patient
from app.schemas.wechat import (
    WechatCreate, WechatUpdate, WechatResponse,
    WechatSearchParams, WechatStats, PaginatedWechatResponse
)

router = APIRouter()


def format_wechat(wechat):
    """Convert database model to dict matching schema fields"""
    return {
        "wechat_id": str(wechat.id),
        "patient_id": str(wechat.patient_id),
        "openid": wechat.openid,
        "nickname": wechat.nickname,
        "avatar_url": wechat.avatar_url,
        "bind_date": wechat.bound_at.date() if wechat.bound_at else None,
        "is_active": wechat.is_active,
        "unbind_date": None,  # 数据库模型没有这个字段
        "created_at": wechat.bound_at
    }


@router.post("")
@router.post("/", status_code=201)
async def create_wechat_binding(
        wechat: WechatCreate,
        db: AsyncSession = Depends(get_db)
):
    """
    创建微信绑定记录
    - 检查患者是否存在
    - 检查openid是否已绑定
    - 创建微信绑定记录
    """
    # 检查患者是否存在
    patient_result = await db.execute(
        select(Patient).where(Patient.patient_id == wechat.patient_id)
    )
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # 检查openid是否已绑定
    existing_result = await db.execute(
        select(PatientWechat).where(
            PatientWechat.openid == wechat.openid,
            PatientWechat.is_active == True
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该微信已绑定其他患者")

    # 检查患者是否已有活跃绑定
    patient_wechat_result = await db.execute(
        select(PatientWechat).where(
            PatientWechat.patient_id == wechat.patient_id,
            PatientWechat.is_active == True
        )
    )
    if patient_wechat_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该患者已有活跃的微信绑定")

    # 创建微信绑定记录
    db_wechat = PatientWechat(
        patient_id=wechat.patient_id,
        openid=wechat.openid,
        nickname=wechat.nickname,
        avatar_url=wechat.avatar_url,
        is_active=True
    )

    db.add(db_wechat)
    await db.commit()
    await db.refresh(db_wechat)

    return format_wechat(db_wechat)


@router.get("")
@router.get("/")
async def list_wechat_bindings(
        patient_id: Optional[UUID] = Query(None),
        openid: Optional[str] = Query(None),
        nickname: Optional[str] = Query(None),
        is_active: Optional[bool] = Query(None),
        bind_date_start: Optional[date] = Query(None),
        bind_date_end: Optional[date] = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        db: AsyncSession = Depends(get_db)
):
    """
    查询微信绑定记录列表（支持多条件筛选，分页返回）
    """
    # 构建基础查询
    base_query = select(PatientWechat)
    count_query = select(func.count(PatientWechat.id))

    # 应用筛选条件
    if patient_id:
        base_query = base_query.where(PatientWechat.patient_id == patient_id)
        count_query = count_query.where(PatientWechat.patient_id == patient_id)
    if openid:
        base_query = base_query.where(PatientWechat.openid == openid)
        count_query = count_query.where(PatientWechat.openid == openid)
    if nickname:
        base_query = base_query.where(PatientWechat.nickname.like(f"%{nickname}%"))
        count_query = count_query.where(PatientWechat.nickname.like(f"%{nickname}%"))
    if is_active is not None:
        base_query = base_query.where(PatientWechat.is_active == is_active)
        count_query = count_query.where(PatientWechat.is_active == is_active)

    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    offset = (page - 1) * page_size
    query = base_query.offset(offset).limit(page_size)

    result = await db.execute(query)
    wechat_bindings = result.scalars().all()

    return {
        "items": [format_wechat(w) for w in wechat_bindings],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{wechat_id}")
async def get_wechat_binding(
        wechat_id: str,
        db: AsyncSession = Depends(get_db)
):
    """
    根据 ID 获取微信绑定记录详情
    """
    result = await db.execute(
        select(PatientWechat).where(PatientWechat.id == int(wechat_id))
    )
    wechat_binding = result.scalar_one_or_none()

    if not wechat_binding:
        raise HTTPException(status_code=404, detail="微信绑定记录不存在")

    return format_wechat(wechat_binding)


@router.put("/{wechat_id}")
async def update_wechat_binding(
        wechat_id: str,
        wechat_update: WechatUpdate,
        db: AsyncSession = Depends(get_db)
):
    """
    更新微信绑定记录
    """
    result = await db.execute(
        select(PatientWechat).where(PatientWechat.id == int(wechat_id))
    )
    db_wechat = result.scalar_one_or_none()

    if not db_wechat:
        raise HTTPException(status_code=404, detail="微信绑定记录不存在")

    # 更新非空字段
    update_data = wechat_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_wechat, field, value)

    await db.commit()
    await db.refresh(db_wechat)

    return format_wechat(db_wechat)


@router.post("/{wechat_id}/unbind")
async def unbind_wechat(
        wechat_id: str,
        db: AsyncSession = Depends(get_db)
):
    """
    解绑微信
    """
    result = await db.execute(
        select(PatientWechat).where(PatientWechat.id == int(wechat_id))
    )
    db_wechat = result.scalar_one_or_none()

    if not db_wechat:
        raise HTTPException(status_code=404, detail="微信绑定记录不存在")

    if not db_wechat.is_active:
        raise HTTPException(status_code=400, detail="该微信已解绑")

    # 标记为不活跃
    db_wechat.is_active = False

    await db.commit()

    return {"message": "微信已解绑"}


@router.get("/patient/{patient_id}/active")
async def get_active_wechat_binding(
        patient_id: str,
        db: AsyncSession = Depends(get_db)
):
    """
    获取患者活跃的微信绑定记录
    """
    result = await db.execute(
        select(PatientWechat).where(
            PatientWechat.patient_id == patient_id,
            PatientWechat.is_active == True
        )
    )
    wechat_binding = result.scalar_one_or_none()

    if not wechat_binding:
        raise HTTPException(status_code=404, detail="该患者无活跃的微信绑定")

    return format_wechat(wechat_binding)


@router.get("/stats/summary")
async def get_wechat_stats(
        start_date: Optional[date] = Query(None),
        end_date: Optional[date] = Query(None),
        db: AsyncSession = Depends(get_db)
):
    """
    获取微信绑定统计信息
    """
    # TODO: 实际实现需要聚合查询
    return {
        "total_bindings": 0,
        "active_bindings": 0,
        "inactive_bindings": 0,
        "by_month": {},
        "avg_bindings_per_month": 0.0
    }


@router.get("/openid/{openid}")
async def get_wechat_by_openid(
        openid: str,
        db: AsyncSession = Depends(get_db)
):
    """
    根据 openid 获取微信绑定记录
    """
    result = await db.execute(
        select(PatientWechat).where(PatientWechat.openid == openid)
    )
    wechat_binding = result.scalar_one_or_none()

    if not wechat_binding:
        raise HTTPException(status_code=404, detail="微信绑定记录不存在")

    return format_wechat(wechat_binding)
