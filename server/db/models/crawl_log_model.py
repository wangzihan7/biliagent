#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 爬虫日志

from sqlalchemy import Column, Integer, String, DateTime, func
from server.db.base import Base


class CrawlLogModel(Base):
    """记录爬虫任务创建/结果"""

    __tablename__ = "crawl_log"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    user_id = Column(String(50), index=True, nullable=False)
    task_id = Column(String(50), index=True, nullable=True)
    keyword = Column(String(200), nullable=True)
    status = Column(String(20), default="success", comment="success/failed")
    error_msg = Column(String(500), nullable=True)
    video_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    danmaku_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now(), index=True, comment="创建时间")
