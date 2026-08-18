#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 爬虫频控配置访问

from typing import Optional
from sqlalchemy.orm import Session
from server.db.models.crawler_config_model import CrawlerConfigModel


class CrawlerConfigRepository:
    """单行频控配置"""

    @staticmethod
    def get_config(db: Session) -> CrawlerConfigModel:
        cfg = db.query(CrawlerConfigModel).order_by(CrawlerConfigModel.id.asc()).first()
        if not cfg:
            cfg = CrawlerConfigModel()
            db.add(cfg)
            db.flush()
        return cfg

    @staticmethod
    def update_config(
        db: Session,
        use_rate_limit: Optional[bool] = None,
        max_concurrency: Optional[int] = None,
        min_interval_ms: Optional[int] = None,
    ) -> CrawlerConfigModel:
        cfg = CrawlerConfigRepository.get_config(db)
        if use_rate_limit is not None:
            cfg.use_rate_limit = use_rate_limit
        if max_concurrency is not None:
            cfg.max_concurrency = max_concurrency
        if min_interval_ms is not None:
            cfg.min_interval_ms = min_interval_ms
        db.flush()
        return cfg
