"""
文书生成服务

根据文书类型（doc_type）与表单数据（form_data），
用字符串模板拼接生成法律文书全文。

支持的文书类型与前端 DocGenerate 页面对应：
- 借款合同、劳动合同、租赁合同、民事起诉状
"""


class _SafeDict(dict):
    """字符串模板格式化辅助类：缺少的字段渲染为空字符串而不是抛 KeyError"""

    def __missing__(self, key: str) -> str:
        return ""


def _today() -> str:
    """获取当前日期的中文格式（作为文书落款日期）"""
    from datetime import datetime

    return datetime.now().strftime("%Y年%m月%d日")


def _to_chinese_amount(amount: str) -> str:
    """
    将阿拉伯数字金额转为中文大写（仅支持整数部分，演示用）
    :param amount: 金额字符串，如 "50000"
    :return: 中文大写，如 "伍万"
    """
    digits = "零壹贰叁肆伍陆柒捌玖"
    units = ["", "拾", "佰", "仟", "万", "拾", "佰", "仟", "亿"]
    try:
        num = int(str(amount).replace(",", "").split(".")[0])
    except (ValueError, TypeError):
        return amount
    if num == 0:
        return "零"
    result = ""
    s = str(num)
    for i, ch in enumerate(s):
        d = int(ch)
        unit = units[len(s) - 1 - i]
        if d != 0:
            result += digits[d] + unit
        elif result and not result.endswith("零"):
            result += "零"
    return result.rstrip("零")


# 各文书类型的文本模板，{字段名} 会被 form_data 中的同名字段替换
# 字段名与前端 DocGenerate.vue 中各类型的 fields[].prop 保持一致
_TEMPLATES: dict[str, str] = {
    "借款合同": (
        "借款合同\n\n"
        "甲方（出借人）：{lender}\n"
        "乙方（借款人）：{borrower}\n\n"
        "一、借款金额\n"
        "乙方向甲方借款人民币（大写）{amount}元整（￥{amount}元）。\n\n"
        "二、借款期限\n"
        "{period}。\n\n"
        "三、借款利息\n"
        "{rate}\n\n"
        "四、还款方式\n"
        "乙方应于借款到期日一次性向甲方归还全部借款本金及利息。\n\n"
        "五、违约责任\n"
        "乙方未按期还款的，应按逾期金额每日万分之五向甲方支付违约金。\n\n"
        "六、争议解决\n"
        "本合同履行过程中发生争议，双方应协商解决；协商不成的，可向甲方所在地人民法院提起诉讼。\n\n"
        "七、其他\n"
        "本合同一式两份，甲乙双方各执一份，自双方签字（盖章）之日起生效。\n\n"
        "甲方（签字/盖章）：                    乙方（签字/盖章）：\n\n"
        "日期：{__date__}"
    ),
    "劳动合同": (
        "劳动合同\n\n"
        "甲方（用人单位）：{employer}\n"
        "乙方（劳动者）：{worker}\n\n"
        "根据《中华人民共和国劳动合同法》及相关法律法规，甲乙双方在平等自愿、协商一致的基础上，签订本合同。\n\n"
        "一、合同期限\n"
        "{period}。\n\n"
        "二、工作岗位与内容\n"
        "乙方同意根据甲方工作需要，担任{position}岗位工作，应按时、保质完成工作任务。\n\n"
        "三、劳动报酬\n"
        "甲方每月以货币形式向乙方支付工资，月工资标准为人民币{salary}元，于每月15日前发放。\n\n"
        "四、工作时间与休息休假\n"
        "甲方安排乙方执行标准工时制度，乙方依法享有法定节假日、年休假等休息权利。\n\n"
        "五、社会保险\n"
        "甲方依法为乙方缴纳基本养老、医疗、失业、工伤、生育保险及住房公积金。\n\n"
        "六、合同的解除与终止\n"
        "双方解除、终止劳动合同应依照《劳动合同法》的规定执行。\n\n"
        "七、争议解决\n"
        "因履行本合同发生争议，可向劳动争议仲裁委员会申请仲裁。\n\n"
        "甲方（盖章）：                          乙方（签字）：\n\n"
        "日期：{__date__}"
    ),
    "租赁合同": (
        "租赁合同\n\n"
        "甲方（出租方）：{lessor}\n"
        "乙方（承租方）：{lessee}\n\n"
        "根据《中华人民共和国民法典》及相关法律法规，甲乙双方在平等自愿、协商一致的基础上，就租赁事宜达成如下协议：\n\n"
        "一、租赁物\n"
        "甲方将位于{target}出租给乙方使用。\n\n"
        "二、租赁期限\n"
        "{period}。\n\n"
        "三、租金及支付方式\n"
        "月租金为人民币{rent}元，乙方应于每月1日前支付当月租金。\n\n"
        "四、押金\n"
        "乙方应于本合同签订时向甲方支付押金人民币{rent}元，租赁期满且无违约时无息退还。\n\n"
        "五、双方权利义务\n"
        "甲方应保证租赁物符合约定用途；乙方应合理使用租赁物并按时支付租金，不得擅自转租。\n\n"
        "六、违约责任\n"
        "任何一方违反本合同约定，应向守约方支付违约金，造成损失的应予赔偿。\n\n"
        "七、争议解决\n"
        "本合同履行过程中发生争议，双方应协商解决；协商不成的，可向租赁物所在地人民法院提起诉讼。\n\n"
        "甲方（签字/盖章）：                    乙方（签字/盖章）：\n\n"
        "日期：{__date__}"
    ),
    "民事起诉状": (
        "民事起诉状\n\n"
        "原告：{plaintiff}\n"
        "被告：{defendant}\n\n"
        "诉讼请求：\n{claim}\n\n"
        "事实与理由：\n{reason}\n\n"
        "综上所述，为维护原告的合法权益，特依据《中华人民共和国民事诉讼法》相关规定，"
        "向贵院提起诉讼，请求依法判如所请。\n\n"
        "此致\n"
        "人民法院\n\n"
        "具状人：\n"
        "日期：{__date__}"
    ),
}


def generate_document(doc_type: str, form_data: dict) -> str:
    """
    生成法律文书全文

    :param doc_type: 文书类型（借款合同/劳动合同/租赁合同/民事起诉状）
    :param form_data: 用户填写的表单数据
    :return: 生成的文书文本
    :raises KeyError: 文书类型不存在对应模板
    """
    template = _TEMPLATES.get(doc_type)
    if template is None:
        raise KeyError(f"不支持的文书类型：{doc_type}")

    # 合并表单数据与内置变量（如落款日期、中文大写金额）
    data = dict(form_data or {})
    data["__date__"] = _today()
    # 借款合同的金额转中文大写
    if doc_type == "借款合同" and "amount" in data:
        data["amount_chinese"] = _to_chinese_amount(str(data["amount"]))
    # 借款利息：有利率则显示，否则视为无息
    if doc_type == "借款合同":
        rate = data.get("rate", "")
        data["rate"] = f"双方约定借款年利率为 {rate}%，利随本清。" if rate else "本借款为无息借款。"

    # 使用 _SafeDict 保证用户未填写的字段渲染为空
    return template.format_map(_SafeDict(data))
