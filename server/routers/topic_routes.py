from typing import Optional
import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from server.db.session import get_db_session
from server.routers.deps import get_current_user
from server.schemas.topic import (
    TopicCreate,
    TopicUpdate,
    TopicResponse,
    PaginatedTopicResponse,
    TopicDetailResponse,
    TopicConversationBind,
    TopicDatasetBind,
    TopicReportResponse,
    TopicReportTaskResponse,
)
from server.services import topic_service

router = APIRouter(prefix="/api/v1", tags=["topics"])


@router.post("/topics", response_model=TopicResponse, summary="创建课题")
def create_topic(
    req: TopicCreate,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return topic_service.create_topic(db, req, current_user)


@router.get("/topics", response_model=PaginatedTopicResponse, summary="课题列表")
def list_topics(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    keyword: Optional[str] = None,
    topic_type: Optional[str] = None,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return topic_service.list_topics(
        db=db,
        limit=limit,
        offset=offset,
        keyword=keyword,
        topic_type=topic_type,
        current_user=current_user,
    )


@router.get("/topics/{topic_id}", response_model=TopicDetailResponse, summary="课题详情（含会话/数据集）")
def topic_detail(
    topic_id: str,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return topic_service.topic_detail(db, topic_id, current_user)


@router.put("/topics/{topic_id}", response_model=TopicResponse, summary="更新课题")
def update_topic(
    topic_id: str,
    req: TopicUpdate,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return topic_service.update_topic(db, topic_id, req)


@router.delete("/topics/{topic_id}", summary="删除课题")
def delete_topic(
    topic_id: str,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    topic_service.delete_topic(db, topic_id)
    return {"success": True}


@router.post("/topics/{topic_id}/conversations", summary="课题绑定会话")
def bind_conversation_to_topic(
    topic_id: str,
    req: TopicConversationBind,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    topic_service.bind_conversation(db, topic_id, req, current_user)
    return {"success": True}


@router.post("/topics/{topic_id}/datasets", summary="课题绑定数据集")
def bind_dataset_to_topic(
    topic_id: str,
    req: TopicDatasetBind,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    topic_service.bind_dataset(db, topic_id, req, current_user)
    return {"success": True}


@router.get("/topics/{topic_id}/report", response_model=TopicReportResponse, summary="课题报告/可视化数据")
def topic_report(
    topic_id: str,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return topic_service.get_topic_report(db, topic_id, current_user)


@router.post(
    "/topics/{topic_id}/report/async",
    response_model=TopicReportTaskResponse,
    summary="异步生成课题报告",
)
def start_topic_report_async(
    topic_id: str,
    background_tasks: BackgroundTasks,
    force: bool = Query(False),
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    task = topic_service.create_topic_report_task(db, topic_id, current_user, force=force)
    if task.get("status") == "pending":
        background_tasks.add_task(
            topic_service.run_topic_report_task,
            task_id=task["task_id"],
        )
    return task


@router.get(
    "/topics/{topic_id}/report/async",
    response_model=TopicReportTaskResponse,
    summary="获取课题报告生成状态",
)
def get_topic_report_async(
    topic_id: str,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    task = topic_service.get_topic_report_task(db, topic_id, current_user)
    if not task:
        return {
            "task_id": "",
            "topic_id": topic_id,
            "status": "missing",
            "created_at": datetime.datetime.utcnow().isoformat(),
        }
    return task

@router.get(
    "/topics/{topic_id}/report.md",
    summary="课题报告 Markdown",
)
def topic_report_markdown(
    topic_id: str,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    md = topic_service.get_topic_report_markdown(db, topic_id, current_user)
    from fastapi.responses import PlainTextResponse

    return PlainTextResponse(md, media_type="text/markdown; charset=utf-8")
