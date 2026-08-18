from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from server.db.session import get_db_session
from server.routers.deps import get_current_user, get_current_admin
from server.services import auth_service
from server.schemas.user import (
    UserCreate,
    BasicUserCreate,
    UserResponse,
    UserLoginRequest,
    UserLoginResponse,
    AdminResetPasswordRequest,
    UpdateProfileRequest,
)

router = APIRouter(prefix="/api/v1", tags=["auth"])


@router.post("/users/register", response_model=UserResponse, summary="用户注册")
def register_user(user: UserCreate, db: Session = Depends(get_db_session)):
    return auth_service.register_user(db, user)


@router.post("/users/login", response_model=UserLoginResponse, summary="用户登录")
def login_user(login: UserLoginRequest, db: Session = Depends(get_db_session)):
    return auth_service.login_user(db, login)


@router.post("/users", response_model=UserResponse, summary="创建用户（兼容旧接口）")
def create_user_basic(user: BasicUserCreate, db: Session = Depends(get_db_session)):
    return auth_service.create_user_basic(db, user)


@router.get("/users/me", response_model=UserResponse, summary="获取当前用户信息")
def get_me(current_user=Depends(get_current_user)):
    return current_user.to_dict()


@router.put("/users/me", response_model=UserResponse, summary="修改本人信息（邮箱/密码）")
def update_me(
    req: UpdateProfileRequest,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return auth_service.update_profile(db, current_user.user_id, req)


@router.get("/users/{user_id}", response_model=UserResponse, summary="获取用户信息")
def get_user(user_id: str, db: Session = Depends(get_db_session)):
    return auth_service.get_user_or_404(db, user_id)


@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="获取用户列表（管理员）",
)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
):
    return auth_service.list_users(db, skip, limit)


@router.post(
    "/admin/users/{user_id}/reset-password",
    response_model=UserResponse,
    summary="管理员重置用户密码",
)
def admin_reset_user_password(
    user_id: str,
    req: AdminResetPasswordRequest,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
):
    return auth_service.reset_password(db, user_id, req)
