"""
合同审查服务

当前阶段为模拟审查：按固定规则返回 3 条风险条款（高/中/低各一条），
其中"原文引用"取自真实上传的合同文本，保证演示效果真实。
"""

# TODO: 接入真实 AI 审查接口（如 OpenAI / 通义千问），
#       建议做法：把 original_text 分段送入大模型，让其按
#       {level, title, clause, analysis, suggestion} 结构输出 JSON，再做聚合。


def _make_excerpt(original_text: str, start: int = 0, length: int = 60) -> str:
    """
    从合同原文中截取一段作为"原文引用"

    :param original_text: 合同原文
    :param start: 起始位置（文本过短时自动回退到 0）
    :param length: 截取的最大长度
    """
    text = " ".join(original_text.split())  # 压缩空白符，便于展示
    if not text:
        return "（未能提取到原文）"
    if start >= len(text):
        start = 0
    excerpt = text[start : start + length]
    return excerpt + ("..." if start + length < len(text) else "")


def review_contract(original_text: str, file_name: str) -> dict:
    """
    执行合同审查（模拟实现）

    :param original_text: 从上传文件中提取的合同原文
    :param file_name: 合同文件名（用于展示）
    :return: 审查结果字典（存入 contracts.review_result 字段）
    """
    # 取原文不同位置的片段作为各风险条款的"原文引用"
    excerpt_r1 = _make_excerpt(original_text, start=0, length=60)
    excerpt_r2 = _make_excerpt(original_text, start=120, length=60)
    excerpt_r3 = _make_excerpt(original_text, start=240, length=60)

    return {
        # 综合评分与结论
        "score": 72,
        "conclusion": f"《{file_name}》共识别出 3 处风险条款，整体风险等级：中。"
        "建议优先处理违约责任与付款条款相关的风险。",
        # 各等级风险数量统计
        "counts": {"high": 1, "medium": 1, "low": 1},
        # 风险条款列表：高 / 中 / 低各一条
        "risks": [
            {
                "level": "high",
                "level_text": "高风险",
                "title": "违约责任约定不对等",
                "clause": excerpt_r1,
                "analysis": "该条款仅约定了乙方的违约责任，未对甲方的违约情形作对等约定，"
                "权利义务明显失衡。依据《民法典》第六条公平原则，"
                "此类条款在诉讼中可能被认定部分无效，但仍会给您带来举证与维权成本。",
                "suggestion": "建议增加甲方违约时的对等责任条款，例如："
                "「任何一方违反本合同约定的，应向守约方支付合同总价款 20% 的违约金。」",
            },
            {
                "level": "medium",
                "level_text": "中风险",
                "title": "付款时间与方式约定不明确",
                "clause": excerpt_r2,
                "analysis": "该条款未明确付款的具体时间节点、支付方式及逾期付款的利息标准，"
                "发生争议时容易因约定不明产生纠纷，依据《民法典》第五百一十一条，"
                "履行时间不明确的，债权人可随时要求履行，但需给对方必要准备时间。",
                "suggestion": "建议明确为：付款期限、支付方式（银行转账账户）、"
                "逾期付款按日万分之五支付违约金等具体内容。",
            },
            {
                "level": "low",
                "level_text": "低风险",
                "title": "缺少争议解决与通知送达条款",
                "clause": excerpt_r3,
                "analysis": "合同未约定争议解决方式与文书送达地址，发生纠纷时"
                "可能因管辖法院不确定而增加诉讼成本，通知送达也容易产生争议。",
                "suggestion": "建议增加条款：因本合同引起的争议由合同签订地/原告所在地人民法院管辖；"
                "双方确认合同首部载明的地址为有效送达地址。",
            },
        ],
        # 合规正向提示
        "passed": [
            "合同包含双方主体信息与签署栏，主体要素完整。",
            "合同文本语言表述总体清晰，未发现明显歧义条款。",
        ],
    }
