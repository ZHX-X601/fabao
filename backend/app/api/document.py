"""
文书生成接口
"""

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import BadRequestError, NotFoundError
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentGenerateRequest, DocumentOut
from app.services.document_docx_service import (
    format_ai_content_docx,
    generate_docx_from_json,
    generate_document_docx,
    sanitize_document_filename,
)
from app.services.document_service import generate_document
from app.utils.response import ok

router = APIRouter(prefix="/documents")


class DownloadRequest(BaseModel):
    """文书下载请求体：传入结构化文书 JSON，后端直接排版生成 docx"""

    doc_data: str  # JSON 字符串，格式：{"title": str, "sections": [{type, ...}, ...]}
    doc_type: str  # 文书类型（用于文件名和降级）


@router.post("/generate", summary="生成法律文书")
async def generate(
    body: DocumentGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    提交表单数据生成文书

    流程：调用 FastGPT / 本地模板生成结构化 JSON -> 保存生成记录 -> 返回记录
    generated_content 字段存储的是 JSON 字符串（含 title + sections 数组）
    """
    doc_data = await generate_document(body.doc_type, body.form_data)
    # 将结构化 JSON 序列化为字符串存储
    content_json = json.dumps(doc_data, ensure_ascii=False)

    document = Document(
        user_id=current_user.id,
        doc_type=body.doc_type,
        form_data=body.form_data,
        generated_content=content_json,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return ok(DocumentOut.model_validate(document))


@router.get("/list", summary="获取当前用户的文书历史列表")
def list_documents(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """按创建时间倒序返回当前用户的全部文书记录"""
    documents = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return ok([DocumentOut.model_validate(d) for d in documents])


@router.get("/{document_id}", summary="获取某条文书记录")
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取指定文书记录详情
    :raises NotFoundError: 记录不存在或不属于当前用户
    """
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if document is None:
        raise NotFoundError("文书记录不存在")
    return ok(DocumentOut.model_validate(document))


@router.post("/download", summary="下载文书为 Word 文件")
async def download_document(
    body: DownloadRequest,
    current_user: User = Depends(get_current_user),
):
    """
    根据结构化文书 JSON 生成专业排版的 Word（.docx）文件并返回下载

    流程：解析 doc_data JSON -> generate_docx_from_json 确定性排版 ->
    以流方式返回（文件名用 RFC 5987 UTF-8 编码，中文不乱码）
    """
    # 解析 doc_data JSON
    try:
        doc_data = json.loads(body.doc_data)
    except (json.JSONDecodeError, ValueError):
        raise BadRequestError("doc_data 不是合法的 JSON 格式")

    if not doc_data.get("title") or not doc_data.get("sections"):
        raise BadRequestError("doc_data 缺少 title 或 sections 字段")

    docx_bytes = generate_docx_from_json(doc_data)

    filename = sanitize_document_filename(body.doc_type)
    from urllib.parse import quote
    encoded_filename = quote(filename)

    return StreamingResponse(
        iter([docx_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": (
                f"attachment; filename=\"report.docx\"; "
                f"filename*=UTF-8''{encoded_filename}"
            ),
            "Content-Length": str(len(docx_bytes)),
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
