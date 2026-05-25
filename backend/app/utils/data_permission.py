"""数据权限工具 - 机构层级数据访问控制
省级 > 市县级 > 乡镇卫生院 > 村卫生室
规则：上级可查看/管理下级机构数据，下级不可查看上级数据
"""
from sqlalchemy import or_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.models import SysUser


# 机构层级编码规则（按编码长度判断）
# 8位  = 市县级 (46012301)
# 9位  = 乡镇级 (460123100)
# 10位+ = 村级   (4601231001)
LEVEL_PROVINCE = 0   # 省级
LEVEL_COUNTY = 1      # 市县级
LEVEL_TOWN = 2        # 乡镇/社区
LEVEL_VILLAGE = 3     # 村


def get_org_level(org_code: str) -> int:
    """根据机构编码判断层级"""
    if not org_code:
        return -1
    length = len(org_code)
    if length <= 8:
        return LEVEL_COUNTY  # 市县级
    elif length == 9:
        return LEVEL_TOWN    # 乡镇级
    else:
        return LEVEL_VILLAGE # 村级


def get_org_prefix(org_code: str) -> str:
    """获取机构编码的前缀（用于匹配下级机构）
    例如：46012301 → 460123（前6位行政区）+ 后面补齐
    简化版：直接字符串前缀匹配
    """
    level = get_org_level(org_code)
    if level == LEVEL_COUNTY:
        return org_code[:8]  # 匹配前8位
    elif level == LEVEL_TOWN:
        return org_code[:9]   # 匹配前9位
    return org_code


def build_org_filter(column, user: SysUser):
    """构建机构数据过滤条件（SQLAlchemy）
    
    Args:
        column: SQLAlchemy Column（如 Patient.manage_org_code）
        user: 当前登录用户
    
    Returns:
        SQLAlchemy BinaryExpression 或 None（None表示不限制）
    """
    if not user.org_code:
        return None
    
    user_role = user.role_code or ''
    user_org = user.org_code
    
    # 非管理员：只能看本机构
    if user_role != 'ADMIN':
        return column == user_org
    
    # 管理员：根据层级决定可见范围
    level = get_org_level(user_org)
    
    if level == LEVEL_VILLAGE:
        # 村级管理员：只能看本村
        return column == user_org
    
    elif level == LEVEL_TOWN:
        # 乡镇级管理员：看本镇 + 下属村
        return or_(
            column == user_org,
            column.like(f"{user_org}%")
        )
    
    else:
        # 市县级/省级管理员：看所有（不限制）
        return None


def can_create_user(creator: SysUser, target_role: str, target_org_code: str) -> tuple:
    """判断 creator 是否可以创建 target 用户
    Returns: (allowed: bool, reason: str)
    """
    # 医生不能创建管理员
    if creator.role_code != 'ADMIN' and target_role == 'ADMIN':
        return False, "医生账户不能创建管理员账户"
    
    creator_level = get_org_level(creator.org_code)
    target_level = get_org_level(target_org_code)
    
    # 上级不能在上级机构创建账户（不能在上级创建）
    if target_level < creator_level:
        return False, "不能在上级机构创建账户"
    
    return True, ""


def can_manage_user(manager: SysUser, target: SysUser) -> bool:
    """判断管理员是否可以管理目标用户（编辑/禁用/删除）"""
    if manager.role_code != 'ADMIN':
        return False
    
    manager_level = get_org_level(manager.org_code)
    target_level = get_org_level(target.org_code)
    
    # 只能管理同级或下级
    return target_level >= manager_level


def get_accessible_org_codes(user: SysUser, all_org_codes: List[str]) -> List[str]:
    """获取用户可访问的机构编码列表（含本级及所有下级）
    用于前端下拉框、数据过滤等场景
    """
    if user.role_code != 'ADMIN':
        return [user.org_code] if user.org_code else []
    
    user_org = user.org_code or ''
    level = get_org_level(user_org)
    result = [user_org]
    
    if level <= LEVEL_COUNTY:
        # 县级管理员：匹配所有下属机构
        prefix = user_org
        for o in all_org_codes:
            if o != user_org and o.startswith(prefix):
                result.append(o)
    elif level == LEVEL_TOWN:
        # 乡镇管理员：匹配本乡镇下属村
        for o in all_org_codes:
            if o != user_org and o.startswith(user_org):
                result.append(o)
    
    return result
