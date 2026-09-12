"""
自定义业务异常模块

约定：
- 所有业务异常继承自 BizError，携带业务状态码 code 与提示信息 message
- main.py 中注册了全局异常处理器，BizError 及其子类会被统一包装为
  {"code": xxx, "message": "...", "data": null} 的响应格式
"""

from typing import Optional


class BizError(Exception):
    """业务异常基类（默认按服务器错误 500 处理）"""

    code: int = 500
    message: str = "服务器内部错误"

    def __init__(self, message: Optional[str] = None, code: Optional[int] = None):
        # 允许在抛出时临时覆盖默认的提示信息 / 状态码
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        super().__init__(self.message)


class BadRequestError(BizError):
    """请求参数错误（400）"""

    code = 400
    message = "请求参数错误"


class UnauthorizedError(BizError):
    """未登录或 token 无效（401）"""

    code = 401
    message = "未登录或登录已过期"


class ForbiddenError(BizError):
    """无权限访问（403）"""

    code = 403
    message = "无权限执行该操作"


class NotFoundError(BizError):
    """资源不存在（404）"""

    code = 404
    message = "资源不存在"


class ConflictError(BizError):
    """资源冲突，如用户名已存在（409）"""

    code = 409
    message = "资源已存在"
