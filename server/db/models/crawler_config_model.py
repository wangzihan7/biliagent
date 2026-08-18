#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 爬虫频控配置

from sqlalchemy import Column, Integer, Boolean, DateTime, func
from server.db.base import Base


class CrawlerConfigModel(Base):
    """全局爬虫频控配置（单行）"""

    __tablename__ = "crawler_config"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    use_rate_limit = Column(Boolean, default=True, comment="是否启用频控")
    max_concurrency = Column(Integer, default=2, comment="最大并发（协程）")
    min_interval_ms = Column(Integer, default=500, comment="最小请求间隔 ms")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
