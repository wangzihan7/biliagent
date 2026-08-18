#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 查询日志

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from server.db.base import Base


class QueryLogModel(Base):
    """记录用户查询/聊天请求"""

    __tablename__ = "query_log"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    user_id = Column(String(50), index=True, nullable=False)
    topic_id = Column(String(50), index=True, nullable=True)
    conversation_id = Column(String(50), index=True, nullable=True)
    status = Column(String(20), default="success", comment="success/failed")
    error_msg = Column(String(500), nullable=True, comment="错误信息")
    query_text = Column(Text, nullable=True, comment="用户问题（可截断）")
    created_at = Column(DateTime, server_default=func.now(), index=True, comment="创建时间")
