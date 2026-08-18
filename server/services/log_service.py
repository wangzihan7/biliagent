from typing import List

from sqlalchemy.orm import Session

from server.db.repository.audit_repository import AuditRepository
from server.schemas.log import QueryLogItem, CrawlLogItem, PaginatedCrawlLogResponse


def list_admin_query_logs(db: Session, limit: int) -> List[QueryLogItem]:
    logs = AuditRepository.list_query_logs(db, user_id=None, limit=limit)
    return [
        QueryLogItem(
            user_id=l.user_id,
            topic_id=l.topic_id,
            conversation_id=l.conversation_id,
            status=l.status,
            error_msg=l.error_msg,
            query_text=l.query_text,
            created_at=str(l.created_at),
        )
        for l in logs
    ]


def list_admin_crawl_logs(db: Session, limit: int, offset: int) -> PaginatedCrawlLogResponse:
    logs, total = AuditRepository.list_crawl_logs_with_total(db, user_id=None, limit=limit, offset=offset)
    return PaginatedCrawlLogResponse(
        items=[
            CrawlLogItem(
                user_id=l.user_id,
                task_id=l.task_id,
                keyword=l.keyword,
                status=l.status,
                error_msg=l.error_msg,
                video_count=l.video_count,
                comment_count=l.comment_count,
                danmaku_count=l.danmaku_count,
                created_at=str(l.created_at),
            )
            for l in logs
        ],
        total=total,
    )


def list_my_query_logs(db: Session, user_id: str, limit: int) -> List[QueryLogItem]:
    logs = AuditRepository.list_query_logs(db, user_id=user_id, limit=limit)
    return [
        QueryLogItem(
            user_id=l.user_id,
            topic_id=l.topic_id,
            conversation_id=l.conversation_id,
            status=l.status,
            error_msg=l.error_msg,
            query_text=l.query_text,
            created_at=str(l.created_at),
        )
        for l in logs
    ]


def list_my_crawl_logs(db: Session, user_id: str, limit: int, offset: int) -> PaginatedCrawlLogResponse:
    logs, total = AuditRepository.list_crawl_logs_with_total(db, user_id=user_id, limit=limit, offset=offset)
    return PaginatedCrawlLogResponse(
        items=[
            CrawlLogItem(
                user_id=l.user_id,
                task_id=l.task_id,
                keyword=l.keyword,
                status=l.status,
                error_msg=l.error_msg,
                video_count=l.video_count,
                comment_count=l.comment_count,
                danmaku_count=l.danmaku_count,
                created_at=str(l.created_at),
            )
            for l in logs
        ],
        total=total,
    )

