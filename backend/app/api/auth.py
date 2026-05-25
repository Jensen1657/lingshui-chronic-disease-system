"""
认证路由 - 登录、登出、获取当前用户信息
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from datetime import datetime, timedelta
import bcrypt
import hashlib

from app.db.session import get_db
from app.config import settings
from app.models import SysUser
from app.schemas.user import UserLogin

router = APIRouter()
security = HTTPBearer()


# JWT 工具函数
def create_access_token(data: dict, expires_delta: timedelta = None):
    """创建 JWT 访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码 - 支持 bcrypt 和 SHA-256 格式"""
    if hashed_password.startswith('$'):
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    else:
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


# 获取当前用户
async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
):
    """获取当前登录用户"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
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

    # 从数据库查询用户
    from sqlalchemy import select
    result = await db.execute(select(SysUser).where(SysUser.username == username))
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
):
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账号已禁用"
        )
    return current_user


@router.post("/login")
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    用户登录
    支持用户名/密码登录，返回 JWT token
    """
    # 查询数据库验证用户
    from sqlalchemy import select

    result = await db.execute(select(SysUser).where(SysUser.username == login_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role_code},
        expires_delta=access_token_expires
    )
    
    # 创建刷新令牌（有效期7天）
    refresh_token = create_access_token(
        data={"sub": user.username, "type": "refresh"},
        expires_delta=timedelta(days=7)
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # 秒
        "user": {"username": user.username, "real_name": user.real_name, "role": user.role_code}
    }


@router.get("/me")
async def get_me(current_user=Depends(get_current_user)):
    """
    获取当前登录用户信息
    """
    return {
        "username": current_user.username,
        "real_name": current_user.real_name,
        "role": current_user.role_code,
        "is_active": current_user.is_active,
    }


@router.post("/logout")
async def logout():
    """
    用户登出
    （前端需删除本地存储的 token）
    """
    return {"message": "登出成功"}


@router.post("/refresh")
async def refresh_token(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
):
    """
    刷新访问令牌
    - 使用 refresh_token 获取新的 access_token
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        # 验证是否为 refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌",
            )
        
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌",
            )
        
        # 查询用户
        from sqlalchemy import select
        result = await db.execute(select(SysUser).where(SysUser.username == username))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被禁用",
            )
        
        # 创建新的访问令牌
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role_code},
            expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌",
        )
