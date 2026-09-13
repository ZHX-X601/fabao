"""
AI 调用封装服务

调用 FastGPT 的 OpenAI 兼容接口（非流式），返回完整回复文本。
如果 FastGPT 不可用（未配置 Key / 请求失败），自动降级到本地关键词模拟回复。
"""

import httpx

from app.config import settings

# FastGPT 对话接口完整地址
_FASTGPT_URL = f"{settings.FASTGPT_BASE_URL}/v1/chat/completions"

# 基于关键词的模拟回复规则（FastGPT 不可用时降级使用）
_MOCK_RULES: list[tuple[tuple[str, ...], str]] = [
    (
        ("工资", "欠薪", "劳动报酬", "拖欠"),
        "根据《劳动合同法》第三十条，用人单位应当按照劳动合同约定和国家规定，"
        "及时足额支付劳动报酬。用人单位拖欠的，您可以：\n"
        "1. 与用人单位协商，要求限期支付；\n"
        "2. 向劳动监察部门投诉或申请劳动仲裁；\n"
        "3. 对仲裁结果不服的，可依法向人民法院提起诉讼。\n"
        "请注意保存劳动合同、工资条、考勤记录等证据材料。",
    ),
    (
        ("借款", "欠钱", "借条", "债务"),
        "根据《民法典》第六百七十五条，借款人应当按照约定的期限返还借款。"
        "对方到期不还的，您可以凭借条、转账记录、聊天记录等证据向法院起诉。\n"
        "提醒：民间借贷诉讼时效为三年，请尽快主张权利，避免超过诉讼时效。",
    ),
    (
        ("离婚", "婚姻", "财产分割"),
        "根据《民法典》第一千零七十九条，夫妻一方要求离婚的，可以由有关组织进行调解"
        "或者直接向人民法院提起离婚诉讼。法院审理离婚案件，应当进行调解；"
        "感情确已破裂、调解无效的，应当准予离婚。\n"
        "关于财产分割：夫妻共同财产由双方协议处理；协议不成的，由人民法院根据财产"
        "具体情况，按照照顾子女、女方和无过错方权益的原则判决。",
    ),
]


def _mock_reply(user_message: str) -> str:
    """本地模拟回复（FastGPT 不可用时的降级方案）"""
    for keywords, reply in _MOCK_RULES:
        if any(keyword in user_message for keyword in keywords):
            return reply
    return (
        "您好，我是法宝 AI 法律助手。您的问题我已收到：\n"
        f"「{user_message[:50]}{'...' if len(user_message) > 50 else ''}」\n\n"
        "为了给您更准确的法律建议，请补充以下信息：\n"
        "1. 事件发生的具体时间与经过；\n"
        "2. 您目前掌握的证据材料；\n"
        "3. 您希望达成的目标。"
    )


async def generate_reply(history: list[dict], user_message: str, chat_id: str) -> str:
    """
    生成 AI 回复

    流程：
    1. 组装消息（历史 + 当前用户消息）
    2. 调用 FastGPT 接口
    3. 成功则返回 AI 回复；失败则降级到本地模拟回复

    :param history: 当前对话的历史消息，格式 [{"role": "user"/"assistant", "content": "..."}]
    :param user_message: 用户本次发送的消息内容
    :param chat_id: FastGPT 会话标识（唯一），决定 FastGPT 侧的记忆与日志归属。
                    必须按"用户 + 对话"维度传入（如 fabao-chat-u{user_id}-c{conversation_id}），
                    否则不同用户/对话会共用同一份记忆造成串台。长度需 < 250。
    :return: AI 回复文本
    """
    # 未配置 FastGPT Key，直接使用本地模拟
    if not settings.FASTGPT_API_KEY:
        return _mock_reply(user_message)

    # 组装消息列表：历史 + 当前用户消息
    messages = list(history)
    messages.append({"role": "user", "content": user_message})

    payload = {
        "chatId": chat_id,
        "stream": False,
        "messages": messages,
    }
    # 部分 FastGPT 版本要求在请求体中携带 appId
    if settings.FASTGPT_APP_ID:
        payload["appId"] = settings.FASTGPT_APP_ID

    try:
        # 使用 httpx 异步调用 FastGPT，设置超时避免长时间阻塞
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                _FASTGPT_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.FASTGPT_API_KEY}",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            # OpenAI 兼容格式：回复内容在 choices[0].message.content
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if content:
                return content
            # FastGPT 返回了空内容，降级
            return _mock_reply(user_message)
    except Exception:
        # 任何异常（网络错误 / 超时 / FastGPT 不可用）都降级到本地模拟回复
        return _mock_reply(user_message)
