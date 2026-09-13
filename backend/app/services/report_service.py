"""
合同审查报告生成服务：使用 python-docx 动态生成 .docx 报告
"""

from io import BytesIO

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

from app.core.exceptions import BadRequestError, NotFoundError

# ---------- 风险等级的中文标签与样式颜色 ----------
LEVEL_LABELS = {"high": "高风险", "medium": "中风险", "low": "低风险"}
LEVEL_COLORS = {
    "high": RGBColor(0xE5, 0x53, 0x3D),  # 红
    "medium": RGBColor(0xE6, 0xA2, 0x3C),  # 橙
    "low": RGBColor(0x90, 0x93, 0x99),  # 灰
}


def _set_chinese_font(run, size: int = 11, bold: bool = False, color: RGBColor | None = None):
    """
    给 run 设置中文字体（必须同时设置 ascii + eastAsia，否则中文会变方块）
    """
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")


def _add_heading(doc: Document, text: str, level: int = 1):
    """添加标题"""
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        _set_chinese_font(run, size=16 if level == 1 else 13, bold=True)
    return h


def _add_paragraph(doc: Document, text: str, *, bold: bool = False, color: RGBColor | None = None,
                   indent: bool = False):
    """添加段落，支持首行缩进（合同文书的惯用排版）"""
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.first_line_indent = Pt(24)  # 2 个字符的缩进
    run = p.add_run(text)
    _set_chinese_font(run, bold=bold, color=color)
    return p


def _add_horizontal_line(doc: Document):
    """添加一条分割线（用段落底边框实现）"""
    p = doc.add_paragraph()
    p_pr = p._p.get_or_add_pPr()
    p_bdr = p_pr.makeelement(qn("w:pBdr"), {})
    bottom = p_bdr.makeelement(qn("w:bottom"), {
        qn("w:val"): "single", qn("w:sz"): "6", qn("w:color"): "cccccc"
    })
    p_bdr.append(bottom)
    p_pr.append(p_bdr)


def generate_contract_report(contract) -> bytes:
    """
    根据合同审查记录生成 .docx 报告，返回二进制内容

    :param contract: Contract 数据库模型实例
    :return: .docx 文件的字节流
    :raises NotFoundError: 记录尚未审查（review_result 为空）
    """
    if not contract.review_result:
        raise NotFoundError("该合同尚未执行审查，无法生成报告")

    result = contract.review_result
    doc = Document()

    # ---------- 报告标题 ----------
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run("合同法律风险审查报告")
    _set_chinese_font(title_run, size=22, bold=True, color=RGBColor(0x1A, 0x3A, 0x5C))

    # 副标题：来源文件名
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = sub.add_run(f"《{contract.file_name}》")
    _set_chinese_font(sub_run, size=12, color=RGBColor(0x90, 0x93, 0x99))

    # 报告生成时间
    from datetime import datetime
    time_p = doc.add_paragraph()
    time_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    time_run = time_p.add_run(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    _set_chinese_font(time_run, size=10, color=RGBColor(0x90, 0x93, 0x99))

    doc.add_paragraph()  # 空行

    # ---------- 一、综合评分 ----------
    _add_heading(doc, "一、综合评分", level=1)
    score = result.get("score", 0)
    counts = result.get("counts", {}) or {}
    summary_text = (
        f"本合同安全评分为 {score} 分（满分 100 分）。"
        f"共识别高风险 {counts.get('high', 0)} 项、"
        f"中风险 {counts.get('medium', 0)} 项、"
        f"低风险 {counts.get('low', 0)} 项。"
    )
    _add_paragraph(doc, summary_text)

    # ---------- 二、整体结论 ----------
    _add_heading(doc, "二、整体审查结论", level=1)
    conclusion = result.get("conclusion", "（无）")
    _add_paragraph(doc, conclusion, indent=True)

    # ---------- 三、风险条款明细 ----------
    risks = result.get("risks", []) or []
    _add_heading(doc, f"三、风险条款明细（共 {len(risks)} 项）", level=1)
    if not risks:
        _add_paragraph(doc, "未识别到明显风险条款。")
    else:
        for idx, risk in enumerate(risks, start=1):
            level = risk.get("level", "low")
            _add_horizontal_line(doc)

            # 风险标题行：序号 + 标题 + 等级标签
            head_p = doc.add_paragraph()
            num_run = head_p.add_run(f"{idx}. ")
            _set_chinese_font(num_run, size=13, bold=True)
            title_run = head_p.add_run(risk.get("title", ""))
            _set_chinese_font(title_run, size=13, bold=True, color=RGBColor(0x1A, 0x3A, 0x5C))
            level_run = head_p.add_run(f"  [{LEVEL_LABELS.get(level, level)}]")
            _set_chinese_font(level_run, size=12, bold=True, color=LEVEL_COLORS.get(level))

            # 原文摘录
            clause_p = doc.add_paragraph()
            label_run = clause_p.add_run("【原文摘录】")
            _set_chinese_font(label_run, size=11, bold=True, color=RGBColor(0x90, 0x93, 0x99))
            text_run = clause_p.add_run(risk.get("clause", ""))
            _set_chinese_font(text_run, size=11)

            # 风险分析
            analysis_p = doc.add_paragraph()
            label_run = analysis_p.add_run("【风险分析】")
            _set_chinese_font(label_run, size=11, bold=True, color=RGBColor(0x90, 0x93, 0x99))
            text_run = analysis_p.add_run(risk.get("analysis", ""))
            _set_chinese_font(text_run, size=11)

            # 修改建议
            suggest_p = doc.add_paragraph()
            label_run = suggest_p.add_run("【修改建议】")
            _set_chinese_font(label_run, size=11, bold=True, color=RGBColor(0x52, 0xA8, 0x6B))
            text_run = suggest_p.add_run(risk.get("suggestion", ""))
            _set_chinese_font(text_run, size=11)

            # 法律依据（可能为空）
            law = risk.get("law") or ""
            if law:
                law_p = doc.add_paragraph()
                label_run = law_p.add_run("【法律依据】")
                _set_chinese_font(label_run, size=11, bold=True, color=RGBColor(0x3A, 0x6B, 0x9F))
                text_run = law_p.add_run(law)
                _set_chinese_font(text_run, size=11)

    # ---------- 四、合规条款 ----------
    passed = result.get("passed", []) or []
    if passed:
        _add_heading(doc, "四、合规条款", level=1)
        for idx, item in enumerate(passed, start=1):
            p = doc.add_paragraph()
            run = p.add_run(f"{idx}. {item}")
            _set_chinese_font(run, size=11)

    # ---------- 免责声明 ----------
    _add_heading(doc, "五、免责声明", level=1)
    disclaimer = (
        "本报告由 AI 自动生成，仅供用户参考，不能替代专业律师的法律意见。"
        "如需作为正式法律文件使用，请咨询执业律师并以其意见为准。"
    )
    _add_paragraph(doc, disclaimer, indent=True)

    # ---------- 落款 ----------
    doc.add_paragraph()
    sign_p = doc.add_paragraph()
    sign_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    sign_run = sign_p.add_run("AI 法律助手 — 法宝")
    _set_chinese_font(sign_run, size=11, color=RGBColor(0x1A, 0x3A, 0x5C))

    # 写入内存，返回字节
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def sanitize_filename(name: str) -> str:
    """
    清理文件名：去掉路径、特殊字符，避免下载时的响应头注入或文件名乱码
    """
    import re

    if not name:
        return "report.docx"
    # 只保留中英文、数字、点、连字符、下划线
    name = re.sub(r"[^\w\u4e00-\u9fa5.\-]", "_", name)
    name = name[:80]  # 防止过长
    base = name.rsplit(".", 1)[0] if "." in name else name
    return f"{base}_审查报告.docx"