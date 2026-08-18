#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 课题-会话 关联表

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from server.db.base import Base


class TopicConversationModel(Base):
    """课题与会话关联（不改动原表结构，单独建映射）"""

    __tablename__ = "topic_conversation_map"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    topic_id = Column(String(50), ForeignKey("topic.topic_id", ondelete="CASCADE"), index=True, nullable=False)
    conversation_id = Column(String(50), ForeignKey("conversation_info.conversation_id", ondelete="CASCADE"), index=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
