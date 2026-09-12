"""
合同审查记录模型（contracts 表）
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Contract(Base):
    """合同审查记录表：保存上传的合同文件、提取的原文与审查结果"""

    __tablename__ = "contracts"

    # 主键，自增
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="记录ID")
    # 所属用户：外键关联 users.id
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属用户ID"
    )
    # 用户上传时的原始文件名
    file_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="上传的文件名")
    # 文件在服务器上的存储路径
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, comment="文件存储路径")
    # 从 docx / pdf 中提取出的合同原文
    original_text: Mapped[Optional[str]] = mapped_column(Text, comment="提取的合同原文")
    # 审查结果（JSON）：风险等级、风险条款列表等；上传后未审查时为 NULL
    review_result: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, comment="审查结果")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )

    # ---------- 关联关系 ----------
    user = relationship("User", back_populates="contracts")
