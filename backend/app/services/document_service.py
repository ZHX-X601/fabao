"""
文书生成服务

调用 FastGPT 文书生成应用，根据用户提供的文书类型和表单信息，
由 AI 起草格式规范的法律文书。AI 返回结构化 JSON（含 title + sections 数组），
后端解析后直接用于 Word 排版和前端预览。

FastGPT 不可用时降级到本地模板生成 JSON。
"""

import json
import re

import httpx

from app.config import settings

# FastGPT 文书生成接口地址
_FASTGPT_URL = f"{settings.FASTGPT_BASE_URL}/v1/chat/completions"


# ========== 本地模板降级（FastGPT 不可用时使用） ==========


def _today() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y年%m月%d日")


# 占位符长度规范（按信息类型）
_PLACEHOLDER = {
    "name": "______",           # 人名/公司名 6
    "id_card": "__________________",  # 身份证号 18
    "phone": "___________",     # 电话 11
    "date": "________",         # 日期 8
    "money": "__________",      # 金额 10
    "address": "____________________",  # 地址 20
    "org": "________________",  # 法院/律所 16
    "default": "________",     # 其他 8
}


def _fallback_generate(doc_type: str, form_data: dict) -> dict:
    """本地模板降级：生成结构化 JSON（与 AI 返回格式一致）"""
    d = dict(form_data or {})
    PH = _PLACEHOLDER

    if doc_type == "民事起诉状":
        plaintiff = d.get("plaintiff") or f"姓名{PH['name']}，身份证号{PH['id_card']}，电话{PH['phone']}，住址{PH['address']}"
        defendant = d.get("defendant") or f"姓名{PH['name']}，身份证号{PH['id_card']}，住址{PH['address']}"
        claims_items = d.get("claims", "").strip()
        facts_text = d.get("facts", "").strip()
        evidence_text = d.get("evidence", "").strip()
        court = d.get("court") or f"{PH['org']}"

        sections = [
            {"type": "party", "role": "原告", "content": plaintiff},
            {"type": "party", "role": "被告", "content": defendant},
            {"type": "blank", "spacing": 1},
            {"type": "heading", "content": "诉讼请求"},
        ]
        if claims_items:
            for idx, item in enumerate(_split_items(claims_items)):
                sections.append({"type": "numbered", "number": _cn_num(idx), "content": item})
        else:
            sections.append({"type": "numbered", "number": "一", "content": f"（请填写诉讼请求）{PH['default']}"})

        sections.append({"type": "blank", "spacing": 1})
        sections.append({"type": "heading", "content": "事实与理由"})
        if facts_text:
            for para in facts_text.split("\n"):
                para = para.strip()
                if para:
                    sections.append({"type": "paragraph", "content": para})
        else:
            sections.append({"type": "paragraph", "content": f"（请填写事实与理由）{PH['default']}"})

        if evidence_text:
            sections.append({"type": "blank", "spacing": 1})
            sections.append({"type": "heading", "content": "证据清单"})
            for idx, item in enumerate(_split_items(evidence_text)):
                sections.append({"type": "numbered", "number": _cn_num(idx), "content": item})

        sections += [
            {"type": "blank", "spacing": 1},
            {"type": "center", "content": "此致", "bold": True},
            {"type": "center", "content": court, "bold": True},
            {"type": "blank", "spacing": 1},
            {"type": "signature", "content": "具状人：（签名或盖章）"},
            {"type": "signature", "content": _today()},
        ]
        return {"title": "民事起诉状", "sections": sections}

    elif doc_type == "民事答辩状":
        respondent = d.get("respondent") or f"姓名{PH['name']}，身份证号{PH['id_card']}，电话{PH['phone']}，住址{PH['address']}"
        opponent = d.get("opponent") or f"姓名{PH['name']}，住址{PH['address']}"
        opinion = d.get("opinion", "").strip()
        defense_facts = d.get("defense_facts", "").strip()
        conclusion = d.get("conclusion", "").strip()
        court = d.get("court") or f"{PH['org']}"

        sections = [
            {"type": "party", "role": "答辩人", "content": respondent},
            {"type": "party", "role": "被答辩人", "content": opponent},
            {"type": "blank", "spacing": 1},
            {"type": "heading", "content": "答辩意见"},
        ]
        if opinion:
            for para in opinion.split("\n"):
                para = para.strip()
                if para:
                    sections.append({"type": "paragraph", "content": para})
        else:
            sections.append({"type": "paragraph", "content": "（请填写答辩意见）"})

        sections.append({"type": "blank", "spacing": 1})
        sections.append({"type": "heading", "content": "事实与理由"})
        if defense_facts:
            for para in defense_facts.split("\n"):
                para = para.strip()
                if para:
                    sections.append({"type": "paragraph", "content": para})
        else:
            sections.append({"type": "paragraph", "content": "（请填写事实与理由）"})

        if conclusion:
            sections += [
                {"type": "blank", "spacing": 1},
                {"type": "heading", "content": "答辩结论"},
            ]
            for para in conclusion.split("\n"):
                para = para.strip()
                if para:
                    sections.append({"type": "paragraph", "content": para})

        sections += [
            {"type": "blank", "spacing": 1},
            {"type": "center", "content": "此致", "bold": True},
            {"type": "center", "content": court, "bold": True},
            {"type": "blank", "spacing": 1},
            {"type": "signature", "content": "答辩人：（签名或盖章）"},
            {"type": "signature", "content": _today()},
        ]
        return {"title": "民事答辩状", "sections": sections}

    elif doc_type == "律师函":
        recipient = d.get("recipient") or f"{PH['name']}"
        lawyer = d.get("lawyer") or f"{PH['name']}"
        law_firm = d.get("law_firm") or f"{PH['org']}"
        statement = d.get("statement", "").strip()
        legal_opinion = d.get("legal_opinion", "").strip()
        demand = d.get("demand", "").strip()
        deadline = d.get("deadline") or f"收到本函之日起{PH['date']}内"

        sections = [
            {"type": "center", "content": f"致：{recipient}", "bold": True},
        ]
        # 引言
        intro = f"本所系{law_firm}，指派{lawyer}律师，就如下事宜向贵方致函如下："
        sections.append({"type": "paragraph", "content": intro})

        if statement:
            sections += [
                {"type": "blank", "spacing": 1},
                {"type": "heading", "content": "一、事实陈述"},
            ]
            for para in statement.split("\n"):
                para = para.strip()
                if para:
                    sections.append({"type": "paragraph", "content": para})

        if legal_opinion:
            sections += [
                {"type": "blank", "spacing": 1},
                {"type": "heading", "content": "二、法律意见"},
            ]
            for para in legal_opinion.split("\n"):
                para = para.strip()
                if para:
                    sections.append({"type": "paragraph", "content": para})

        if demand:
            sections += [
                {"type": "blank", "spacing": 1},
                {"type": "heading", "content": "三、郑重函告"},
            ]
            for idx, item in enumerate(_split_items(demand)):
                sections.append({"type": "numbered", "number": _cn_num(idx), "content": item})

        # 履行期限
        sections += [
            {"type": "blank", "spacing": 1},
            {"type": "paragraph", "content": f"请贵方于{deadline}内履行上述义务，逾期本所将进一步采取法律措施。"},
            {"type": "blank", "spacing": 1},
            {"type": "signature", "content": law_firm},
            {"type": "signature", "content": f"{lawyer} 律师"},
            {"type": "signature", "content": _today()},
        ]
        return {"title": "律 师 函", "sections": sections}

    elif doc_type == "授权委托书":
        principal = d.get("principal") or f"姓名{PH['name']}，身份证号{PH['id_card']}"
        agent = d.get("agent") or f"姓名{PH['name']}，身份证号{PH['id_card']}，电话{PH['phone']}"
        matter = d.get("matter", "").strip()
        authority = d.get("authority") or "一般代理"
        valid_period = d.get("valid_period") or f"自{PH['date']}起至{PH['date']}止"

        sections = [
            {"type": "blank", "spacing": 1},
            {"type": "party", "role": "委托人", "content": principal},
            {"type": "party", "role": "受委托人", "content": agent},
            {"type": "blank", "spacing": 1},
            {"type": "paragraph", "content": f"{principal}现委托{agent}，代为办理如下事项："},
            {"type": "blank", "spacing": 1},
            {"type": "heading", "content": "一、委托事项"},
        ]
        if matter:
            for para in matter.split("\n"):
                para = para.strip()
                if para:
                    sections.append({"type": "paragraph", "content": para})
        else:
            sections.append({"type": "paragraph", "content": "（请填写委托事项）"})

        sections += [
            {"type": "blank", "spacing": 1},
            {"type": "heading", "content": "二、代理权限"},
        ]
        if authority in ("一般代理", "一般授权"):
            sections.append({
                "type": "paragraph",
                "content": "受托人在上述委托事项范围内所实施的法律行为及签署的相关文书，本委托人均予以承认。",
            })
        elif authority in ("特别代理", "特别授权"):
            sections.append({
                "type": "paragraph",
                "content": "受托人在上述委托事项范围内享有特别授权，包括但不限于：代为承认、放弃、变更诉讼请求，进行和解，提起反诉或上诉，签收法律文书等。",
            })
        else:
            sections.append({"type": "paragraph", "content": f"代理权限：{authority}"})

        sections += [
            {"type": "blank", "spacing": 1},
            {"type": "heading", "content": "三、委托期限"},
            {"type": "paragraph", "content": f"本委托书有效期为：{valid_period}。"},
            {"type": "blank", "spacing": 1},
            {"type": "signature", "content": "委托人：（签名或盖章）"},
            {"type": "signature", "content": _today()},
        ]
        return {"title": "授权委托书", "sections": sections}

    # 未知类型
    return {
        "title": doc_type,
        "sections": [
            {"type": "notice", "content": f"暂不支持的文书类型：{doc_type}，请配置 FastGPT 后重试"},
        ],
    }


# ========== 辅助函数 ==========

_CN_NUMS = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]


def _cn_num(i: int) -> str:
    """序号转中文（一、二、...、十、十一、...）"""
    if i < 10:
        return _CN_NUMS[i]
    if i < 20:
        return "十" + _CN_NUMS[i - 10]
    if i < 100:
        tens = i // 10
        ones = i % 10
        return _CN_NUMS[tens - 1] + "十" + (_CN_NUMS[ones - 1] if ones else "")
    return str(i + 1)


def _split_items(text: str) -> list[str]:
    """将一段文本拆成列表项"""
    if not text or not text.strip():
        return []
    lines = [line.strip().lstrip("0123456789.、). 　") for line in text.split("\n")]
    lines = [line for line in lines if line]
    if len(lines) > 1:
        return lines
    if "；" in text:
        return [s.strip() for s in text.split("；") if s.strip()]
    parts = re.split(r"(?<=。)\s*", text)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) > 1:
        return parts
    return [text.strip()]


# ========== AI 返回 JSON 解析 ==========


def _extract_json(text: str) -> dict | None:
    """
    从 AI 返回文本中提取 JSON 对象。

    AI 可能在 JSON 前后附带解释文字，或用 ```json ``` 包裹，
    此函数尽力提取出第一个合法的 {...} 结构。
    """
    if not text or not text.strip():
        return None

    # 1. 尝试直接解析整段文本
    try:
        result = json.loads(text.strip())
        if isinstance(result, dict) and "title" in result:
            return result
    except (json.JSONDecodeError, ValueError):
        pass

    # 2. 去掉 ```json ... ``` 包裹后解析
    code_block_re = re.compile(r"```(?:json)?\s*\n?(.*?)\n?\s*```", re.DOTALL)
    match = code_block_re.search(text)
    if match:
        try:
            result = json.loads(match.group(1).strip())
            if isinstance(result, dict) and "title" in result:
                return result
        except (json.JSONDecodeError, ValueError):
            pass

    # 3. 从文本中找第一个 { ... } 配对
    brace_start = text.find("{")
    if brace_start != -1:
        depth = 0
        for i in range(brace_start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[brace_start : i + 1]
                    try:
                        result = json.loads(candidate)
                        if isinstance(result, dict) and "title" in result:
                            return result
                    except (json.JSONDecodeError, ValueError):
                        pass
                    break

    return None


def _validate_sections(sections: list) -> list:
    """校验并修正 sections 数组中的每个元素"""
    valid_types = {"party", "heading", "numbered", "paragraph", "center", "signature", "blank", "notice"}
    cleaned = []
    for s in sections:
        if not isinstance(s, dict):
            continue
        t = s.get("type", "")
        if t not in valid_types:
            # 无法识别的 type 降级为 paragraph
            s = {"type": "paragraph", "content": str(s.get("content", ""))}
        # 确保必填字段存在
        if t in ("party", "heading", "paragraph", "center", "signature", "notice") and not s.get("content"):
            continue
        if t == "party" and not s.get("role"):
            s["role"] = "当事人"
        if t == "numbered":
            if not s.get("content"):
                continue
            if not s.get("number"):
                s["number"] = "●"
        if t == "blank":
            s["spacing"] = max(1, min(3, int(s.get("spacing", 1))))
        cleaned.append(s)
    return cleaned


# ========== FastGPT 调用 ==========


def _build_doc_prompt(doc_type: str, form_data: dict) -> str:
    """
    根据文书类型和表单数据，拼接成 FastGPT 能理解的用户消息。
    """
    lines = [f"请帮我起草一份【{doc_type}】。以下是已知信息：\n"]

    field_map = {
        "民事起诉状": [
            ("plaintiff", "原告信息"), ("defendant", "被告信息"),
            ("claims", "诉讼请求"), ("facts", "事实与理由"),
            ("evidence", "证据清单"), ("court", "此致法院"),
        ],
        "民事答辩状": [
            ("respondent", "答辩人信息"), ("opponent", "被答辩人信息"),
            ("opinion", "答辩意见"), ("defense_facts", "事实与理由"),
            ("conclusion", "答辩结论"), ("court", "此致法院"),
        ],
        "律师函": [
            ("recipient", "致函对象"), ("lawyer", "发函律师"),
            ("law_firm", "律师事务所"), ("statement", "事实陈述"),
            ("legal_opinion", "法律意见"), ("demand", "郑重函告要求"),
            ("deadline", "履行期限"),
        ],
        "授权委托书": [
            ("principal", "委托人"), ("agent", "受委托人"),
            ("matter", "委托事项"), ("authority", "代理权限"),
            ("valid_period", "有效期"),
        ],
    }

    fields = field_map.get(doc_type, [])
    for key, label in fields:
        if v := form_data.get(key):
            lines.append(f"{label}：{v}")

    return "\n".join(lines)


async def generate_document(doc_type: str, form_data: dict) -> dict:
    """
    生成法律文书，返回结构化 JSON（title + sections）

    优先调用 FastGPT 文书生成应用；若未配置 Key 或调用失败，
    则降级到本地模板生成 JSON。

    :param doc_type: 文书类型（民事起诉状/民事答辩状/律师函/授权委托书）
    :param form_data: 用户填写的表单数据
    :return: 结构化文书数据 {"title": str, "sections": [...]}
    """
    # 未配置 FastGPT Key，直接使用本地降级
    if not settings.FASTGPT_API_KEY or not settings.FASTGPT_DOC_APP_ID:
        return _fallback_generate(doc_type, form_data)

    user_message = _build_doc_prompt(doc_type, form_data)

    payload = {
        "chatId": f"fabao-doc-{doc_type}",
        "stream": False,
        "messages": [{"role": "user", "content": user_message}],
        "appId": settings.FASTGPT_DOC_APP_ID,
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
            if content:
                parsed = _extract_json(content)
                if parsed and parsed.get("title") and parsed.get("sections"):
                    parsed["sections"] = _validate_sections(parsed["sections"])
                    return parsed
                # AI 返回了内容但不是合法 JSON → 降级
            return _fallback_generate(doc_type, form_data)
    except Exception:
        return _fallback_generate(doc_type, form_data)
