#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 消息数据访问层

from typing import List, Optional, Dict
import json
from sqlalchemy.orm import Session
from server.db.models.message_model import MessageModel
import uuid


class MessageRepository:
    """消息数据访问层"""
    
    @staticmethod
    def add_message(db: Session, conversation_id: str, user_id: str,
                   role: str, content: str, metadata: Optional[Dict] = None) -> MessageModel:
        """添加消息"""
        message_id = str(uuid.uuid4())
        message = MessageModel(
            message_id=message_id,
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            content=content,
            meta_data=metadata
        )
        db.add(message)
        db.flush()
        db.refresh(message)
        return message
    
    @staticmethod
    def get_conversation_messages(db: Session, conversation_id: str, 
                                 limit: int = 100) -> List[MessageModel]:
        """获取会话的消息历史（取最新 N 条，再按时间正序返回）"""
        rows = (
            db.query(MessageModel)
            .filter(MessageModel.conversation_id == conversation_id)
            .order_by(MessageModel.create_time.desc(), MessageModel.id.desc())
            .limit(limit)
            .all()
        )
        return rows[::-1]
    
    @staticmethod
    def get_recent_messages(db: Session, conversation_id: str, 
                           limit: int = 10) -> List[MessageModel]:
        """获取最近的N条消息"""
        return db.query(MessageModel).filter(
            MessageModel.conversation_id == conversation_id
        ).order_by(MessageModel.create_time.desc(), MessageModel.id.desc()).limit(limit).all()[::-1]
    
    @staticmethod
    def get_message_by_id(db: Session, message_id: str) -> Optional[MessageModel]:
        """根据消息ID获取消息"""
        return db.query(MessageModel).filter(
            MessageModel.message_id == message_id
        ).first()

    @staticmethod
    def update_metadata(db: Session, message_id: str, metadata: Dict) -> Optional[MessageModel]:
        """更新消息的 metadata 字段（部分更新，保留原有键）"""
        message = db.query(MessageModel).filter(
            MessageModel.message_id == message_id
        ).first()
        if not message:
            return None
        base_meta = message.meta_data or {}
        if isinstance(base_meta, str):
            try:
                base_meta = json.loads(base_meta)
            except Exception:
                base_meta = {}
        if not isinstance(base_meta, dict):
            base_meta = {}
        new_meta = dict(base_meta)
        new_meta.update(metadata or {})
        message.meta_data = new_meta
        db.flush()
        db.refresh(message)
        return message
    
    @staticmethod
    def delete_conversation_messages(db: Session, conversation_id: str) -> int:
        """删除会话的所有消息"""
        count = db.query(MessageModel).filter(
            MessageModel.conversation_id == conversation_id
        ).delete()
        db.flush()
        return count
