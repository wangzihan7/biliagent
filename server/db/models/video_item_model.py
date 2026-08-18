#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 视频基础信息模型

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from server.db.base import Base


class VideoItemModel(Base):
    """视频基础信息"""

    __tablename__ = "video_item"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    aid = Column(String(50), unique=True, nullable=True, index=True, comment="视频AID")
    bvid = Column(String(50), unique=True, nullable=True, index=True, comment="视频BVID")
    title = Column(String(255), comment="标题")
    author = Column(String(100), comment="作者")
    url = Column(String(255), comment="链接")
    description = Column(Text, comment="描述")
    tags = Column(Text, comment="标签")
    play = Column(Integer, default=0, comment="播放数")
    favorite_count = Column(Integer, default=0, comment="收藏数")
    comment_count = Column(Integer, default=0, comment="评论数(实际抓取)")
    danmaku_count = Column(Integer, default=0, comment="弹幕数(实际抓取)")
    pubdate = Column(DateTime, comment="发布时间")
    dataset_id = Column(String(50), index=True, comment="关联数据集ID")
    keyword = Column(String(100), comment="关联关键词")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "aid": self.aid,
            "bvid": self.bvid,
            "title": self.title,
            "author": self.author,
            "url": self.url,
            "description": self.description,
            "tags": self.tags,
            "play": self.play,
            "favorite_count": self.favorite_count,
            "comment_count": self.comment_count,
            "danmaku_count": self.danmaku_count,
            "pubdate": str(self.pubdate) if self.pubdate else None,
            "keyword": self.keyword,
            "created_at": str(self.created_at) if self.created_at else None,
        }
