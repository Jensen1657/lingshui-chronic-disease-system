"""访问控制中间件（基于角色的权限管理）"""
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Callable
import logging

from app.config import settings
from app.dependencies.auth import get_current_user, User

logger = logging.getLogger(__name__)

# 角色权限映射
ROLE_PERMISSIONS = {
    "ADMIN": [
        "patient:create", "patient:read", "patient:update", "patient:delete",
        "followup:create", "followup:read", "followup:update", "followup:delete",
        "referral:create", "referral:read", "referral:update", "referral:delete",
        "assessment:create", "assessment:read", "assessment:update", "assessment:delete",
        "alert:create", "alert:read", "alert:update", "alert:delete",
        "tcm:create", "tcm:read", "tcm:update", "tcm:delete",
        "emergency:create", "emergency:read", "emergency:update", "emergency:delete",
        "self_report:create", "self_report:read", "self_report:update", "self_report:delete",
        "reminder:create", "reminder:read", "reminder:update", "reminder:delete",
        "wechat:create", "wechat:read", "wechat:update", "wechat:delete",
        "dashboard:read", "dashboard:export",
        "audit:read", "audit:export",
        "scoring:read", "quality_control:read",
    ],
    "DOCTOR": [
        "patient:create", "patient:read", "patient:update",
        "followup:create", "followup:read", "followup:update",
        "referral:create", "referral:read", "referral:update",
        "assessment:create", "assessment:read", "assessment:update",
        "alert:read",
        "tcm:create", "tcm:read", "tcm:update",
        "emergency:create", "emergency:read", "emergency:update",
        "self_report:read",
        "reminder:read",
        "dashboard:read",
        "scoring:read", "quality_control:read",
    ],
    "NURSE": [
        "patient:read",
        "followup:create", "followup:read", "followup:update",
        "referral:read",
        "assessment:read",
        "alert:read",
        "tcm:read",
        "self_report:read",
        "reminder:read", "reminder:create",
        "dashboard:read",
    ],
}


def check_permission(required_permission: str):
    """
    权限检查依赖注入
    用法：@router.get("/patients", dependencies=[Depends(check_permission("patient:read"))])
    """
    async def permission_checker(user: User = Depends(get_current_user)):
        user_permissions = ROLE_PERMISSIONS.get(user.role, [])
        
        if required_permission not in user_permissions:
            logger.warning(
                f"权限拒绝: 用户 {user.username} (角色 {user.role}) "
                f"尝试访问 {required_permission}"
            )
            raise HTTPException(
                status_code=403,
                detail=f"权限不足：需要 {required_permission} 权限"
            )
        
        return user
    
    return permission_checker


class RoleChecker:
    """角色检查器（可用于多个权限）"""
    
    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions
    
    async def __call__(self, user: User = Depends(get_current_user)):
        user_permissions = ROLE_PERMISSIONS.get(user.role, [])
        
        # 检查是否拥有任意一个所需权限
        has_permission = any(
            perm in user_permissions 
            for perm in self.required_permissions
        )
        
        if not has_permission:
            logger.warning(
                f"权限拒绝: 用户 {user.username} (角色 {user.role}) "
                f"尝试访问需要 {self.required_permissions} 之一的接口"
            )
            raise HTTPException(
                status_code=403,
                detail=f"权限不足：需要以下权限之一：{', '.join(self.required_permissions)}"
            )
        
        return user


# 便捷依赖注入
require_admin = RoleChecker(["patient:delete", "audit:read", "dashboard:export"])
require_doctor = RoleChecker(["patient:create", "followup:create"])
require_nurse = RoleChecker(["followup:create", "reminder:create"])
