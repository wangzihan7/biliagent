#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 视频/评论/弹幕 数据访问层

from typing import List, Optional
from sqlalchemy.orm import Session
from server.db.models.video_item_model import VideoItemModel
from server.db.models.video_comment_model import VideoCommentModel
from server.db.models.video_danmaku_model import VideoDanmakuModel
from datetime import datetime


class VideoRepository:
    """视频及其评论、弹幕的存取"""

    @staticmethod
    def upsert_video(
        db: Session,
        aid: Optional[str],
        bvid: Optional[str],
        title: str,
        author: str,
        url: str,
        description: str,
        tags: str,
        play: int,
        favorite_count: int,
        comment_count: int,
        danmaku_count: int,
        pubdate: Optional[datetime],
        keyword: Optional[str],
        dataset_id: Optional[str],
    ) -> VideoItemModel:
        """根据 aid/bvid upsert 视频基础信息"""
        video = None
        if aid:
            video = db.query(VideoItemModel).filter(VideoItemModel.aid == str(aid)).first()
        if not video and bvid:
            video = db.query(VideoItemModel).filter(VideoItemModel.bvid == str(bvid)).first()

        if video:
            video.title = title
            video.author = author
            video.url = url
            video.description = description
            video.tags = tags
            video.play = play
            video.favorite_count = favorite_count
            video.comment_count = comment_count
            video.danmaku_count = danmaku_count
            video.pubdate = pubdate
            video.keyword = keyword
            video.dataset_id = dataset_id
        else:
            video = VideoItemModel(
                aid=str(aid) if aid else None,
                bvid=str(bvid) if bvid else None,
                title=title,
                author=author,
                url=url,
                description=description,
                tags=tags,
                play=play,
                favorite_count=favorite_count,
                comment_count=comment_count,
                danmaku_count=danmaku_count,
                pubdate=pubdate,
                keyword=keyword,
                dataset_id=dataset_id,
            )
            db.add(video)
        db.flush()
        return video

    @staticmethod
    def add_comments(db: Session, video: VideoItemModel, aid: Optional[str], comments: List[str]) -> int:
        """批量插入评论（去重: 按 video_id+content）"""
        if not comments:
            return 0
        existing = {
            c[0]
            for c in db.query(VideoCommentModel.content).filter(
                VideoCommentModel.video_id == video.id
            )
        }
        to_insert = [c for c in comments if c not in existing]
        if not to_insert:
            return 0
        rows = [
            VideoCommentModel(video_id=video.id, aid=str(aid) if aid else None, content=c)
            for c in to_insert
        ]
        db.add_all(rows)
        db.flush()
        return len(rows)

    @staticmethod
    def add_danmaku(
        db: Session, video: VideoItemModel, aid: Optional[str], danmaku_list: List[dict]
    ) -> int:
        """批量插入弹幕（去重: 按 video_id+text+progress_ms）"""
        if not danmaku_list:
            return 0
        existing = {
            (dm.text, dm.progress_ms)
            for dm in db.query(VideoDanmakuModel.text, VideoDanmakuModel.progress_ms).filter(
                VideoDanmakuModel.video_id == video.id
            )
        }
        rows = []
        for dm in danmaku_list:
            text = dm.get("text") or ""
            progress = int(dm.get("progress_ms") or 0)
            key = (text, progress)
            if key in existing:
                continue
            rows.append(
                VideoDanmakuModel(
                    video_id=video.id,
                    aid=str(aid) if aid else None,
                    text=text,
                    progress_ms=progress,
                )
            )
        if not rows:
            return 0
        db.add_all(rows)
        db.flush()
        return len(rows)

    @staticmethod
    def list_videos_by_dataset_id(db: Session, dataset_id: str) -> List[VideoItemModel]:
        return (
            db.query(VideoItemModel)
            .filter(VideoItemModel.dataset_id == dataset_id)
            .order_by(VideoItemModel.id.desc())
            .all()
        )

    @staticmethod
    def list_videos_by_dataset_ids(db: Session, dataset_ids: List[str]) -> List[VideoItemModel]:
        if not dataset_ids:
            return []
        return (
            db.query(VideoItemModel)
            .filter(VideoItemModel.dataset_id.in_(dataset_ids))
            .all()
        )

    @staticmethod
    def list_video_comments(
        db: Session, video_id: int, limit: Optional[int] = None
    ) -> List[str]:
        query = db.query(VideoCommentModel.content).filter(
            VideoCommentModel.video_id == video_id
        )
        if limit is not None:
            query = query.limit(limit)
        return [c[0] for c in query.all()]

    @staticmethod
    def list_video_danmaku(
        db: Session, video_id: int, limit: Optional[int] = None
    ) -> List[tuple]:
        query = db.query(
            VideoDanmakuModel.text, VideoDanmakuModel.progress_ms
        ).filter(VideoDanmakuModel.video_id == video_id)
        if limit is not None:
            query = query.limit(limit)
        return query.all()
