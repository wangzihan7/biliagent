from typing import Optional, List

from sqlalchemy.orm import Session

from server.db.session import get_db
from server.db.repository.dataset_repository import DatasetRepository
from server.db.repository.audit_repository import AuditRepository
from server.schemas.dataset import CrawlTaskResponse
from server.exceptions import InternalError
from blibli_get import pipeline as bili_pipeline


def _to_task_response(task) -> CrawlTaskResponse:
    return CrawlTaskResponse(
        task_id=task.task_id,
        status=task.status,
        keyword=task.keyword,
        page=task.page,
        max_items=task.max_items,
        video_count=task.video_count,
        comment_count=task.comment_count,
        danmaku_count=task.danmaku_count,
        created_at=str(task.created_at),
        updated_at=str(task.updated_at),
    )


def create_crawl_task(
    db: Session,
    user_id: str,
    keyword: str,
    page: int,
    max_items: Optional[int],
    dataset_name: Optional[str],
    max_comments: Optional[int],
    max_comment_pages: Optional[int],
    max_replies: Optional[int],
    max_danmaku: Optional[int],
) -> CrawlTaskResponse:
    max_items_val = max_items or bili_pipeline.MAX_RESULTS_PER_KEYWORD
    task = DatasetRepository.create_task(
        db=db,
        keyword=keyword,
        page=page,
        max_items=max_items_val,
        status="running",
    )
    db.commit()
    return _to_task_response(task) 


async def run_crawl_task(
    task_id: str,
    user_id: str,
    keyword: str,
    page: int,
    max_items: int,
    dataset_name: Optional[str],
    max_comments: Optional[int],
    max_comment_pages: Optional[int],
    max_replies: Optional[int],
    max_danmaku: Optional[int],
) -> None:
    with get_db() as db:
        DatasetRepository.update_task(
            db=db,
            task_id=task_id,
            status="running",
        )
        db.commit()

        try:
            result = await bili_pipeline.crawl_to_db(
                [keyword],
                page=page,
                max_items=max_items,
                dataset_name=dataset_name or f"dataset-{keyword}-{task_id[:6]}",
                user_id=user_id,
                task_id=task_id,
                max_comments=max_comments,
                max_comment_pages=max_comment_pages,
                max_replies=max_replies,
                max_danmaku=max_danmaku,
            )
            DatasetRepository.update_task(
                db=db,
                task_id=task_id,
                status="success",
                video_count=result["videos"],
                comment_count=result["comments"],
                danmaku_count=result["danmaku"],
            )
            db.commit()
            AuditRepository.log_crawl(
                db=db,
                user_id=user_id,
                task_id=task_id,
                keyword=keyword,
                status="success",
                error_msg=None,
                video_count=result["videos"],
                comment_count=result["comments"],
                danmaku_count=result["danmaku"],
            )
            db.commit()
        except Exception as e:
            DatasetRepository.update_task(
                db=db,
                task_id=task_id,
                status="failed",
                error_msg=str(e)[:255],
            )
            db.commit()
            AuditRepository.log_crawl(
                db=db,
                user_id=user_id,
                task_id=task_id,
                keyword=keyword,
                status="failed",
                error_msg=str(e)[:255],
            )
            db.commit()
            raise InternalError(f"{str(e)}")


def list_crawl_tasks(
    db: Session,
    keyword: Optional[str],
    limit: int,
) -> List[CrawlTaskResponse]:
    tasks = DatasetRepository.list_tasks(db, keyword=keyword, limit=limit)
    return [_to_task_response(t) for t in tasks]
