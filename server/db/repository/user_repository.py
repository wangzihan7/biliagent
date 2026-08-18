#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 用户数据访问层（现在以“账号”而非邮箱作为登录标识）

from typing import Optional, List
from sqlalchemy.orm import Session
from server.db.models.user_model import UserModel
import uuid
import hashlib


class UserRepository:
    """用户数据访问类"""

    @staticmethod
    def _hash_password(password: str) -> str:
        """简单密码哈希（后续可替换为更安全算法）"""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @staticmethod
    def create_user(
        db: Session,
        user_name: str,
        account: Optional[str] = None,
        password: Optional[str] = None,
        role: str = "user",
    ) -> UserModel:
        """创建用户

        说明：
        - account 作为登录账号，对应到 UserModel.email 字段存储；
        - user_name 作为昵称显示。
        """
        user_id = str(uuid.uuid4())
        password_hash = (
            UserRepository._hash_password(password) if password is not None else None
        )
        user = UserModel(
            user_id=user_id,
            user_name=user_name,
            email=account,
            password_hash=password_hash,
            role=role,
        )
        db.add(user)
        db.flush()
        return user

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[UserModel]:
        """根据用户ID获取用户"""
        return (
            db.query(UserModel)
            .filter(
                UserModel.user_id == user_id,
                UserModel.is_active == True,
            )
            .first()
        )

    @staticmethod
    def get_user_by_name(db: Session, user_name: str) -> Optional[UserModel]:
        """根据用户名获取用户（用于用户名登录）"""
        return (
            db.query(UserModel)
            .filter(
                UserModel.user_name == user_name,
                UserModel.is_active == True,
            )
            .first()
        )

    @staticmethod
    def get_user_by_account(db: Session, account: str) -> Optional[UserModel]:
        """根据账号获取用户"""
        return (
            db.query(UserModel)
            .filter(
                UserModel.email == account,
                UserModel.is_active == True,
            )
            .first()
        )

    @staticmethod
    def get_user_by_account_and_password(
        db: Session, account: str, password: str
    ) -> Optional[UserModel]:
        """根据账号和密码获取用户（登录用）"""
        password_hash = UserRepository._hash_password(password)
        return (
            db.query(UserModel)
            .filter(
                UserModel.email == account,
                UserModel.password_hash == password_hash,
                UserModel.is_active == True,
            )
            .first()
        )

    @staticmethod
    def get_user_by_name_and_password(
        db: Session, user_name: str, password: str
    ) -> Optional[UserModel]:
        """根据用户名和密码获取用户（登录用）"""
        password_hash = UserRepository._hash_password(password)
        return (
            db.query(UserModel)
            .filter(
                UserModel.user_name == user_name,
                UserModel.password_hash == password_hash,
                UserModel.is_active == True,
            )
            .first()
        )

    @staticmethod
    def list_users(db: Session, skip: int = 0, limit: int = 100) -> List[UserModel]:
        """获取用户列表"""
        return (
            db.query(UserModel)
            .filter(UserModel.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def update_user(
        db: Session,
        user_id: str,
        user_name: Optional[str] = None,
        account: Optional[str] = None,
        password: Optional[str] = None,
        role: Optional[str] = None,
    ) -> Optional[UserModel]:
        """更新用户信息"""
        user = UserRepository.get_user_by_id(db, user_id)
        if not user:
            return None

        if user_name:
            user.user_name = user_name
        if account:
            user.email = account
        if password is not None:
            user.password_hash = UserRepository._hash_password(password)
        if role is not None:
            user.role = role

        db.flush()
        return user

    @staticmethod
    def delete_user(db: Session, user_id: str) -> bool:
        """删除用户(软删)"""
        user = UserRepository.get_user_by_id(db, user_id)
        if not user:
            return False

        user.is_active = False
        db.flush()
        return True
