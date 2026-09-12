"""
合同审查相关 Pydantic 模型
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class ContractOut(BaseModel):
    """合同审查记录返回体"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    file_path: str
    original_text: Optional[str] = None
    review_result: Optional[dict[str, Any]] = None
    created_at: datetime
