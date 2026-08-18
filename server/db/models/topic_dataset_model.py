#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 课题-数据集 关联表

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from server.db.base import Base


class TopicDatasetModel(Base):
    """课题与数据集关联"""

    __tablename__ = "topic_dataset_map"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    topic_id = Column(String(50), ForeignKey("topic.topic_id", ondelete="CASCADE"), index=True, nullable=False)
    dataset_id = Column(String(50), ForeignKey("dataset.dataset_id", ondelete="CASCADE"), index=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
