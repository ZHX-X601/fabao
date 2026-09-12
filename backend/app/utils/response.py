"""
统一响应格式工具

本项目所有接口统一返回：
{"code": 200, "message": "success", "data": {...}}
"""

from typing import Any, Optional


def ok(data: Optional[Any] = None) -> dict:
    """
    构造成功响应

    :param data: 业务数据，可以是 None / dict / list / Pydantic 模型等，
                 FastAPI 会自动完成 JSON 序列化（含 datetime 等类型）
    :return: 统一格式的响应字典
    """
    return {"code": 200, "message": "success", "data": data}
