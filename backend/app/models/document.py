"""
文书生成记录模型（documents 表）
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Document(Base):
    """文书生成记录表：保存每次生成文书的表单数据与生成结果"""

    __tablename__ = "documents"

    # 主键，自增
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="记录ID")
    # 所属用户：外键关联 users.id
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属用户ID"
    )
    # 文书类型：起诉状 / 答辩状 / 律师函 / 授权委托书
    doc_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="文书类型")
    # 用户填写的表单数据（JSON 格式，结构随文书类型不同而不同）
    form_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, comment="表单数据")
    # 模板拼接生成的文书全文
    generated_content: Mapped[Optional[str]] = mapped_column(Text, comment="生成的文书内容")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )

    # ---------- 关联关系 ----------
    user = relationship("User", back_populates="documents")
