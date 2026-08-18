#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 课题（Topic）模型

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from server.db.base import Base


class TopicModel(Base):
    """课题"""

    __tablename__ = "topic"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    topic_id = Column(String(50), unique=True, nullable=False, index=True, comment="课题UUID")
    user_id = Column(String(50), nullable=True, index=True, comment="创建用户ID")
    name = Column(String(200), nullable=False, comment="课题名称")
    topic_type = Column(String(100), nullable=True, comment="课题类型，如旅游攻略/话题分析等")
    description = Column(Text, nullable=True, comment="课题描述")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
