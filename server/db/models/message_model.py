#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 消息历史模型

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum, func
from server.db.base import Base


class MessageModel(Base):
    """消息历史模型"""
    __tablename__ = 'message_history'
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='消息ID')
    conversation_id = Column(String(50), ForeignKey('conversation_info.conversation_id', ondelete='CASCADE'),
                            nullable=False, index=True, comment='会话ID')
    user_id = Column(String(50), nullable=False, index=True, comment='用户ID')
    message_id = Column(String(50), unique=True, comment='消息唯一标识')
    role = Column(Enum('user', 'assistant', 'system'), nullable=False, comment='角色类型')
    content = Column(Text, nullable=False, comment='消息内容')
    meta_data = Column(JSON, comment='元数据')
    create_time = Column(DateTime, server_default=func.now(), index=True, comment='创建时间')
    
    def __repr__(self):
        return f"<Message(message_id='{self.message_id}', role='{self.role}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'message_id': self.message_id,
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'role': self.role,
            'content': self.content,
            'metadata': self.meta_data,
            'create_time': str(self.create_time) if self.create_time else None
        }
