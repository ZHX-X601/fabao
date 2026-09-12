"""
用户相关 Pydantic 模型：注册 / 登录 / 用户信息返回
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """用户注册请求体"""

    username: str = Field(
        min_length=3, max_length=50, description="用户名（3-50 个字符）"
    )
    email: EmailStr = Field(description="邮箱（自动校验格式）")
    password: str = Field(min_length=6, max_length=64, description="密码（至少 6 位）")


class UserLogin(BaseModel):
    """用户登录请求体"""

    username: str = Field(description="用户名")
    password: str = Field(description="密码")


class UserOut(BaseModel):
    """用户信息返回体（绝不包含密码字段）"""

    # from_attributes=True：允许直接从 ORM 对象读取字段构造模型（Pydantic V2 写法）
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    created_at: datetime


class LoginOut(BaseModel):
    """登录成功响应体：JWT 令牌 + 用户信息"""

    access_token: str = Field(description="JWT 访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    user: UserOut = Field(description="当前用户信息")
