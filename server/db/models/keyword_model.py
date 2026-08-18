#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 关键词提取记录模型

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from server.db.base import Base


class KeywordExtractionModel(Base):
    """关键词提取记录模型"""
    __tablename__ = 'keyword_extraction'
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='记录ID')
    extraction_id = Column(String(50), unique=True, comment='提取记录唯一标识')
    conversation_id = Column(String(50), ForeignKey('conversation_info.conversation_id', ondelete='CASCADE'),
                            nullable=False, index=True, comment='会话ID')
    user_id = Column(String(50), nullable=False, index=True, comment='用户ID')
    original_question = Column(Text, nullable=False, comment='原始问题')
    extracted_keywords = Column(String(500), comment='提取的关键词')
    create_time = Column(DateTime, server_default=func.now(), index=True, comment='创建时间')
    
    def __repr__(self):
        return f"<KeywordExtraction(extraction_id='{self.extraction_id}', keywords='{self.extracted_keywords}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            'extraction_id': self.extraction_id,
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'original_question': self.original_question,
            'extracted_keywords': self.extracted_keywords,
            'create_time': str(self.create_time) if self.create_time else None
        }
