"""
认证相关接口：注册 / 登录 / 获取当前用户信息
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import ConflictError, BadRequestError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import LoginOut, UserCreate, UserLogin, UserOut
from app.utils.response import ok

router = APIRouter(prefix="/auth")


@router.post("/register", summary="用户注册")
def register(body: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册

    流程：校验用户名/邮箱是否已被占用 -> 哈希密码 -> 落库 -> 返回用户信息
    """
    # 1. 检查用户名是否已存在
    if db.query(User).filter(User.username == body.username).first():
        raise ConflictError("用户名已被注册")
    # 2. 检查邮箱是否已存在
    if db.query(User).filter(User.email == body.email).first():
        raise ConflictError("邮箱已被注册")

    # 3. 创建用户（密码只存 bcrypt 哈希，绝不存明文）
    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)  # 刷新对象以获取数据库生成的 id / created_at

    return ok(UserOut.model_validate(user))


@router.post("/login", summary="用户登录")
def login(body: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录

    校验账号密码，签发 JWT 令牌
    :raises BadRequestError: 用户不存在或密码错误
    """
    # 1. 查询用户
    user = db.query(User).filter(User.username == body.username).first()
    # 2. 用户不存在或密码不匹配时，统一返回模糊提示（避免暴露账号是否存在）
    if user is None or not verify_password(body.password, user.hashed_password):
        raise BadRequestError("用户名或密码错误")

    # 3. 签发 JWT：载荷中包含用户 ID 与用户名
    token = create_access_token(user_id=user.id, username=user.username)
    return ok(
        LoginOut(
            access_token=token,
            token_type="bearer",
            user=UserOut.model_validate(user),
        )
    )


@router.get("/me", summary="获取当前用户信息")
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息（需在请求头携带 Authorization: Bearer <token>）"""
    return ok(UserOut.model_validate(current_user))
