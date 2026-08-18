#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 会话数据访问层

from typing import List, Optional
from sqlalchemy.orm import Session
from server.db.models.conversation_model import ConversationModel
import uuid
from datetime import datetime


class ConversationRepository:
    """会话数据访问层"""
    
    @staticmethod
    def create_conversation(db: Session, user_id: str, 
                          conversation_name: str = "B站数据分析对话") -> ConversationModel:
        """创建会话"""
        conversation_id = str(uuid.uuid4())
        conversation = ConversationModel(
            conversation_id=conversation_id,
            user_id=user_id,
            conversation_name=conversation_name
        )
        db.add(conversation)
        db.flush()
        return conversation
    
    @staticmethod
    def get_conversation_by_id(db: Session, conversation_id: str) -> Optional[ConversationModel]:
        """根据会话ID获取会话"""
        return db.query(ConversationModel).filter(
            ConversationModel.conversation_id == conversation_id,
            ConversationModel.is_delete == False
        ).first()
    
    @staticmethod
    def get_user_conversations(db: Session, user_id: str, limit: int = 50) -> List[ConversationModel]:
        """获取用户的所有会话"""
        return db.query(ConversationModel).filter(
            ConversationModel.user_id == user_id,
            ConversationModel.is_delete == False
        ).order_by(ConversationModel.update_time.desc()).limit(limit).all()
    
    @staticmethod
    def update_conversation_name(db: Session, conversation_id: str, 
                                conversation_name: str) -> Optional[ConversationModel]:
        """更新会话名称"""
        conversation = ConversationRepository.get_conversation_by_id(db, conversation_id)
        if conversation:
            conversation.conversation_name = conversation_name
            conversation.update_time = datetime.now()
            db.flush()
        return conversation
    
    @staticmethod
    def delete_conversation(db: Session, conversation_id: str) -> bool:
        """删除会话(软删除)"""
        conversation = ConversationRepository.get_conversation_by_id(db, conversation_id)
        if conversation:
            conversation.is_delete = True
            conversation.update_time = datetime.now()
            db.flush()
            return True
        return False
    
    @staticmethod
    def touch_conversation(db: Session, conversation_id: str) -> None:
        """更新会话的最后修改时间"""
        conversation = ConversationRepository.get_conversation_by_id(db, conversation_id)
        if conversation:
            conversation.update_time = datetime.now()
            db.flush()
