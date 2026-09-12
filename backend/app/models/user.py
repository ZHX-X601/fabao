"""
用户模型（users 表）
"""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """用户表：存储注册用户的账号信息"""

    __tablename__ = "users"

    # 主键，自增
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="用户ID")
    # 用户名：唯一，非空
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="用户名"
    )
    # 邮箱：唯一，非空
    email: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True, comment="邮箱"
    )
    # 密码：存储 bcrypt 哈希后的密文，绝不存明文
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False, comment="加密后的密码")
    # 创建时间：由数据库在插入时自动填充
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    # 更新时间：插入时填充，行数据更新时自动刷新
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # ---------- 关联关系 ----------
    # 用户名下的对话 / 文书 / 合同审查记录；删除用户时级联删除
    conversations = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
    documents = relationship(
        "Document", back_populates="user", cascade="all, delete-orphan"
    )
    contracts = relationship(
        "Contract", back_populates="user", cascade="all, delete-orphan"
    )
