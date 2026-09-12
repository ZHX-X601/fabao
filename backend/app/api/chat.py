"""
AI 法律咨询接口：对话与消息管理
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.chat import (
    ConversationCreate,
    ConversationOut,
    MessageCreate,
    MessageOut,
    SendMessageOut,
)
from app.services import ai_service
from app.utils.response import ok

router = APIRouter(prefix="/chat")

# 送给 AI 的最大历史消息条数（避免上下文过长）
MAX_HISTORY = 10


def _get_owned_conversation(db: Session, conversation_id: int, user_id: int) -> Conversation:
    """
    获取当前用户名下的对话；不存在或不属于该用户时统一抛 404

    :raises NotFoundError: 对话不存在或无权访问
    """
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if conversation is None:
        raise NotFoundError("对话不存在")
    return conversation


@router.get("/conversations", summary="获取当前用户的对话列表")
def list_conversations(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """按最近更新时间倒序返回当前用户的全部对话"""
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return ok([ConversationOut.model_validate(c) for c in conversations])


@router.post("/conversations", summary="新建对话")
def create_conversation(
    body: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """新建一个空对话，返回对话信息（含 id）"""
    conversation = Conversation(user_id=current_user.id, title=body.title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return ok(ConversationOut.model_validate(conversation))


@router.delete("/conversations/{conversation_id}", summary="删除对话")
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除对话（消息表通过级联关系一并删除）"""
    conversation = _get_owned_conversation(db, conversation_id, current_user.id)
    db.delete(conversation)
    db.commit()
    return ok({"deleted": True})


@router.get("/conversations/{conversation_id}/messages", summary="获取对话的消息列表")
def list_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """返回指定对话内的全部消息（按创建时间正序）"""
    conversation = _get_owned_conversation(db, conversation_id, current_user.id)
    return ok([MessageOut.model_validate(m) for m in conversation.messages])


@router.post("/conversations/{conversation_id}/messages", summary="发送消息并获取 AI 回复")
async def send_message(
    conversation_id: int,
    body: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    发送消息接口（核心流程）：

    1. 保存用户消息
    2. 组装最近的历史消息作为上下文
    3. 调用 AI 服务生成回复
    4. 保存 AI 回复并刷新对话更新时间
    5. 返回两条消息
    """
    conversation = _get_owned_conversation(db, conversation_id, current_user.id)

    # ---------- 1. 保存用户消息 ----------
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=body.content,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 首条消息时，自动用消息内容截断生成对话标题（前端列表展示更友好）
    if conversation.title == "新的对话" or not conversation.title:
        conversation.title = body.content[:30]
        conversation.updated_at = datetime.now()
        db.commit()

    # ---------- 2. 组装历史上下文 ----------
    history_msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(MAX_HISTORY)
        .all()
    )
    history: list[dict[str, Any]] = [
        {"role": "assistant" if m.role == "assistant" else "user", "content": m.content or ""}
        for m in reversed(history_msgs)  # 数据库取的是倒序，这里反转回时间正序
    ]

    # ---------- 3. 调用 AI 服务生成回复 ----------
    reply_text = await ai_service.generate_reply(history[:-1], body.content)

    # ---------- 4. 保存 AI 回复，刷新对话更新时间 ----------
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=reply_text,
    )
    db.add(assistant_msg)
    conversation.updated_at = datetime.now()
    db.commit()
    db.refresh(assistant_msg)

    # ---------- 5. 返回结果 ----------
    return ok(
        SendMessageOut(
            conversation_id=conversation.id,
            user_message=MessageOut.model_validate(user_msg),
            assistant_message=MessageOut.model_validate(assistant_msg),
        )
    )
