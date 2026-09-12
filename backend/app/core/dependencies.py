"""
公共依赖模块

通过 FastAPI 依赖注入机制为路由提供：
1. 数据库会话（get_db）
2. 当前登录用户（get_current_user）
"""

from collections.abc import Generator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.database import SessionLocal
from app.models.user import User

# HTTPBearer 用于从请求头 Authorization: Bearer <token> 中提取令牌
# auto_error=False：令牌缺失时不由库直接抛 403，而是返回 None，由我们统一抛业务异常
bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """
    数据库会话依赖

    每个请求创建一个独立会话，请求结束后自动关闭（生成器依赖的标准写法）
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    当前登录用户依赖

    流程：提取 Bearer 令牌 -> 校验解析 JWT -> 查询用户是否存在
    :raises UnauthorizedError: 未携带令牌 / 令牌无效或过期 / 用户不存在
    """
    # 1. 请求头未携带令牌
    if credentials is None:
        raise UnauthorizedError()

    # 2. 校验并解析令牌，取出用户 ID
    payload = decode_access_token(credentials.credentials)
    user_id = int(payload["sub"])

    # 3. 查询用户（用户被删除后，旧 token 也会立即失效）
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise UnauthorizedError("用户不存在或已被删除")
    return user
