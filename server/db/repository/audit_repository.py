#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 查询/爬虫审计日志

from typing import List, Optional
from sqlalchemy.orm import Session
from server.db.models.query_log_model import QueryLogModel
from server.db.models.crawl_log_model import CrawlLogModel


class AuditRepository:
    """审计日志的增/查"""

    @staticmethod
    def log_query(
        db: Session,
        user_id: str,
        topic_id: Optional[str],
        conversation_id: Optional[str],
        query_text: Optional[str],
        status: str = "success",
        error_msg: Optional[str] = None,
    ) -> QueryLogModel:
        record = QueryLogModel(
            user_id=user_id,
            topic_id=topic_id,
            conversation_id=conversation_id,
            query_text=(query_text or "")[:500],
            status=status,
            error_msg=(error_msg or "")[:500] if error_msg else None,
        )
        db.add(record)
        db.flush()
        return record

    @staticmethod
    def log_crawl(
        db: Session,
        user_id: str,
        task_id: Optional[str],
        keyword: Optional[str],
        status: str = "success",
        error_msg: Optional[str] = None,
        video_count: int = 0,
        comment_count: int = 0,
        danmaku_count: int = 0,
    ) -> CrawlLogModel:
        record = CrawlLogModel(
            user_id=user_id,
            task_id=task_id,
            keyword=keyword,
            status=status,
            error_msg=(error_msg or "")[:500] if error_msg else None,
            video_count=video_count,
            comment_count=comment_count,
            danmaku_count=danmaku_count,
        )
        db.add(record)
        db.flush()
        return record

    @staticmethod
    def list_query_logs(db: Session, user_id: Optional[str] = None, limit: int = 50) -> List[QueryLogModel]:
        q = db.query(QueryLogModel).order_by(QueryLogModel.created_at.desc())
        if user_id:
            q = q.filter(QueryLogModel.user_id == user_id)
        return q.limit(limit).all()

    @staticmethod
    def list_crawl_logs(db: Session, user_id: Optional[str] = None, limit: int = 50) -> List[CrawlLogModel]:
        q = db.query(CrawlLogModel).order_by(CrawlLogModel.created_at.desc())
        if user_id:
            q = q.filter(CrawlLogModel.user_id == user_id)
        return q.limit(limit).all()

    @staticmethod
    def list_crawl_logs_with_total(
        db: Session, user_id: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[CrawlLogModel], int]:
        q = db.query(CrawlLogModel).order_by(CrawlLogModel.created_at.desc())
        if user_id:
            q = q.filter(CrawlLogModel.user_id == user_id)
        total = q.count()
        logs = q.offset(offset).limit(limit).all()
        return logs, total
