"""
合同审查接口：上传合同 / 执行审查 / 历史列表
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.contract import Contract
from app.models.user import User
from app.schemas.contract import ContractOut
from app.services.contract_service import review_contract
from app.utils.file_handler import check_file_suffix, extract_text
from app.utils.response import ok

router = APIRouter(prefix="/contracts")


@router.post("/upload", summary="上传合同文件")
async def upload_contract(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    上传合同文件（.docx / .pdf）

    流程：校验后缀 -> 落盘保存（UUID 重命名避免重名/路径注入）-> 提取文本 -> 建审查记录
    """
    # 1. 校验文件格式（不合法会抛 400）
    suffix = check_file_suffix(file.filename or "")

    # 2. 用 UUID 重命名后保存到上传目录，避免重名覆盖与特殊字符问题
    save_dir = Path(settings.UPLOAD_PATH)
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / f"{uuid.uuid4().hex}{suffix}"
    with open(save_path, "wb") as f:
        f.write(await file.read())

    # 3. 提取合同文本（解析失败会抛业务异常，此时文件已保存但记录不创建）
    text = extract_text(str(save_path), file.filename or "")

    # 4. 创建审查记录（review_result 暂为 NULL，等待执行审查）
    contract = Contract(
        user_id=current_user.id,
        file_name=file.filename or "未命名文件",
        file_path=str(save_path),
        original_text=text,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return ok(ContractOut.model_validate(contract))


@router.post("/review/{contract_id}", summary="执行合同审查")
def review(
    contract_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    对已上传的合同执行审查（每次调用都会重新审查并覆盖旧结果）

    :raises NotFoundError: 记录不存在或不属于当前用户
    """
    contract = (
        db.query(Contract)
        .filter(Contract.id == contract_id, Contract.user_id == current_user.id)
        .first()
    )
    if contract is None:
        raise NotFoundError("合同记录不存在")

    # 调用审查服务（当前为模拟实现），结果为可 JSON 化的字典，直接存 JSON 字段
    contract.review_result = review_contract(contract.original_text or "", contract.file_name)
    db.commit()
    db.refresh(contract)
    return ok(ContractOut.model_validate(contract))


@router.get("/list", summary="获取当前用户的审查历史列表")
def list_contracts(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """按创建时间倒序返回当前用户的全部合同审查记录"""
    contracts = (
        db.query(Contract)
        .filter(Contract.user_id == current_user.id)
        .order_by(Contract.created_at.desc())
        .all()
    )
    return ok([ContractOut.model_validate(c) for c in contracts])
