from typing import List

from sqlalchemy.orm import Session

from server.auth.jwt_utils import create_access_token, decode_token
from server.db.repository.user_repository import UserRepository
from server.exceptions import BadRequestError, UnauthorizedError, NotFoundError
from server.schemas.user import (
    UserCreate,
    BasicUserCreate,
    UserResponse,
    UserLoginRequest,
    UserLoginResponse,
    AdminResetPasswordRequest,
    UpdateProfileRequest,
)


def register_user(db: Session, user: UserCreate) -> UserResponse:
    if UserRepository.get_user_by_name(db, user.user_name):
        raise BadRequestError("用户名已被使用")
    if user.email and UserRepository.get_user_by_account(db, user.email):
        raise BadRequestError("邮箱已被使用")

    new_user = UserRepository.create_user(
        db,
        user_name=user.user_name,
        account=user.email,
        password=user.password,
        role=user.role,
    )
    db.commit()
    return UserResponse.model_validate(new_user)


def login_user(db: Session, login: UserLoginRequest) -> UserLoginResponse:
    user = UserRepository.get_user_by_name_and_password(
        db, login.user_name, login.password
    )
    if not user:
        raise UnauthorizedError("用户名或密码错误")

    return UserLoginResponse(
        user_id=user.user_id,
        user_name=user.user_name,
        role=user.role,
        token=create_access_token({"sub": user.user_id, "role": user.role}),
    )


def create_user_basic(db: Session, user: BasicUserCreate) -> UserResponse:
    new_user = UserRepository.create_user(
        db,
        user_name=user.user_name,
        account=user.email,
    )
    db.commit()
    return UserResponse.model_validate(new_user)


def get_user_from_token(db: Session, token: str):
    try:
        payload = decode_token(token)
    except Exception as exc:
        raise UnauthorizedError(f"Token 无效: {exc}")

    user_id = payload.get("sub")
    role = payload.get("role")
    user = UserRepository.get_user_by_id(db, user_id)
    if not user or user.role != role:
        raise ("用户不存在或角色不符")
    return user


def get_user_or_404(db: Session, user_id: str) -> UserResponse:
    user = UserRepository.get_user_by_id(db, user_id)
    if not user:
        raise NotFoundError("用户不存在")
    return UserResponse.model_validate(user)


def list_users(db: Session, skip: int, limit: int) -> List[UserResponse]:
    users = UserRepository.list_users(db, skip, limit)
    return [
        UserResponse(
            user_id=u.user_id,
            user_name=u.user_name,
            email=u.email,
            role=u.role,
            create_time=str(u.create_time),
        )
        for u in users
    ]


def reset_password(db: Session, user_id: str, req: AdminResetPasswordRequest) -> UserResponse:
    user = UserRepository.update_user(
        db,
        user_id=user_id,
        password=req.new_password,
    )
    if not user:
        raise NotFoundError("用户不存在")
    db.commit()
    return UserResponse.model_validate(user)


def update_profile(db: Session, user_id: str, req: UpdateProfileRequest) -> UserResponse:
    user = UserRepository.get_user_by_id(db, user_id)
    if not user:
        raise NotFoundError("用户不存在")

    # 邮箱变更时检查唯一
    new_email = None
    if req.email and req.email != user.email:
        if UserRepository.get_user_by_account(db, req.email):
            raise BadRequestError("邮箱已被使用")
        new_email = req.email

    # 密码变更需要旧密码校验
    new_password = None
    if req.new_password is not None:
        if not req.old_password:
            raise BadRequestError("旧密码不能为空")
        if UserRepository._hash_password(req.old_password) != user.password_hash:
            raise BadRequestError("旧密码不正确")
        new_password = req.new_password

    updated = UserRepository.update_user(
        db,
        user_id=user_id,
        account=new_email,
        password=new_password,
    )
    if not updated:
        raise NotFoundError("用户不存在")
    db.commit()
    return UserResponse.model_validate(updated)
