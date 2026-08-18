#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 代理与爬虫访问配置

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from server.db.base import Base


class ProxyConfigModel(Base):
    """代理配置（全局单行）"""

    __tablename__ = "proxy_config"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    use_proxy = Column(Boolean, default=True, comment="是否启用代理")
    extract_url = Column(String(500), nullable=True, comment="代理提取接口")
    refresh_interval_sec = Column(Integer, default=40, comment="代理刷新间隔秒")
    test_url = Column(String(500), nullable=True, comment="代理测试 URL")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
