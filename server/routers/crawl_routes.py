from typing import Optional, List

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from server.db.session import get_db_session
from server.routers.deps import get_current_user
from server.schemas.dataset import CrawlRequest, CrawlTaskResponse
from server.services import crawl_service

router = APIRouter(prefix="/api/v1", tags=["crawl"])


@router.post(
    "/crawl",
    response_model=CrawlTaskResponse,
    summary="触发小规模抓取并写入数据库",
)
async def trigger_crawl(
    req: CrawlRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    task = crawl_service.create_crawl_task(
        db=db,
        user_id=current_user.user_id,
        keyword=req.keyword,
        page=req.page,
        max_items=req.max_items,
        dataset_name=req.dataset_name,
        max_comments=req.max_comments,
        max_comment_pages=req.max_comment_pages,
        max_replies=req.max_replies,
        max_danmaku=req.max_danmaku,
    )
    background_tasks.add_task(
        crawl_service.run_crawl_task,
        task_id=task.task_id,
        user_id=current_user.user_id,
        keyword=req.keyword,
        page=req.page,
        max_items=task.max_items,
        dataset_name=req.dataset_name,
        max_comments=req.max_comments,
        max_comment_pages=req.max_comment_pages,
        max_replies=req.max_replies,
        max_danmaku=req.max_danmaku,
    )
    return task


@router.get(
    "/crawl/tasks",
    response_model=List[CrawlTaskResponse],
    summary="查询抓取任务列表",
)
def list_crawl_tasks(
    keyword: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db_session),
):
    return crawl_service.list_crawl_tasks(db, keyword=keyword, limit=limit)
