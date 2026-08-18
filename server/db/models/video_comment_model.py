#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 视频评论模型

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from server.db.base import Base


class VideoCommentModel(Base):
    """视频评论"""

    __tablename__ = "video_comment"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    video_id = Column(Integer, ForeignKey("video_item.id", ondelete="CASCADE"), index=True, nullable=False)
    aid = Column(String(50), index=True, comment="视频AID")
    content = Column(Text, nullable=False, comment="评论内容")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
