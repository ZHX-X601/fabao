"""
FastAPI 应用入口

职责：
1. 创建 FastAPI 应用实例（含 lifespan 启动钩子）
2. 注册 CORS 中间件
3. 注册全局异常处理器（统一响应格式）
4. 挂载所有业务路由（前缀 /api/v1）
5. 提供健康检查接口
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.config import settings
from app.core.exceptions import BizError
from app.database import Base, engine

# 配置基础日志格式，便于排查问题
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期钩子

    启动时：自动建表（开发环境便捷开关，生产建议用 alembic）+ 确保上传目录存在
    关闭时：记录日志
    """
    if settings.AUTO_CREATE_TABLES:
        try:
            # 导入 models 包触发全部模型注册，create_all 才能发现所有表
            import app.models  # noqa: F401
            Base.metadata.create_all(bind=engine)
            logger.info("数据库表检查/创建完成")
        except Exception as exc:  # noqa: BLE001 数据库不可用时允许服务继续启动
            logger.warning("自动建表失败（请检查 MySQL 是否已启动）：%s", exc)

    # 确保上传目录存在（首次运行时创建）
    Path(settings.UPLOAD_PATH).mkdir(parents=True, exist_ok=True)
    logger.info("应用启动完成：%s", settings.APP_NAME)
    # 打印实际生效的跨域白名单，便于排查线上域名被拦截的问题
    logger.info("CORS 允许来源：%s", settings.CORS_ORIGINS)
    yield
    logger.info("应用已关闭")


# 创建应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="法宝 - AI法律助手 后端 API（统一前缀 /api/v1）",
    lifespan=lifespan,
)

# ---------- CORS 跨域中间件：允许前端开发服务器访问 ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- 全局异常处理器：统一响应格式 {"code", "message", "data"} ----------
@app.exception_handler(BizError)
async def biz_error_handler(request: Request, exc: BizError):
    """业务异常：按异常自身携带的状态码返回"""
    return JSONResponse(
        status_code=exc.code,
        content={"code": exc.code, "message": exc.message, "data": None},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """请求参数校验失败（422）：整理错误字段位置与原因后返回"""
    errors = [
        {
            "field": ".".join(str(loc) for loc in err.get("loc", [])),
            "message": err.get("msg", ""),
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"code": 422, "message": "请求参数校验失败", "data": errors},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    """兜底异常：任何未处理的异常统一按 500 返回，并记录完整堆栈"""
    logger.exception("未处理的异常：%s", exc)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误", "data": None},
    )


# ---------- 挂载业务路由：所有接口统一 /api/v1 前缀 ----------
app.include_router(api_router, prefix="/api/v1")


@app.get("/", summary="健康检查")
def health_check():
    """健康检查接口，同时可用于快速确认服务是否启动"""
    return {
        "code": 200,
        "message": "success",
        "data": {"app": settings.APP_NAME, "status": "running"},
    }
