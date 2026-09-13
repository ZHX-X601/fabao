"""
配置管理模块

使用 pydantic-settings 从环境变量 / .env 文件读取配置，
所有配置项集中在此处定义，其他模块统一从 settings 对象获取。
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ 目录的绝对路径（config.py 位于 backend/app/ 下，向上一层即 backend）
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """应用配置类：字段名与环境变量名一一对应（不区分大小写）"""

    # 告诉 pydantic-settings 从 backend/.env 读取配置
    # 用绝对路径，避免从其他目录启动 uvicorn 时读不到 .env 而回退到默认值
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",  # 忽略 .env 中多余的环境变量，避免启动报错
    )

    # ---------- 应用基础配置 ----------
    APP_NAME: str = "法宝 - AI法律助手"
    DEBUG: bool = False  # 调试模式：开启后打印 SQL 日志

    # ---------- 数据库配置 ----------
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "123456"
    DB_NAME: str = "fabao"
    # 数据库连接地址覆盖项：设置后直接使用该地址（支持 sqlite:// 等），便于测试或特殊部署
    DATABASE_URL_OVERRIDE: str = ""

    # ---------- JWT 认证配置 ----------
    JWT_SECRET_KEY: str = "fabao-please-change-this-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # token 有效期（分钟），默认 24 小时

    # ---------- 文件与建表配置 ----------
    UPLOAD_DIR: str = "uploads"  # 合同上传文件保存目录
    AUTO_CREATE_TABLES: bool = True  # 启动时自动建表（开发用，生产建议用 alembic）

    # ---------- 跨域配置 ----------
    # 允许携带跨域凭证的前端来源列表
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:5174"]

    # ---------- FastGPT 配置 ----------
    # FastGPT 服务地址（后端直接调用，不走前端代理）
    FASTGPT_BASE_URL: str = "http://localhost:3000/api"
    # FastGPT 应用专属 API Key（三个模块共用）
    FASTGPT_API_KEY: str = ""
    # AI 法律咨询应用 ID
    FASTGPT_APP_ID: str = ""
    # 文书生成应用 ID
    FASTGPT_DOC_APP_ID: str = ""
    # 合同审查应用 ID
    FASTGPT_CONTRACT_APP_ID: str = ""

    @property
    def DATABASE_URL(self) -> str:
        """
        拼接 SQLAlchemy 使用的 MySQL 连接地址（charset 保证中文正常存储）

        若配置了 DATABASE_URL_OVERRIDE 则优先使用（如 sqlite:///./test.db）
        """
        if self.DATABASE_URL_OVERRIDE:
            return self.DATABASE_URL_OVERRIDE
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def UPLOAD_PATH(self) -> str:
        """上传目录的绝对路径（无论从哪个目录启动 uvicorn 都指向 backend/uploads）"""
        return str(BASE_DIR / self.UPLOAD_DIR)


@lru_cache  # 单例缓存：保证全进程只读取一次配置
def get_settings() -> Settings:
    """获取全局配置单例"""
    return Settings()


# 全局配置对象：其他模块统一 `from app.config import settings` 使用
settings = get_settings()
