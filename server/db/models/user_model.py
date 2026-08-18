#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 用户模型

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from server.db.base import Base


class UserModel(Base):
    """用户模型"""

    __tablename__ = "user_info"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    user_id = Column(String(50), unique=True, nullable=False, index=True, comment="用户唯一标识")
    # 这里作为展示名称（昵称），可以与登录账号不同
    user_name = Column(String(100), comment="用户昵称")
    # 历史字段名为 email，这里专门用于存储“登录账号”，不再表示邮箱含义
    email = Column(String(100), comment="登录账号")
    password_hash = Column(String(255), comment="密码哈希")
    role = Column(String(20), nullable=False, default="user", comment="用户角色: user/admin")
    auth_token = Column(String(255), nullable=True, comment="登录 Token")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    is_active = Column(Boolean, default=True, comment="是否激活")

    def __repr__(self) -> str:
        return f"<User(user_id='{self.user_id}', user_name='{self.user_name}')>"

    def to_dict(self) -> dict:
        """转换为字典，统一对外暴露 account 字段"""
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "account": self.email,
            # 向外兼容 email 字段，沿用历史“email”列作为账号
            "email": self.email,
            "role": self.role,
            "create_time": str(self.create_time) if self.create_time else None,
            "update_time": str(self.update_time) if self.update_time else None,
            "is_active": self.is_active,
        }
