#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 爬虫任务模型

from sqlalchemy import Column, Integer, String, DateTime, func
from server.db.base import Base


class CrawlTaskModel(Base):
    """记录单次关键词抓取任务"""

    __tablename__ = "crawl_task"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    task_id = Column(String(50), unique=True, index=True, nullable=False, comment="任务UUID")
    keyword = Column(String(200), nullable=False, comment="抓取关键词")
    page = Column(Integer, default=1, comment="页数")
    max_items = Column(Integer, default=0, comment="每关键词抓取条数上限")
    status = Column(String(20), default="pending", comment="任务状态")
    video_count = Column(Integer, default=0, comment="视频数")
    comment_count = Column(Integer, default=0, comment="评论数")
    danmaku_count = Column(Integer, default=0, comment="弹幕数")
    data_path = Column(String(255), comment="数据文件路径(可选)")
    error_msg = Column(String(500), comment="错误信息")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
