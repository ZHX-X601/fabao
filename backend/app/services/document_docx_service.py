"""
法律文书 docx 生成服务：基于结构化 JSON 生成有专业排版的 Word 文档

核心设计：
  AI 返回的是 {"title": str, "sections": [{type, ...}, ...]} 结构化 JSON，
  后端按 sections 中每个元素的 type 确定性选择排版样式，无需正则猜测。

与合同审查报告字体策略对齐：
  - 必须同时设置 ascii + eastAsia，否则中文在 Word 中会变方块
  - 字体统一 Microsoft YaHei（eastAsia）+ Times New Roman（ascii/hAnsi）
  - 中文文书标准排版：标题二号居中加粗、节标题三号加粗、正文小四首行缩进 2 字符
"""

from datetime import datetime
from io import BytesIO

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

from app.core.exceptions import BadRequestError

# ========== 样式常量 ==========
BLACK = RGBColor(0x00, 0x00, 0x00)            # 纯黑（全文统一）
TEXT_COLOR = BLACK

CHINESE_FONT = "Microsoft YaHei"  # 微软雅黑
ENGLISH_FONT = "Times New Roman"


# ========== 字体与段落工具函数 ==========

def _set_run_font(run, size: int = 12, bold: bool = False,
                  color: RGBColor | None = None, italic: bool = False):
    """统一设置 run 的字体（同时配 ascii + eastAsia，中文不会变方块）"""
    if color is None:
        color = TEXT_COLOR
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = CHINESE_FONT
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        from docx.oxml import OxmlElement
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:eastAsia"), CHINESE_FONT)
    rFonts.set(qn("w:ascii"), ENGLISH_FONT)
    rFonts.set(qn("w:hAnsi"), ENGLISH_FONT)


def _set_default_style(doc: Document):
    """设置文档 Normal 样式（影响所有未单独设置的段落）"""
    style = doc.styles["Normal"]
    style.font.name = CHINESE_FONT
    style.font.size = Pt(12)
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        from docx.oxml import OxmlElement
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:eastAsia"), CHINESE_FONT)
    rFonts.set(qn("w:ascii"), ENGLISH_FONT)
    rFonts.set(qn("w:hAnsi"), ENGLISH_FONT)


# ========== 按 section type 排版 ==========

def _render_title(doc: Document, text: str):
    """大标题（如"民事起诉状"）：二号字、居中、加粗"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(24)
    p.paragraph_format.line_spacing = 1.5
    run = p.add_run(text)
    _set_run_font(run, size=22, bold=True, color=BLACK)


def _render_party(doc: Document, section: dict):
    """当事人信息行：'原告：xxx' 形式（role 加粗、content 正常）"""
    role = section.get("role", "当事人")
    content = section.get("content", "")
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(24)  # 首行缩进 2 字符
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.6
    label_run = p.add_run(f"{role}：")
    _set_run_font(label_run, size=12, bold=True)
    content_run = p.add_run(content)
    _set_run_font(content_run, size=12)


def _render_heading(doc: Document, section: dict):
    """节标题（如"诉讼请求"）：三号字、加粗"""
    text = section.get("content", "")
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = 1.5
    run = p.add_run(text)
    _set_run_font(run, size=15, bold=True, color=BLACK)


def _render_numbered(doc: Document, section: dict):
    """中文编号列表项：number 加粗，content 正常"""
    number = section.get("number", "●")
    content = section.get("content", "")
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(24)
    p.paragraph_format.line_spacing = 1.6
    p.paragraph_format.space_after = Pt(4)
    prefix_run = p.add_run(f"{number}、")
    _set_run_font(prefix_run, size=12, bold=True)
    body_run = p.add_run(content)
    _set_run_font(body_run, size=12)


def _render_paragraph(doc: Document, section: dict):
    """正文段落：默认首行缩进 2 字符、1.6 倍行距"""
    text = section.get("content", "")
    if not text:
        return
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(24)
    p.paragraph_format.line_spacing = 1.6
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    _set_run_font(run, size=12)


def _render_center(doc: Document, section: dict):
    """居中行（用于"此致"、法院名等）"""
    text = section.get("content", "")
    bold = section.get("bold", False)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.6
    run = p.add_run(text)
    _set_run_font(run, size=12, bold=bold)


def _render_signature(doc: Document, section: dict):
    """落款行：右对齐"""
    text = section.get("content", "")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.6
    run = p.add_run(text)
    _set_run_font(run, size=12)


def _render_blank(doc: Document, section: dict):
    """空行占位"""
    spacing = max(1, min(3, int(section.get("spacing", 1))))
    for _ in range(spacing):
        doc.add_paragraph()


def _render_notice(doc: Document, section: dict):
    """提示信息：斜体（与正文区分）"""
    text = section.get("content", "")
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(24)
    p.paragraph_format.line_spacing = 1.6
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    _set_run_font(run, size=11, italic=True, color=BLACK)


# section type → 渲染函数映射
_RENDERERS = {
    "party": _render_party,
    "heading": _render_heading,
    "numbered": _render_numbered,
    "paragraph": _render_paragraph,
    "center": _render_center,
    "signature": _render_signature,
    "blank": _render_blank,
    "notice": _render_notice,
}


# ========== 入口 ==========

def generate_docx_from_json(doc_data: dict) -> bytes:
    """
    基于结构化 JSON 生成专业排版的 .docx 文件

    :param doc_data: {"title": str, "sections": [{type, ...}, ...]}
    :return: .docx 文件的字节流
    """
    title = doc_data.get("title", "法律文书")
    sections = doc_data.get("sections", [])
    if not sections:
        raise BadRequestError("文书内容为空，无法生成 Word 文件")

    doc = Document()
    _set_default_style(doc)

    # 渲染标题
    _render_title(doc, title)

    # 按 sections 顺序渲染
    for section in sections:
        stype = section.get("type", "paragraph")
        renderer = _RENDERERS.get(stype, _render_paragraph)
        renderer(doc, section)

    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def format_ai_content_docx(doc_type: str, content: str) -> bytes:
    """
    对 AI 生成的文书纯文本做智能排版，生成专业排版的 .docx 文件

    兼容旧逻辑：如果前端传来的是纯文本（非 JSON），尝试用正则解析；
    但新流程下应该传 JSON，此函数作为兜底。

    :param doc_type: 文书类型
    :param content: AI 生成的文书全文（纯文本 or JSON）
    :return: .docx 文件的字节流
    """
    import json as _json
    import re as _re

    if not content or not content.strip():
        raise BadRequestError("文书内容为空，无法生成 Word 文件")

    # 优先尝试解析为 JSON
    parsed = None
    try:
        parsed = _json.loads(content.strip())
    except (ValueError, _json.JSONDecodeError):
        pass

    if parsed and isinstance(parsed, dict) and parsed.get("title") and parsed.get("sections"):
        return generate_docx_from_json(parsed)

    # 降级：纯文本 → 包装成简单 JSON 结构
    lines = content.split("\n")
    sections = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            sections.append({"type": "blank", "spacing": 1})
        elif len(stripped) <= 10 and not stripped.endswith(("。", "，", "；")):
            sections.append({"type": "heading", "content": stripped})
        else:
            sections.append({"type": "paragraph", "content": stripped})

    return generate_docx_from_json({"title": doc_type, "sections": sections})


def generate_document_docx(doc_type: str, form_data: dict) -> bytes:
    """
    按文书类型用模板生成 docx（降级方案，不用 AI）

    :param doc_type: 文书类型
    :param form_data: 用户填写的表单数据
    :return: .docx 文件的字节流
    """
    from app.services.document_service import _fallback_generate
    doc_data = _fallback_generate(doc_type, form_data)
    return generate_docx_from_json(doc_data)


def sanitize_document_filename(doc_type: str) -> str:
    """生成下载文件名：<文书类型>_<时间戳>.docx"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{doc_type}_{timestamp}.docx"
