"""
文件读取工具：解析上传的 .docx / .pdf 合同文件并提取纯文本
"""

import os

import PyPDF2
from docx import Document as DocxDocument

from app.core.exceptions import BadRequestError

# 允许上传的文件后缀
ALLOWED_SUFFIXES = {".docx", ".pdf"}


def check_file_suffix(file_name: str) -> str:
    """
    校验上传文件的后缀是否受支持

    :param file_name: 原始文件名
    :return: 小写后缀（如 ".docx"）
    :raises BadRequestError: 后缀不受支持
    """
    suffix = os.path.splitext(file_name)[1].lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise BadRequestError("仅支持 .docx 或 .pdf 格式的合同文件")
    return suffix


def extract_text_from_docx(file_path: str) -> str:
    """
    从 Word（.docx）文件中提取文本

    同时读取段落与表格单元格内容，保证合同中的条款表格不丢失
    """
    doc = DocxDocument(file_path)
    lines: list[str] = []

    # 读取所有段落文本
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            lines.append(text)

    # 读取所有表格（按行拼接单元格）
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                lines.append(" | ".join(cells))

    return "\n".join(lines)


def extract_text_from_pdf(file_path: str) -> str:
    """
    从 PDF 文件中提取文本

    :raises BadRequestError: PDF 为扫描件/加密文件等无法解析的情况
    """
    try:
        reader = PyPDF2.PdfReader(file_path)
        # PDF 已加密时先尝试用空密码解密（仅限无口令的权限加密）
        if reader.is_encrypted:
            reader.decrypt("")
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()
    except BadRequestError:
        raise
    except Exception as exc:  # noqa: BLE001 解析失败统一转成业务异常
        raise BadRequestError(f"PDF 文件解析失败：{exc}") from exc


def extract_text(file_path: str, file_name: str) -> str:
    """
    文件解析统一入口：根据后缀分发到对应解析器

    :param file_path: 服务器上的文件存储路径
    :param file_name: 原始文件名（用于判断后缀）
    :return: 提取出的纯文本
    """
    suffix = check_file_suffix(file_name)
    if suffix == ".docx":
        text = extract_text_from_docx(file_path)
    else:
        text = extract_text_from_pdf(file_path)

    # 文本过短视为无效合同文件，提示用户
    if not text or len(text.strip()) < 20:
        raise BadRequestError("未能从文件中提取到有效文本，请确认上传的是内容完整的合同文件")
    return text
