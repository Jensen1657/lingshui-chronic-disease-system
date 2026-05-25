"""数据加密服务（合规要求：PII 字段加密存储）"""
from cryptography.fernet import Fernet, InvalidToken
from cryptography.exceptions import InvalidKey
import base64
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class EncryptionService:
    """PII 数据加密/解密服务（AES-128-CBC + HMAC-SHA256）"""

    def __init__(self):
        # 从配置中读取密钥（需在 .env 中设置 ENCRYPTION_KEY）
        key = settings.ENCRYPTION_KEY
        if not key:
            # 如果没有配置，使用 JWT_SECRET_KEY 派生（不推荐生产环境）
            logger.warning("ENCRYPTION_KEY 未配置，使用 JWT_SECRET_KEY 派生（不推荐）")
            key = base64.urlsafe_b64encode(settings.JWT_SECRET_KEY.encode()[:32])

        if isinstance(key, str):
            key = key.encode()
        if len(key) == 44:  # base64 encoded Fernet key
            self._fernet = Fernet(key)
        else:
            # 从字符串生成 Fernet key
            key = base64.urlsafe_b64encode(key[:32])
            self._fernet = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """加密明文，返回 base64 编码的密文"""
        if not plaintext:
            return plaintext
        try:
            ciphertext = self._fernet.encrypt(plaintext.encode())
            return base64.urlsafe_b64encode(ciphertext).decode()
        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise ValueError("加密失败") from e

    def decrypt(self, ciphertext: str) -> str:
        """解密 base64 编码的密文，返回明文"""
        if not ciphertext:
            return ciphertext
        try:
            decoded = base64.urlsafe_b64decode(ciphertext.encode())
            plaintext = self._fernet.decrypt(decoded)
            return plaintext.decode()
        except InvalidToken:
            logger.error("解密失败：无效的 token 或密钥错误")
            raise ValueError("解密失败：数据可能已损坏或密钥错误") from None
        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise ValueError("解密失败") from e

    def encrypt_dict(self, data: dict, fields: list) -> dict:
        """批量加密字典中的指定字段"""
        result = data.copy()
        for field in fields:
            if field in result and result[field]:
                result[field] = self.encrypt(str(result[field]))
        return result

    def decrypt_dict(self, data: dict, fields: list) -> dict:
        """批量解密字典中的指定字段"""
        result = data.copy()
        for field in fields:
            if field in result and result[field]:
                result[field] = self.decrypt(result[field])
        return result


# 全局单例
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """获取加密服务单例"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service

# 模块级单例实例，供其他模块直接 import 使用
encryption_service = get_encryption_service()
