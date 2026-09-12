"""
消息模型（messages 表）
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Message(Base):
    """消息表：对话中的一条用户提问或 AI 回复"""

    __tablename__ = "messages"

    # 主键，自增
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="消息ID")
    # 所属对话：外键关联 conversations.id，删除对话时级联删除
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属对话ID",
    )
    # 角色：仅允许 "user"（用户提问）/ "assistant"（AI 回复）
    role: Mapped[str] = mapped_column(String(20), nullable=False, comment="角色 user/assistant")
    # 消息正文
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="消息内容")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )

    # ---------- 关联关系 ----------
    conversation = relationship("Conversation", back_populates="messages")
