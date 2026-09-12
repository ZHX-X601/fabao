"""
路由聚合模块

把各业务模块的路由汇总为 api_router，由 main.py 统一挂载到 /api/v1 前缀下。
"""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.document import router as document_router
from app.api.contract import router as contract_router

api_router = APIRouter()
api_router.include_router(auth_router, tags=["认证"])
api_router.include_router(chat_router, tags=["AI法律咨询"])
api_router.include_router(document_router, tags=["文书生成"])
api_router.include_router(contract_router, tags=["合同审查"])
