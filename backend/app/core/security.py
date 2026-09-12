"""
安全认证工具：密码哈希 + JWT 生成与校验
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.core.exceptions import UnauthorizedError

# 密码哈希上下文：使用 bcrypt 算法（自动加盐，无需手动处理）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """把明文密码哈希为 bcrypt 密文"""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与数据库中的哈希是否匹配"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: int, username: str, expires_minutes: Optional[int] = None
) -> str:
    """
    生成 JWT 访问令牌

    :param user_id: 用户 ID（写入 sub 声明）
    :param username: 用户名（写入自定义声明，便于业务展示）
    :param expires_minutes: 有效期（分钟），不传则使用配置默认值
    :return: 编码后的 JWT 字符串
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.JWT_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {
        "sub": str(user_id),  # JWT 标准声明：主题（此处放用户 ID，必须为字符串）
        "username": username,
        "exp": expire,  # JWT 标准声明：过期时间
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    校验并解析 JWT

    :param token: JWT 字符串（不含 Bearer 前缀）
    :return: 解析出的声明字典
    :raises UnauthorizedError: token 无效或已过期
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        # sub 中存储用户 ID，缺失视为非法 token
        if "sub" not in payload:
            raise UnauthorizedError()
        return payload
    except JWTError:
        # 过期 / 签名不匹配 / 格式错误等所有 JWT 异常统一按未登录处理
        raise UnauthorizedError()
