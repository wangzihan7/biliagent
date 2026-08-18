#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 会话模型

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from server.db.base import Base


class ConversationModel(Base):
    """会话模型"""
    __tablename__ = 'conversation_info'
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='会话ID')
    conversation_id = Column(String(50), unique=True, nullable=False, index=True, comment='会话唯一标识')
    user_id = Column(String(50), ForeignKey('user_info.user_id', ondelete='CASCADE'), 
                     nullable=False, index=True, comment='用户ID')
    conversation_name = Column(String(200), default='B站数据分析对话', comment='会话名称')
    create_time = Column(DateTime, server_default=func.now(), comment='创建时间')
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    is_delete = Column(Boolean, default=False, comment='是否删除')
    
    def __repr__(self):
        return f"<Conversation(conversation_id='{self.conversation_id}', user_id='{self.user_id}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'conversation_name': self.conversation_name,
            'create_time': str(self.create_time) if self.create_time else None,
            'update_time': str(self.update_time) if self.update_time else None,
            'is_delete': self.is_delete
        }
