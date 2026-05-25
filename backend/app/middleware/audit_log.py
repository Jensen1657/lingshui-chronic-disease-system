"""审计日志中间件（自动记录所有 API 请求）"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
import asyncio
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """审计日志中间件（自动记录所有 API 请求）"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """处理请求并记录审计日志"""
        # 仅记录变更类 API 请求（跳过 GET 和健康检查）
        if request.method == "GET" or request.url.path in ("/health", "/", "/docs", "/openapi.json"):
            return await call_next(request)
        
        if not request.url.path.startswith("/api"):
            return await call_next(request)
        
        # 记录开始时间
        start_time = datetime.utcnow()
        
        # 处理请求
        response = await call_next(request)
        
        # 计算耗时
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # 异步记录审计日志（不阻塞响应）
        try:
            user_id, username, user_role = _extract_user_from_token(request)
            
            action = f"{request.method}"
            path_parts = request.url.path.split('/')
            resource = path_parts[3] if len(path_parts) > 3 else 'unknown'
            
            asyncio.create_task(
                _log_to_database(
                    action=action,
                    resource=resource,
                    resource_id=path_parts[-1] if path_parts[-1] else None,
                    ip_address=self._get_client_ip(request),
                    user_agent=request.headers.get("user-agent", ""),
                    request_method=request.method,
                    request_path=request.url.path,
                    response_status="success" if response.status_code < 400 else "error",
                    details={
                        "response_code": response.status_code,
                        "duration_seconds": duration,
                    },
                    user_id=user_id,
                    username=username,
                    user_role=user_role,
                )
            )
        except Exception as e:
            logger.debug(f"审计日志记录跳过: {e}")
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端 IP 地址"""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        return request.client.host if request.client else "unknown"


def _extract_user_from_token(request: Request) -> tuple:
    """从请求头中提取 JWT token 中的用户信息"""
    try:
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return ("anonymous", "anonymous", "ANONYMOUS")
        
        token = auth_header.split(" ")[1]
        from jose import jwt
        from app.config import settings
        
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username = payload.get("sub", "unknown")
        role = payload.get("role", "UNKNOWN")
        # 使用 username 作为 user_id（简化处理）
        return (username, username, role)
    except Exception:
        return ("anonymous", "anonymous", "ANONYMOUS")


async def _log_to_database(
    action: str,
    resource: str,
    resource_id: Optional[str],
    ip_address: str,
    user_agent: str,
    request_method: str,
    request_path: str,
    response_status: str,
    details: dict,
    user_id: str = "system",
    username: str = "system",
    user_role: str = "SYSTEM",
):
    """异步记录审计日志到数据库"""
    try:
        from app.db.session import async_session_factory
        from app.services.audit_log_service import AuditLogService
        
        async with async_session_factory() as db:
            await AuditLogService.log_action(
                db=db,
                user_id=user_id,
                username=username,
                user_role=user_role,
                action=action,
                resource=resource,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                request_method=request_method,
                request_path=request_path,
                response_status=response_status,
                details=details,
            )
            await db.commit()
    except Exception as e:
        logger.debug(f"审计日志写入失败: {e}")
