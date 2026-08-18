from typing import Iterable, List, Optional

from sqlalchemy.orm import Session

from server.db.repository.conversation_repository import ConversationRepository
from server.db.repository.dataset_repository import DatasetRepository
from server.db.repository.topic_repository import TopicRepository
from server.schemas.dataset import DatasetResponse
from server.schemas.topic import (
    TopicResponse,
    TopicDetailResponse,
    TopicCreate,
    TopicUpdate,
    TopicConversationBind,
    TopicDatasetBind,
    PaginatedTopicResponse,
    TopicReportResponse,
)
from server.services.topic_report_service import (
    build_topic_report,
    build_llm_summary,
    render_topic_report_markdown,
)
from server.services import topic_report_task_service
from server.exceptions import ForbiddenError, NotFoundError


def get_topic_or_404(db: Session, topic_id: str):
    topic = TopicRepository.get_topic(db, topic_id)
    if not topic:
        raise NotFoundError("课题不存在")
    return topic


def assert_topic_access(topic, current_user):
    if getattr(current_user, "role", "") != "admin" and topic.user_id != current_user.user_id:
        raise ForbiddenError("无权访问该课题")


def to_topic_response(topic) -> TopicResponse:
    return TopicResponse(
        topic_id=topic.topic_id,
        name=topic.name,
        topic_type=topic.topic_type,
        description=topic.description,
        created_at=str(topic.created_at),
        updated_at=str(topic.updated_at),
    )


def build_topic_detail(
    topic,
    conversations: Iterable,
    datasets: Iterable,
) -> TopicDetailResponse:
    return TopicDetailResponse(
        topic_id=topic.topic_id,
        name=topic.name,
        topic_type=topic.topic_type,
        description=topic.description,
        created_at=str(topic.created_at),
        updated_at=str(topic.updated_at),
        conversations=[
            {
                "conversation_id": c.conversation_id,
                "user_id": c.user_id,
                "conversation_name": c.conversation_name,
                "topic_id": topic.topic_id,
                "create_time": str(c.create_time),
                "update_time": str(c.update_time),
            }
            for c in conversations
        ],
        datasets=[
            {
                "dataset_id": d.dataset_id,
                "name": d.name,
                "keyword": d.keyword,
                "task_id": d.task_id,
                "video_count": d.video_count,
                "comment_count": d.comment_count,
                "danmaku_count": d.danmaku_count,
                "data_path": d.data_path,
                "created_at": str(d.created_at),
                "updated_at": str(d.updated_at),
            }
            for d in datasets
        ],
    )


def create_topic(db: Session, req: TopicCreate, current_user) -> TopicResponse:
    topic = TopicRepository.create_topic(
        db=db,
        user_id=current_user.user_id,
        name=req.name,
        topic_type=req.topic_type,
        description=req.description,
    )
    db.commit()
    return to_topic_response(topic)


def list_topics(
    db: Session,
    limit: int,
    offset: int,
    keyword: Optional[str],
    topic_type: Optional[str],
    current_user,
) -> PaginatedTopicResponse:
    is_admin = getattr(current_user, "role", "") == "admin"
    topics, total = TopicRepository.list_topics_with_total(
        db,
        limit=limit,
        offset=offset,
        keyword=keyword,
        topic_type=topic_type,
        user_id=None if is_admin else current_user.user_id,
        only_owned=not is_admin,
    )
    return PaginatedTopicResponse(
        items=[to_topic_response(t) for t in topics],
        total=total,
    )


def topic_detail(db: Session, topic_id: str, current_user) -> TopicDetailResponse:
    topic = get_topic_or_404(db, topic_id)
    assert_topic_access(topic, current_user)
    conversations = TopicRepository.list_conversations(db, topic_id)
    datasets = TopicRepository.list_datasets(db, topic_id)
    return build_topic_detail(topic, conversations, datasets)


def update_topic(db: Session, topic_id: str, req: TopicUpdate) -> TopicResponse:
    topic = TopicRepository.update_topic(
        db=db,
        topic_id=topic_id,
        name=req.name,
        topic_type=req.topic_type,
        description=req.description,
    )
    if not topic:
        raise NotFoundError("课题不存在")
    db.commit()
    return to_topic_response(topic)


def delete_topic(db: Session, topic_id: str) -> None:
    ok = TopicRepository.delete_topic(db, topic_id)
    if not ok:
        raise NotFoundError("课题不存在")
    db.commit()


def bind_conversation(db: Session, topic_id: str, req: TopicConversationBind, current_user) -> None:
    topic = TopicRepository.get_topic(db, topic_id)
    if not topic:
        raise NotFoundError("课题不存在")
    if getattr(current_user, "role", "") != "admin" and topic.user_id != current_user.user_id:
        raise ForbiddenError("无权访问该课题")
    conv = ConversationRepository.get_conversation_by_id(db, req.conversation_id)
    if not conv:
        raise NotFoundError("会话不存在")
    TopicRepository.attach_conversation(db, topic_id, req.conversation_id)
    db.commit()


def bind_dataset(db: Session, topic_id: str, req: TopicDatasetBind, current_user) -> None:
    topic = TopicRepository.get_topic(db, topic_id)
    if not topic:
        raise NotFoundError("课题不存在")
    if getattr(current_user, "role", "") != "admin" and topic.user_id != current_user.user_id:
        raise ForbiddenError("无权访问该课题")
    dataset = DatasetRepository.get_by_dataset_id(db, req.dataset_id)
    if not dataset:
        raise NotFoundError("数据集不存在")
    TopicRepository.attach_dataset(db, topic_id, req.dataset_id)
    db.commit()


def get_topic_report(db: Session, topic_id: str, current_user) -> TopicReportResponse:
    topic = get_topic_or_404(db, topic_id)
    assert_topic_access(topic, current_user)
    report = build_topic_report(db, topic_id)
    llm_summary = build_llm_summary(report)
    return TopicReportResponse(
        topic_id=report["topic_id"],
        topic_name=report["topic_name"],
        summary=report["summary"],
        llm_summary=llm_summary or None,
        totals=report["totals"],
        top_tags=report["top_tags"],
        top_keywords=report["top_keywords"],
        sentiment=report["sentiment"],
        trend=report["trend"],
        key_answers=report.get("key_answers", []),
        charts=report.get("charts"),
    )


def get_topic_report_markdown(db: Session, topic_id: str, current_user) -> str:
    topic = get_topic_or_404(db, topic_id)
    assert_topic_access(topic, current_user)
    report = build_topic_report(db, topic_id)
    llm_summary = build_llm_summary(report)
    return render_topic_report_markdown(report, llm_summary or "")


def create_topic_report_task(
    db: Session, topic_id: str, current_user, force: bool = False
) -> dict:
    topic = get_topic_or_404(db, topic_id)
    assert_topic_access(topic, current_user)
    return topic_report_task_service.create_task(topic_id, force=force)


def get_topic_report_task(db: Session, topic_id: str, current_user) -> Optional[dict]:
    topic = get_topic_or_404(db, topic_id)
    assert_topic_access(topic, current_user)
    return topic_report_task_service.get_task_for_topic(topic_id)


def run_topic_report_task(task_id: str) -> None:
    topic_report_task_service.run_task(task_id)
