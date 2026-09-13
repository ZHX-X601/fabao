"""
合同审查服务

调用 FastGPT 合同审查应用，对合同文本进行逐条风险识别，
返回结构化 JSON 审查报告。FastGPT 不可用时降级到本地模拟审查。
"""

import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# FastGPT 合同审查接口地址
_FASTGPT_URL = f"{settings.FASTGPT_BASE_URL}/v1/chat/completions"


# ========== 本地模拟降级 ==========


def _fallback_review(original_text: str, file_name: str) -> dict:
    """本地模拟审查（FastGPT 不可用时降级使用）"""
    text = " ".join(original_text.split())
    excerpt1 = (text[:60] + "...") if len(text) > 60 else text or "（未能提取到原文）"
    excerpt2 = (text[120:180] + "...") if len(text) > 180 else text or "（未能提取到原文）"
    excerpt3 = (text[240:300] + "...") if len(text) > 300 else text or "（未能提取到原文）"

    return {
        "score": 72,
        "conclusion": f"《{file_name}》共识别出 3 处风险条款，整体风险等级：中。"
        "建议优先处理违约责任与付款条款相关的风险。（AI 审查服务不可用，此为模拟结果）",
        "counts": {"high": 1, "medium": 1, "low": 1},
        "risks": [
            {
                "level": "high",
                "title": "违约责任约定不对等",
                "clause": excerpt1,
                "analysis": "该条款仅约定了乙方的违约责任，未对甲方的违约情形作对等约定，"
                "权利义务明显失衡。依据《民法典》第六条公平原则，"
                "此类条款在诉讼中可能被认定部分无效。",
                "suggestion": "建议增加甲方违约时的对等责任条款，例如："
                "「任何一方违反本合同约定的，应向守约方支付合同总价款 20% 的违约金。」",
                "law": "《中华人民共和国民法典》第六条",
            },
            {
                "level": "medium",
                "title": "付款时间与方式约定不明确",
                "clause": excerpt2,
                "analysis": "该条款未明确付款的具体时间节点、支付方式及逾期付款的利息标准，"
                "发生争议时容易因约定不明产生纠纷。",
                "suggestion": "建议明确付款期限、支付方式（银行转账账户）、"
                "逾期付款按日万分之五支付违约金等具体内容。",
                "law": "《中华人民共和国民法典》第五百一十一条",
            },
            {
                "level": "low",
                "title": "缺少争议解决与通知送达条款",
                "clause": excerpt3,
                "analysis": "合同未约定争议解决方式与文书送达地址，发生纠纷时"
                "可能因管辖法院不确定而增加诉讼成本。",
                "suggestion": "建议增加条款：因本合同引起的争议由合同签订地人民法院管辖；"
                "双方确认合同首部载明的地址为有效送达地址。",
                "law": "《中华人民共和国民事诉讼法》第三十四条",
            },
        ],
        "passed": [],
    }


# ========== FastGPT 调用与 JSON 解析 ==========


def _parse_fastgpt_json(raw_content: str) -> dict | None:
    """
    尝试从 FastGPT 返回的文本中提取 JSON。

    FastGPT 被指示直接输出 JSON（不带 markdown 代码块），
    但实际可能包裹在 ```json ... ``` 中，这里做兼容处理。
    """
    text = raw_content.strip()

    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试去掉 markdown 代码块包裹
    if text.startswith("```"):
        # 去掉首尾的 ```json 和 ```
        lines = text.split("\n")
        # 去掉第一行（```json 或 ```）
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        # 去掉最后一行（```）
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        try:
            return json.loads("\n".join(lines))
        except json.JSONDecodeError:
            pass

    # 最后尝试从文本中找到第一个 { 和最后一个 } 之间的内容
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    return None


def _map_fastgpt_result(fastgpt_json: dict, file_name: str) -> dict:
    """
    将 FastGPT 合同审查应用返回的 JSON 映射为前端期望的格式。

    FastGPT 返回格式：
      { risk_score, risk_stats, risks: [{level, category, clause, analysis, suggestion, law}], suggestion }

    前端期望格式：
      { score, conclusion, counts, risks: [{level, title, clause, analysis, suggestion, law}], passed }
    """
    risk_score = fastgpt_json.get("risk_score", 0)
    risk_stats = fastgpt_json.get("risk_stats", {})
    risks_raw = fastgpt_json.get("risks", [])
    suggestion = fastgpt_json.get("suggestion", "")

    # 映射 risks 数组：category → title, 保留 law 字段
    risks_mapped = []
    for r in risks_raw:
        risks_mapped.append(
            {
                "level": r.get("level", "low"),
                "title": r.get("category", "未分类"),
                "clause": r.get("clause", ""),
                "analysis": r.get("analysis", ""),
                "suggestion": r.get("suggestion", ""),
                "law": r.get("law", ""),
            }
        )

    return {
        "score": risk_score,
        "conclusion": suggestion or f"《{file_name}》审查完成，详见下方风险条款。",
        "counts": {
            "high": risk_stats.get("high", 0),
            "medium": risk_stats.get("medium", 0),
            "low": risk_stats.get("low", 0),
        },
        "risks": risks_mapped,
        # FastGPT 审查应用不输出"合规条款"，留空即可
        "passed": [],
    }


async def review_contract(original_text: str, file_name: str, user_id: int, contract_id: int) -> dict:
    """
    执行合同审查

    优先调用 FastGPT 合同审查应用；若未配置 Key 或调用失败/JSON 解析失败，
    则降级到本地模拟审查。

    :param original_text: 从上传文件中提取的合同原文
    :param file_name: 合同文件名（用于展示）
    :param user_id: 当前用户 ID（用于 FastGPT 会话隔离）
    :param contract_id: 合同记录主键（同一份合同多次审查共用同一 chatId，历史互相关联）
    :return: 审查结果字典
    """
    # 未配置 FastGPT，直接降级
    if not settings.FASTGPT_API_KEY or not settings.FASTGPT_CONTRACT_APP_ID:
        return _fallback_review(original_text, file_name)

    # 合同原文过短时也降级（无法有效审查）
    if len(original_text.strip()) < 50:
        logger.warning("合同原文过短（%d 字符），降级到本地模拟", len(original_text.strip()))
        return _fallback_review(original_text, file_name)

    # chatId 按"用户 + 合同记录"维度唯一（r=contracts 主键，前缀区分模块），
    # 不同用户 / 不同合同互不可见；同一合同重新审查会带上上次的审查历史
    payload = {
        "chatId": f"fabao-review-u{user_id}-r{contract_id}",
        "stream": False,
        "messages": [{"role": "user", "content": original_text}],
        "appId": settings.FASTGPT_CONTRACT_APP_ID,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
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
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            if not content:
                logger.warning("FastGPT 返回空内容，降级到本地模拟")
                return _fallback_review(original_text, file_name)

            # 尝试解析 JSON
            fastgpt_json = _parse_fastgpt_json(content)
            if fastgpt_json is None:
                logger.warning("FastGPT 返回内容无法解析为 JSON，降级到本地模拟")
                return _fallback_review(original_text, file_name)

            # 校验基本结构
            if "risk_score" not in fastgpt_json or "risks" not in fastgpt_json:
                logger.warning("FastGPT 返回 JSON 结构不符预期，降级到本地模拟")
                return _fallback_review(original_text, file_name)

            # 映射为前端格式
            return _map_fastgpt_result(fastgpt_json, file_name)

    except Exception as exc:
        logger.warning("FastGPT 合同审查调用失败：%s，降级到本地模拟", exc)
        return _fallback_review(original_text, file_name)
