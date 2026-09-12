"""
数据库连接与会话管理模块

职责：
1. 创建 SQLAlchemy 引擎（engine）
2. 创建会话工厂（SessionLocal）
3. 声明所有 ORM 模型的公共基类（Base）
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# 创建数据库引擎
# pool_pre_ping：每次取连接前先 ping 一下，避免 MySQL 8 小时空闲断连后报错
# pool_recycle：连接最长复用时间（秒），进一步规避断连问题
# echo：调试模式下打印 SQL 语句
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG,
)

# 创建会话工厂
# autoflush=False：查询前不自动把未提交的修改刷入数据库，行为更可控
# expire_on_commit=False：提交后对象属性不失效，避免响应序列化时再次查库
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的公共基类（SQLAlchemy 2.0 新式声明式基类）"""
