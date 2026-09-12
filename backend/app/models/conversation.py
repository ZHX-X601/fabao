"""
对话模型（conversations 表）
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Conversation(Base):
    """对话表：一次 AI 法律咨询会话对应一条记录"""

    __tablename__ = "conversations"

    # 主键，自增
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="对话ID")
    # 所属用户：外键关联 users.id
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属用户ID"
    )
    # 对话标题（默认取用户首条消息截断，也可在创建时指定）
    title: Mapped[str] = mapped_column(
        String(100), nullable=False, default="新的对话", comment="对话标题"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # ---------- 关联关系 ----------
    user = relationship("User", back_populates="conversations")
    # 对话内的消息列表；删除对话时级联删除全部消息
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",  # 按时间正序返回消息
    )
