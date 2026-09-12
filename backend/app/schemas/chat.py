"""
AI 法律咨询相关 Pydantic 模型：对话与消息的请求/响应
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    """新建对话请求体（标题可省略，默认“新的对话”）"""

    title: str = Field(default="新的对话", max_length=100, description="对话标题")


class ConversationOut(BaseModel):
    """对话信息返回体"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    """发送消息请求体"""

    content: str = Field(min_length=1, max_length=4000, description="消息内容（1-4000 字）")


class MessageOut(BaseModel):
    """消息返回体"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: datetime


class SendMessageOut(BaseModel):
    """发送消息接口的响应体：同时返回用户消息与 AI 回复"""

    conversation_id: int = Field(description="对话 ID")
    user_message: MessageOut = Field(description="用户消息")
    assistant_message: MessageOut = Field(description="AI 回复消息")
