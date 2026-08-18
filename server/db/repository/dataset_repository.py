#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 数据集/任务 数据访问层

import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from server.db.models.crawl_task_model import CrawlTaskModel
from server.db.models.dataset_model import DatasetModel
from server.db.models.video_item_model import VideoItemModel
from server.db.models.video_comment_model import VideoCommentModel
from server.db.models.video_danmaku_model import VideoDanmakuModel
from server.db.models.topic_dataset_model import TopicDatasetModel


class DatasetRepository:
    """管理 crawl_task 与 dataset 的基础操作"""

    @staticmethod
    def create_task(
        db: Session,
        keyword: str,
        page: int,
        max_items: int,
        task_id: Optional[str] = None,
        status: str = "running",
    ) -> CrawlTaskModel:
        """
        创建爬虫任务记录。

        兼容两种调用方式：
        - 旧接口：create_task(db, keyword, page, max_items)
        - 新接口：create_task(db, keyword, page, max_items, task_id=..., status=...)
        """
        task_id = task_id or uuid.uuid4().hex
        task = CrawlTaskModel(
            task_id=task_id,
            keyword=keyword,
            page=page,
            max_items=max_items,
            status=status,
        )
        db.add(task)
        db.flush()
        return task

    @staticmethod
    def update_task(
        db: Session,
        task_id: str,
        status: str,
        video_count: int = 0,
        comment_count: int = 0,
        danmaku_count: int = 0,
        error_msg: Optional[str] = None,
        data_path: Optional[str] = None,
    ) -> Optional[CrawlTaskModel]:
        task = (
            db.query(CrawlTaskModel)
            .filter(CrawlTaskModel.task_id == task_id)
            .first()
        )
        if not task:
            return None
        task.status = status
        task.video_count = video_count
        task.comment_count = comment_count
        task.danmaku_count = danmaku_count
        task.error_msg = error_msg
        if data_path:
            task.data_path = data_path
        db.flush()
        return task

    @staticmethod
    def create_dataset(
        db: Session,
        name: str,
        keyword: str,
        task_id: Optional[str],
        video_count: int,
        comment_count: int,
        danmaku_count: int,
        data_path: Optional[str] = None,
        dataset_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> DatasetModel:
        dataset_id = dataset_id or uuid.uuid4().hex
        dataset = DatasetModel(
            dataset_id=dataset_id,
            user_id=user_id,
            name=name,
            keyword=keyword,
            task_id=task_id,
            video_count=video_count,
            comment_count=comment_count,
            danmaku_count=danmaku_count,
            data_path=data_path,
        )
        db.add(dataset)
        db.flush()
        return dataset

    @staticmethod
    def list_tasks(db: Session, keyword: Optional[str] = None, limit: int = 20) -> List[CrawlTaskModel]:
        query = db.query(CrawlTaskModel).order_by(CrawlTaskModel.created_at.desc())
        if keyword:
            query = query.filter(CrawlTaskModel.keyword.like(f"%{keyword}%"))
        return query.limit(limit).all()

    @staticmethod
    def list_datasets(
        db: Session,
        keyword: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        user_id: Optional[str] = None,
        only_owned: bool = False,
    ) -> List[DatasetModel]:
        query = db.query(DatasetModel).order_by(DatasetModel.created_at.desc())
        if keyword:
            query = query.filter(DatasetModel.keyword.like(f"%{keyword}%"))
        if user_id:
            query = query.filter(DatasetModel.user_id == user_id)
        return query.offset(offset).limit(limit).all()

    @staticmethod
    def list_datasets_with_total(
        db: Session,
        keyword: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        user_id: Optional[str] = None,
        only_owned: bool = False,
    ) -> tuple[list[DatasetModel], int]:
        """支持分页并返回总数."""
        query = db.query(DatasetModel).order_by(DatasetModel.created_at.desc())
        if keyword:
            query = query.filter(DatasetModel.keyword.like(f"%{keyword}%"))
        if user_id:
            query = query.filter(DatasetModel.user_id == user_id)
        total = query.count()
        items = query.offset(offset).limit(limit).all()
        return items, total

    @staticmethod
    def get_by_dataset_ids(db: Session, dataset_ids: List[str]) -> List[DatasetModel]:
        """Fetch datasets by dataset_id list."""
        if not dataset_ids:
            return []
        return (
            db.query(DatasetModel)
            .filter(DatasetModel.dataset_id.in_(dataset_ids))
            .all()
        )

    @staticmethod
    def get_by_dataset_id(db: Session, dataset_id: str) -> Optional[DatasetModel]:
        """Fetch a single dataset by dataset_id."""
        return (
            db.query(DatasetModel)
            .filter(DatasetModel.dataset_id == dataset_id)
            .first()
        )

    @staticmethod
    def get_video_ids(db: Session, dataset_id: str) -> List[int]:
        return [
            vid
            for (vid,) in db.query(VideoItemModel.id)
            .filter(VideoItemModel.dataset_id == dataset_id)
            .all()
        ]

    @staticmethod
    def delete_comments_by_video_ids(db: Session, video_ids: List[int]) -> int:
        if not video_ids:
            return 0
        return (
            db.query(VideoCommentModel)
            .filter(VideoCommentModel.video_id.in_(video_ids))
            .delete(synchronize_session=False)
        )

    @staticmethod
    def delete_danmaku_by_video_ids(db: Session, video_ids: List[int]) -> int:
        if not video_ids:
            return 0
        return (
            db.query(VideoDanmakuModel)
            .filter(VideoDanmakuModel.video_id.in_(video_ids))
            .delete(synchronize_session=False)
        )

    @staticmethod
    def delete_videos_by_dataset_id(db: Session, dataset_id: str) -> int:
        return (
            db.query(VideoItemModel)
            .filter(VideoItemModel.dataset_id == dataset_id)
            .delete(synchronize_session=False)
        )

    @staticmethod
    def delete_topic_dataset_links(db: Session, dataset_id: str) -> int:
        return (
            db.query(TopicDatasetModel)
            .filter(TopicDatasetModel.dataset_id == dataset_id)
            .delete(synchronize_session=False)
        )

    @staticmethod
    def delete_dataset(db: Session, dataset_id: str) -> int:
        return (
            db.query(DatasetModel)
            .filter(DatasetModel.dataset_id == dataset_id)
            .delete(synchronize_session=False)
        )
