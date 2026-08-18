#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 数据集模型（轻量）

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from server.db.base import Base


class DatasetModel(Base):
    """关键词数据集元数据"""

    __tablename__ = "dataset"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    dataset_id = Column(String(50), unique=True, index=True, nullable=False, comment="数据集UUID")
    user_id = Column(String(50), nullable=True, index=True, comment="创建用户ID")
    name = Column(String(200), nullable=False, comment="数据集名称")
    keyword = Column(String(200), nullable=False, comment="关键词")
    task_id = Column(String(50), ForeignKey("crawl_task.task_id", ondelete="SET NULL"), comment="关联任务ID")
    video_count = Column(Integer, default=0, comment="视频数")
    comment_count = Column(Integer, default=0, comment="评论数")
    danmaku_count = Column(Integer, default=0, comment="弹幕数")
    data_path = Column(String(255), comment="数据文件路径(可选)")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
