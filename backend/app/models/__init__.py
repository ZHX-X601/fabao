"""
SQLAlchemy 数据模型包

在此统一导入所有模型，确保 alembic 自动生成迁移、
Base.metadata.create_all() 时能发现全部表结构。
"""

from app.models.user import User  # noqa: F401
from app.models.conversation import Conversation  # noqa: F401
from app.models.message import Message  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.contract import Contract  # noqa: F401

__all__ = ["User", "Conversation", "Message", "Document", "Contract"]
