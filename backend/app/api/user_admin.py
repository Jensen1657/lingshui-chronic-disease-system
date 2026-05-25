"""
用户管理 API - 管理员账户管理医生账户
支持：创建/编辑/禁用用户、机构层级数据权限控制
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional, List
from datetime import datetime
import bcrypt

from app.db.session import get_db
from app.models import SysUser, DimRegion, SysRolePermission
from app.schemas.user import UserCreate, UserUpdate, UserResponse, RolePermission
from app.api.auth import get_current_user, get_password_hash

router = APIRouter()

# 机构层级定义（与 data_permission.py 保持一致）
ORG_LEVELS = {
    0: "省级",
    1: "市县级", 
    2: "乡镇卫生院/社区卫生服务中心",
    3: "村卫生室"
}

# 账户类型
ACCOUNT_TYPES = {
    "ADMIN": "管理员账户",
    "DOCTOR": "医生账户"
}


def get_org_level(org_code: str) -> int:
    """根据机构编码判断层级（与 data_permission.py 逻辑一致）"""
    if not org_code:
        return -1
    code_len = len(org_code)
    # 8位及以下 = 市县级（如 46012301）
    if code_len <= 8:
        return 1
    # 9位 = 乡镇级（如 460123100）
    elif code_len == 9:
        return 2
    # 10位及以上 = 村级（如 4601231001）
    else:
        return 3


def can_manage_user(manager: SysUser, target: SysUser) -> bool:
    """判断管理员是否可以管理目标用户"""
    # 管理员只能管理同机构或下级机构的用户
    manager_level = get_org_level(manager.org_code)
    target_level = get_org_level(target.org_code)
    
    # 上级不能被下级管理
    if target_level < manager_level:
        return False
    
    # 同级或下级可以管理
    if target_level >= manager_level:
        return True
    
    return False


async def get_user_accessible_orgs(user: SysUser, db: AsyncSession) -> List[str]:
    """获取用户可访问的机构编码列表（含所有下级）"""
    user_level = get_org_level(user.org_code)
    
    if user.role_code == "ADMIN":
        # 管理员可以看到本级及以下所有机构
        result = await db.execute(
            select(DimRegion.org_code).where(
                or_(
                    DimRegion.org_code == user.org_code,
                    DimRegion.parent_code.like(f"{user.org_code[:user_level*3]}%"),
                )
            )
        )
        rows = result.scalars().all()
        orgs = list(rows)
        if user.org_code not in orgs:
            orgs.append(user.org_code)
        return orgs
    else:
        # 医生只能看到自己机构
        return [user.org_code]


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    role_code: Optional[str] = None,
    org_code: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户列表（仅管理员）
    - 管理员只能看到本级及下级机构的用户
    - 支持按关键词、角色、机构、状态筛选
    """
    if current_user.role_code != "ADMIN":
        raise HTTPException(status_code=403, detail="只有管理员账户可以查看用户列表")
    
    # 构建查询条件
    conditions = []
    
    # 数据权限：只显示本级及下级机构
    accessible_orgs = await get_user_accessible_orgs(current_user, db)
    conditions.append(SysUser.org_code.in_(accessible_orgs))
    
    if keyword:
        conditions.append(
            or_(
                SysUser.username.contains(keyword),
                SysUser.real_name.contains(keyword),
            )
        )
    
    if role_code:
        conditions.append(SysUser.role_code == role_code)
    
    if org_code:
        conditions.append(SysUser.org_code == org_code)
    
    if is_active is not None:
        conditions.append(SysUser.is_active == is_active)
    
    # 查询总数
    count_query = select(func.count()).select_from(SysUser).where(and_(*conditions))
    total = (await db.execute(count_query)).scalar() or 0
    
    # 查询数据
    query = (
        select(SysUser)
        .where(and_(*conditions))
        .order_by(SysUser.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    results = (await db.execute(query)).scalars().all()
    
    # 获取机构名称映射
    org_codes = list(set(u.org_code for u in results))
    org_names = {}
    if org_codes:
        org_result = await db.execute(
            select(DimRegion.org_code, DimRegion.org_name).where(
                DimRegion.org_code.in_(org_codes)
            )
        )
        for row in org_result.fetchall():
            org_names[row[0]] = row[1]
    
    items = []
    for u in results:
        item = {
            "user_id": u.user_id,
            "username": u.username,
            "real_name": u.real_name,
            "org_code": u.org_code,
            "org_name": org_names.get(u.org_code, u.org_code),
            "org_level": ORG_LEVELS.get(get_org_level(u.org_code), "未知"),
            "role_code": u.role_code,
            "role_name": ACCOUNT_TYPES.get(u.role_code, u.role_code),
            "is_active": u.is_active,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        items.append(item)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/users")
async def create_user(
    user_data: UserCreate,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建新用户（仅管理员）
    - 管理员只能创建 DOCTOR 类型账户，不能创建 ADMIN 账户
    - 只能创建同级或下级机构的账户
    """
    if current_user.role_code != "ADMIN":
        raise HTTPException(status_code=403, detail="只有管理员账户可以创建用户")
    
    # 医生不能创建管理员账户
    if user_data.role_code == "ADMIN":
        raise HTTPException(status_code=403, detail="医生账户不能创建管理员账户")
    
    # 检查目标机构是否在管辖范围内
    manager_level = get_org_level(current_user.org_code)
    target_level = get_org_level(user_data.org_code)
    
    if target_level < manager_level:
        raise HTTPException(
            status_code=403, 
            detail="不能在上级机构创建账户"
        )
    
    # 检查用户名是否已存在
    existing = await db.execute(
        select(SysUser).where(SysUser.username == user_data.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 创建用户
    password_hash = get_password_hash(user_data.password)
    new_user = SysUser(
        username=user_data.username,
        password_hash=password_hash,
        real_name=user_data.real_name,
        org_code=user_data.org_code,
        role_code=user_data.role_code,
        id_card_enc=user_data.id_card_enc,
        phone_enc=user_data.phone_enc,
        region_code=user_data.region_code,
        is_active=user_data.is_active,
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return {
        "message": "用户创建成功",
        "user_id": new_user.user_id,
        "username": new_user.username,
        "real_name": new_user.real_name,
        "role_code": new_user.role_code,
    }


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    更新用户信息（仅管理员）
    - 不能将角色改为 ADMIN（除非当前用户是超级管理员）
    - 只能管理本级及下级机构用户
    """
    if current_user.role_code != "ADMIN":
        raise HTTPException(status_code=403, detail="只有管理员账户可以编辑用户")
    
    # 查找目标用户
    result = await db.execute(select(SysUser).where(SysUser.user_id == user_id))
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 权限检查
    if not can_manage_user(current_user, target_user):
        raise HTTPException(status_code=403, detail="无权管理该用户")
    
    # 不允许通过此接口提升为管理员
    if user_data.role_code == "ADMIN" and target_user.role_code != "ADMIN":
        raise HTTPException(status_code=403, detail="不能将普通账户升级为管理员账户")
    
    # 更新字段
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(target_user, field, value)
    
    target_user.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "用户信息更新成功"}


@router.patch("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: str,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    启用/禁用用户（仅管理员）
    """
    if current_user.role_code != "ADMIN":
        raise HTTPException(status_code=403, detail="只有管理员账户可以操作")
    
    result = await db.execute(select(SysUser).where(SysUser.user_id == user_id))
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if not can_manage_user(current_user, target_user):
        raise HTTPException(status_code=403, detail="无权操作该用户")
    
    target_user.is_active = not target_user.is_active
    target_user.updated_at = datetime.utcnow()
    
    await db.commit()
    
    status_text = "启用" if target_user.is_active else "禁用"
    return {"message": f"用户已{status_text}", "is_active": target_user.is_active}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除用户（仅管理员，软删除/禁用）
    注意：实际执行禁用操作，不物理删除以保留数据完整性
    """
    if current_user.role_code != "ADMIN":
        raise HTTPException(status_code=403, detail="只有管理员账户可以删除用户")
    
    if user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="不能删除自己的账户")
    
    result = await db.execute(select(SysUser).where(SysUser.user_id == user_id))
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if not can_manage_user(current_user, target_user):
        raise HTTPException(status_code=403, detail="无权删除该用户")
    
    # 软删除：禁用账户
    target_user.is_active = False
    target_user.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "用户已禁用（软删除）"}


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: str,
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户详情"""
    if current_user.role_code != "ADMIN":
        raise HTTPException(status_code=403, detail="权限不足")
    
    result = await db.execute(select(SysUser).where(SysUser.user_id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 获取机构名称
    org_name = None
    org_result = await db.execute(
        select(DimRegion.org_name).where(DimRegion.org_code == user.org_code)
    )
    org_row = org_result.scalar_one_or_none()
    if org_row:
        org_name = org_row
    
    return {
        "user_id": user.user_id,
        "username": user.username,
        "real_name": user.real_name,
        "org_code": user.org_code,
        "org_name": org_name,
        "org_level": ORG_LEVELS.get(get_org_level(user.org_code), "未知"),
        "role_code": user.role_code,
        "role_name": ACCOUNT_TYPES.get(user.role_code, user.role_code),
        "is_active": user.is_active,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


# ==================== 机构管理 ====================

@router.get("/orgs")
async def list_orgs(
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取机构树形列表
    - 返回当前用户所在机构及所有下级机构
    - 树形结构展示层级关系
    """
    # 获取所有区域/机构数据
    result = await db.execute(
        select(DimRegion).order_by(DimRegion.region_level, DimRegion.region_code)
    )
    all_orgs = result.scalars().all()
    
    # 过滤出有 org_code 的记录
    org_list = []
    for org in all_orgs:
        if org.org_code:
            org_list.append({
                "region_code": org.region_code,
                "region_name": org.region_name,
                "region_level": org.region_level,
                "parent_code": org.parent_code,
                "org_code": org.org_code,
                "org_name": org.org_name,
                "level_name": ORG_LEVELS.get(org.region_level, f"级别{org.region_level}"),
            })
    
    # 构建树形结构
    def build_tree(items, parent_code=None):
        tree = []
        for item in items:
            if item["parent_code"] == parent_code:
                children = build_tree(items, item["region_code"])
                node = dict(item)
                if children:
                    node["children"] = children
                tree.append(node)
        return tree
    
    tree = build_tree(org_list)
    
    return {
        "tree": tree,
        "flat": org_list,
        "total": len(org_list),
    }


@router.get("/roles")
async def list_roles(
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取角色列表及权限定义"""
    result = await db.execute(select(SysRolePermission))
    roles = result.scalars().all()
    
    return [
        {
            "role_code": r.role_code,
            "role_name": r.role_name,
            "permissions": r.permissions,
            "description": r.description,
            "account_type": "ADMIN" if r.role_code == "ADMIN" else "DOCTOR",
        }
        for r in roles
    ]


@router.put("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    new_password: str = Query(..., min_length=6, max_length=100),
    current_user: SysUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    重置用户密码（仅管理员）
    """
    if current_user.role_code != "ADMIN":
        raise HTTPException(status_code=403, detail="只有管理员账户可以重置密码")
    
    result = await db.execute(select(SysUser).where(SysUser.user_id == user_id))
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if not can_manage_user(current_user, target_user):
        raise HTTPException(status_code=403, detail="无权操作该用户")
    
    target_user.password_hash = get_password_hash(new_password)
    target_user.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "密码重置成功"}
