from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from server.db.session import get_db_session
from server.routers.deps import get_current_user, get_current_admin
from server.schemas.log import QueryLogItem, PaginatedCrawlLogResponse
from server.services import log_service

router = APIRouter(prefix="/api/v1", tags=["logs"])


@router.get("/admin/query-logs", response_model=list[QueryLogItem], summary="查询日志（admin）")
def list_query_logs(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
):
    return log_service.list_admin_query_logs(db, limit=limit)


@router.get("/admin/crawl-logs", response_model=PaginatedCrawlLogResponse, summary="爬虫日志（admin）")
def list_crawl_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
):
    return log_service.list_admin_crawl_logs(db, limit=limit, offset=offset)


@router.get("/logs/query", response_model=list[QueryLogItem], summary="我的查询日志")
def list_my_query_logs(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return log_service.list_my_query_logs(db, user_id=current_user.user_id, limit=limit)


@router.get("/logs/crawl", response_model=PaginatedCrawlLogResponse, summary="我的爬虫日志")
def list_my_crawl_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return log_service.list_my_crawl_logs(
        db, user_id=current_user.user_id, limit=limit, offset=offset
    )
