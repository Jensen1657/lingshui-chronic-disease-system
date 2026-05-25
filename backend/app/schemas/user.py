"""
User and Authentication Schemas
陵水县人民医院慢病管理系统 - 用户认证相关模型
"""
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID


class UserBase(BaseModel):
    """Base user schema"""
    model_config = ConfigDict(from_attributes=True)
    
    username: str = Field(..., min_length=3, max_length=50)
    real_name: str = Field(..., min_length=1, max_length=100)
    org_code: str = Field(..., max_length=50)
    role_code: str = Field(..., max_length=20)


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=6, max_length=100)
    id_card_enc: Optional[str] = None
    phone_enc: Optional[str] = None
    region_code: Optional[str] = Field(None, max_length=12)
    is_active: bool = True


class UserUpdate(BaseModel):
    """User update schema"""
    model_config = ConfigDict(from_attributes=True)
    
    real_name: Optional[str] = Field(None, min_length=1, max_length=100)
    org_code: Optional[str] = Field(None, max_length=50)
    role_code: Optional[str] = None
    phone_enc: Optional[str] = None
    is_active: Optional[bool] = None


class UserLogin(BaseModel):
    """User login schema"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class UserResponse(UserBase):
    """User response schema"""
    user_id: str
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class UserWithPermissions(UserResponse):
    """User with permissions schema"""
    permissions: List[str] = []


class Token(BaseModel):
    """Token schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """Token payload schema"""
    sub: Optional[str] = None
    exp: Optional[int] = None
    role: Optional[str] = None


class TokenRefresh(BaseModel):
    """Token refresh schema"""
    refresh_token: str


class PasswordChange(BaseModel):
    """Password change schema"""
    old_password: str = Field(..., min_length=6, max_length=100)
    new_password: str = Field(..., min_length=6, max_length=100)
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v, info):
        if 'old_password' in info.data and v == info.data['old_password']:
            raise ValueError('New password must be different from old password')
        return v


class RolePermission(BaseModel):
    """Role permission schema"""
    model_config = ConfigDict(from_attributes=True)
    
    role_code: str
    role_name: str
    permissions: List[str]
    description: Optional[str] = None
