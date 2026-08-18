#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 关键词提取数据访问层

from typing import List, Optional
from sqlalchemy.orm import Session
from server.db.models.keyword_model import KeywordExtractionModel
import uuid


class KeywordRepository:
    """关键词提取数据访问层"""
    
    @staticmethod
    def add_keyword_extraction(db: Session, conversation_id: str, user_id: str,
                              original_question: str, extracted_keywords: str) -> KeywordExtractionModel:
        """添加关键词提取记录"""
        extraction_id = str(uuid.uuid4())
        extraction = KeywordExtractionModel(
            extraction_id=extraction_id,
            conversation_id=conversation_id,
            user_id=user_id,
            original_question=original_question,
            extracted_keywords=extracted_keywords
        )
        db.add(extraction)
        db.flush()
        return extraction
    
    @staticmethod
    def get_conversation_keywords(db: Session, conversation_id: str, 
                                 limit: int = 50) -> List[KeywordExtractionModel]:
        """获取会话的关键词提取历史"""
        return db.query(KeywordExtractionModel).filter(
            KeywordExtractionModel.conversation_id == conversation_id
        ).order_by(KeywordExtractionModel.create_time.desc()).limit(limit).all()
    
