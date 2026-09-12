"""
文书生成相关 Pydantic 模型
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# 支持的文书类型（与前端 DocGenerate 页面的选项保持一致）
DOC_TYPES = ["借款合同", "劳动合同", "租赁合同", "民事起诉状"]


class DocumentGenerateRequest(BaseModel):
    """文书生成请求体"""

    doc_type: str = Field(description=f"文书类型，可选值：{DOC_TYPES}")
    form_data: dict[str, Any] = Field(
        default_factory=dict, description="表单数据（键为字段名，值为用户填写内容）"
    )

    @field_validator("doc_type")
    @classmethod
    def check_doc_type(cls, v: str) -> str:
        """校验文书类型是否在支持列表中"""
        if v not in DOC_TYPES:
            raise ValueError(f"不支持的文书类型：{v}，可选值：{DOC_TYPES}")
        return v


class DocumentOut(BaseModel):
    """文书记录返回体"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    doc_type: str
    form_data: dict[str, Any]
    generated_content: str
    created_at: datetime
