import shutil
import io
import csv
import json
import datetime
from typing import Optional, List, Tuple

from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from server.db.repository.dataset_repository import DatasetRepository
from server.db.repository.video_repository import VideoRepository
from server.exceptions import ForbiddenError, NotFoundError
from bili_server.document_loader import DocumentLoader
from server.schemas.dataset import DatasetResponse, PaginatedDatasetResponse


def get_dataset_or_404(db: Session, dataset_id: str):
    dataset = DatasetRepository.get_by_dataset_id(db, dataset_id)
    if not dataset:
        raise NotFoundError("数据集不存在")
    return dataset


def list_datasets(
    db: Session,
    keyword: Optional[str],
    limit: int,
    offset: int,
    current_user,
) -> PaginatedDatasetResponse:
    is_admin = getattr(current_user, "role", "") == "admin"
    datasets, total = DatasetRepository.list_datasets_with_total(
        db,
        keyword=keyword,
        limit=limit,
        offset=offset,
        user_id=None if is_admin else current_user.user_id,
        only_owned=not is_admin,
    )
    return PaginatedDatasetResponse(
        items=[
            DatasetResponse(
                dataset_id=d.dataset_id,
                user_id=getattr(d, "user_id", None),
                name=d.name,
                keyword=d.keyword,
                task_id=d.task_id,
                video_count=d.video_count,
                comment_count=d.comment_count,
                danmaku_count=d.danmaku_count,
                data_path=d.data_path,
                created_at=str(d.created_at),
                updated_at=str(d.updated_at),
            )
            for d in datasets
        ],
        total=total,
    )


def get_dataset_detail(db: Session, dataset_id: str) -> DatasetResponse:
    dataset = DatasetRepository.get_by_dataset_id(db, dataset_id)
    if not dataset:
        raise NotFoundError("数据集不存在")
    return DatasetResponse(
        dataset_id=dataset.dataset_id,
        user_id=getattr(dataset, "user_id", None),
        name=dataset.name,
        keyword=dataset.keyword,
        task_id=dataset.task_id,
        video_count=dataset.video_count,
        comment_count=dataset.comment_count,
        danmaku_count=dataset.danmaku_count,
        data_path=dataset.data_path,
        created_at=str(dataset.created_at),
        updated_at=str(dataset.updated_at),
    )


def export_dataset(
    db: Session,
    dataset_id: str,
    format: str,
    current_user,
):
    dataset = get_dataset_or_404(db, dataset_id)
    if getattr(current_user, "role", "") != "admin" and dataset.user_id != current_user.user_id:
        raise ForbiddenError("无权导出该数据集")

    videos = VideoRepository.list_videos_by_dataset_id(db, dataset_id)

    if format == "jsonl":
        buffer = io.StringIO()
        for v in videos:
            comments = VideoRepository.list_video_comments(db, v.id)
            danmaku_rows = VideoRepository.list_video_danmaku(db, v.id)
            danmaku = [{"text": d[0], "progress_ms": d[1]} for d in danmaku_rows]
            record = {
                "dataset_id": v.dataset_id,
                "keyword": v.keyword,
                "aid": v.aid,
                "bvid": v.bvid,
                "title": v.title,
                "url": v.url,
                "author": v.author,
                "tags": v.tags,
                "play": v.play,
                "favorite_count": v.favorite_count,
                "comment_count": v.comment_count,
                "danmaku_count": v.danmaku_count,
                "pubdate": v.pubdate.isoformat() if isinstance(v.pubdate, datetime.datetime) else None,
                "comments": comments,
                "danmaku": danmaku,
            }
            buffer.write(json.dumps(record, ensure_ascii=False) + "\n")
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="text/plain; charset=utf-8")

    # CSV
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "dataset_id",
            "keyword",
            "aid",
            "bvid",
            "title",
            "url",
            "author",
            "tags",
            "play",
            "favorite_count",
            "comment_count",
            "danmaku_count",
            "pubdate",
            "comments",
            "danmaku",
        ]
    )
    for v in videos:
        comments = VideoRepository.list_video_comments(db, v.id)
        danmaku_rows = VideoRepository.list_video_danmaku(db, v.id)
        danmaku_strings = [f"{d[0]}@{d[1]}ms" for d in danmaku_rows]
        writer.writerow(
            [
                v.dataset_id,
                v.keyword,
                v.aid,
                v.bvid,
                v.title,
                v.url,
                v.author,
                v.tags,
                v.play,
                v.favorite_count,
                v.comment_count,
                v.danmaku_count,
                v.pubdate.isoformat() if isinstance(v.pubdate, datetime.datetime) else "",
                "; ".join(comments),
                "; ".join(danmaku_strings),
            ]
        )
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="text/csv; charset=utf-8")


def delete_dataset_and_related(db: Session, dataset_id: str) -> None:
    # 删除评论和弹幕
    video_ids = DatasetRepository.get_video_ids(db, dataset_id)
    if video_ids:
        DatasetRepository.delete_comments_by_video_ids(db, video_ids)
        DatasetRepository.delete_danmaku_by_video_ids(db, video_ids)

    # 删除视频
    DatasetRepository.delete_videos_by_dataset_id(db, dataset_id)
    # 删除课题绑定关系
    DatasetRepository.delete_topic_dataset_links(db, dataset_id)
    # 删除数据集
    DatasetRepository.delete_dataset(db, dataset_id)
    db.commit()

    # 清理向量库缓存
    try:
        loader = DocumentLoader()
        path = loader._dataset_store_path([dataset_id])  # type: ignore[attr-defined]
        if path.exists():
            shutil.rmtree(path)
    except Exception:
        pass
