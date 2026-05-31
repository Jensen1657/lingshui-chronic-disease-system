"""审计日志中间件（自动记录所有 API 请求）

修复：改用独立数据库会话 + BackgroundTask 模式，避免 asyncio.create_task 在 FastAPI 中静默失败。
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp
import logging
from datetime import datetime
from typing import Optional
import uuid

logger = logging.getLogger(__name__)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """审计日志中间件（自动记录所有变更类 API 请求）"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """处理请求并记录审计日志"""
        # 仅记录变更类 API 请求（跳过 GET 和健康检查）
        if request.method == "GET":
            return await call_next(request)

        path = request.url.path
        if path in ("/health", "/", "/docs", "/openapi.json"):
            return await call_next(request)

        if not path.startswith("/api"):
            return await call_next(request)

        # 记录开始时间
        start_time = datetime.utcnow()

        # 处理请求
        response = await call_next(request)

        # 计算耗时
        duration = (datetime.utcnow() - start_time).total_seconds()

        # 提取用户信息
        user_id, username, user_role = _extract_user_from_token(request)

        # 解析资源路径
        path_parts = path.split('/')
        resource = path_parts[3] if len(path_parts) > 3 else 'unknown'
        resource_id = path_parts[-1] if len(path_parts) > 1 and path_parts[-1] != resource else None

        # 标记敏感操作
        is_sensitive = 'Y' if any(kw in path for kw in ['delete', 'password', 'role', 'permission']) else 'N'

        # 直接异步写入（不使用 asyncio.create_task，避免会话关闭问题）
        try:
            await _write_audit_log(
                user_id=user_id,
                username=username,
                user_role=user_role,
                action=request.method,
                resource=resource,
                resource_id=resource_id,
                ip_address=_get_client_ip(request),
                user_agent=request.headers.get("user-agent", ""),
                request_method=request.method,
                request_path=path,
                response_status="success" if response.status_code < 400 else "error",
                details={
                    "response_code": response.status_code,
                    "duration_seconds": round(duration, 3),
                },
                is_sensitive=is_sensitive,
            )
        except Exception as e:
            # 审计日志写入失败不应阻断业务请求
            logger.warning(f"审计日志写入失败: {e}")

        return response


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
        return (username, username, role)
    except Exception:
        return ("anonymous", "anonymous", "ANONYMOUS")


def _get_client_ip(request: Request) -> str:
    """获取客户端 IP 地址"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


async def _write_audit_log(
    user_id: str,
    username: str,
    user_role: str,
    action: str,
    resource: str,
    resource_id: Optional[str],
    ip_address: str,
    user_agent: str,
    request_method: str,
    request_path: str,
    response_status: str,
    details: dict,
    is_sensitive: str = 'N',
):
    """使用独立数据库会话写入审计日志"""
    from app.db.session import _get_factory
    from app.models.audit_log import AuditLog

    factory = _get_factory()
    async with factory() as db:
        try:
            log = AuditLog(
                log_id=str(uuid.uuid4()),
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
                is_sensitive=is_sensitive,
            )
            db.add(log)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.debug(f"审计日志写入异常: {e}")
            raise
