from typing import Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    user_name: str = Field(..., description="用户名")
    email: Optional[str] = Field(None, description="邮箱，可选")
    password: str = Field(..., description="密码")
    role: str = Field("user", description="角色: user/admin")


class BasicUserCreate(BaseModel):
    user_name: str = Field(..., description="用户名")
    email: Optional[str] = Field(None, description="邮箱，可选")


class UserResponse(BaseModel):
    user_id: str
    user_name: str
    email: Optional[str]
    role: str
    create_time: str

    class Config:
        from_attributes = True


class UserLoginRequest(BaseModel):
    user_name: str
    password: str


class UserLoginResponse(BaseModel):
    user_id: str
    user_name: str
    role: str
    token: str


class AdminResetPasswordRequest(BaseModel):
    """管理员重置用户密码请求"""

    new_password: str = Field(..., min_length=6, description="新密码，至少 6 位")


class UpdateProfileRequest(BaseModel):
    """用户自助修改个人信息"""

    email: Optional[str] = Field(None, description="新的邮箱/账号")
    old_password: Optional[str] = Field(None, description="旧密码，用于验证")
    new_password: Optional[str] = Field(None, min_length=6, description="新密码，至少 6 位")
