"""
User 模型别名 — auth.py 等模块使用 User 而非 SysUser
"""
from app.models import SysUser

# 导出别名，方便 auth.py 等模块直接使用 User
User = SysUser
