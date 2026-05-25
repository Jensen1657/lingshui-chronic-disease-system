"""
认证依赖模块
提供 get_current_user、get_current_active_user 等依赖项
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.config import settings
from app.db.session import get_db
from app.models import SysUser

# JWT 配置
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM

# Bearer 认证方案
security = HTTPBearer()


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
) -> SysUser:
    """
    获取当前认证用户
    - 验证 JWT token
    - 从数据库获取用户
    - 返回用户对象
    """
    token = credentials.credentials

    # 验证 JWT token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭证",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 从数据库获取用户
    result = await db.execute(
        select(SysUser).where(SysUser.username == username)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
        current_user: SysUser = Depends(get_current_user)
) -> SysUser:
    """
    获取当前活跃用户
    - 检查用户状态
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账号已禁用"
        )

    return current_user


async def get_admin_user(
        current_user: SysUser = Depends(get_current_active_user)
) -> SysUser:
    """
    获取管理员用户
    - 检查用户是否为 ADMIN 角色
    """
    if getattr(current_user, 'role_code', None) != 'ADMIN':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


def require_roles(*roles: str):
    """RBAC 角色检查依赖工厂
    
    用法:
        @router.get("/admin-only", dependencies=[Depends(require_roles('ADMIN'))])
        @router.get("/doctor-or-admin", dependencies=[Depends(require_roles('ADMIN', 'DOCTOR'))])
    """
    async def role_checker(current_user: SysUser = Depends(get_current_active_user)) -> SysUser:
        user_role = getattr(current_user, 'role_code', None)
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要以下角色之一: {', '.join(roles)}"
            )
        return current_user
    return role_checker


async def get_user_from_token(token: str) -> Optional[SysUser]:
    """
    从 JWT token 中提取用户信息（不查询数据库）
    用于审计日志中间件
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # 不查询数据库，只返回用户 ID
        # 审计日志只需要 user_id
        class FakeUser:
            def __init__(self, user_id: str):
                self.user_id = user_id
        
        return FakeUser(user_id)
    except JWTError:
        return None
