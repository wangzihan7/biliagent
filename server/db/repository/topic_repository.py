#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 课题相关的数据访问

import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from server.db.models.topic_model import TopicModel
from server.db.models.topic_conversation_model import TopicConversationModel
from server.db.models.topic_dataset_model import TopicDatasetModel
from server.db.models.conversation_model import ConversationModel
from server.db.models.dataset_model import DatasetModel


class TopicRepository:
    """课题、课题-会话、课题-数据集 相关操作"""

    @staticmethod
    def create_topic(
        db: Session,
        name: str,
        topic_type: Optional[str],
        description: Optional[str],
        user_id: Optional[str] = None,
    ) -> TopicModel:
        topic_id = uuid.uuid4().hex
        topic = TopicModel(
            topic_id=topic_id,
            user_id=user_id,
            name=name,
            topic_type=topic_type,
            description=description,
        )
        db.add(topic)
        db.flush()
        return topic

    @staticmethod
    def get_topic(db: Session, topic_id: str) -> Optional[TopicModel]:
        return (
            db.query(TopicModel)
            .filter(TopicModel.topic_id == topic_id)
            .first()
        )

    @staticmethod
    def list_topics(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        keyword: Optional[str] = None,
        topic_type: Optional[str] = None,
        user_id: Optional[str] = None,
        only_owned: bool = False,
    ) -> List[TopicModel]:
        query = db.query(TopicModel).order_by(TopicModel.created_at.desc())
        if keyword:
            like_kw = f"%{keyword}%"
            query = query.filter((TopicModel.name.like(like_kw)) | (TopicModel.description.like(like_kw)))
        if topic_type:
            query = query.filter(TopicModel.topic_type == topic_type)
        if user_id:
            query = query.filter(TopicModel.user_id == user_id)
        return query.offset(offset).limit(limit).all()

    @staticmethod
    def list_topics_with_total(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        keyword: Optional[str] = None,
        topic_type: Optional[str] = None,
        user_id: Optional[str] = None,
        only_owned: bool = False,
    ) -> tuple[List[TopicModel], int]:
        query = db.query(TopicModel).order_by(TopicModel.created_at.desc())
        if keyword:
            like_kw = f"%{keyword}%"
            query = query.filter((TopicModel.name.like(like_kw)) | (TopicModel.description.like(like_kw)))
        if topic_type:
            query = query.filter(TopicModel.topic_type == topic_type)
        if user_id:
            query = query.filter(TopicModel.user_id == user_id)
        total = query.count()
        items = query.offset(offset).limit(limit).all()
        return items, total

    @staticmethod
    def update_topic(db: Session, topic_id: str, name: Optional[str], topic_type: Optional[str], description: Optional[str]) -> Optional[TopicModel]:
        topic = TopicRepository.get_topic(db, topic_id)
        if not topic:
            return None
        if name:
            topic.name = name
        if topic_type is not None:
            topic.topic_type = topic_type
        if description is not None:
            topic.description = description
        db.flush()
        return topic

    @staticmethod
    def delete_topic(db: Session, topic_id: str) -> bool:
        topic = TopicRepository.get_topic(db, topic_id)
        if not topic:
            return False
        db.delete(topic)
        db.flush()
        return True

    @staticmethod
    def attach_conversation(db: Session, topic_id: str, conversation_id: str) -> TopicConversationModel:
        link = TopicConversationModel(topic_id=topic_id, conversation_id=conversation_id)
        db.add(link)
        db.flush()
        return link

    @staticmethod
    def list_conversations(db: Session, topic_id: str) -> List[ConversationModel]:
        return (
            db.query(ConversationModel)
            .join(TopicConversationModel, TopicConversationModel.conversation_id == ConversationModel.conversation_id)
            .filter(TopicConversationModel.topic_id == topic_id)
            .order_by(ConversationModel.update_time.desc())
            .all()
        )

    @staticmethod
    def attach_dataset(db: Session, topic_id: str, dataset_id: str) -> TopicDatasetModel:
        link = TopicDatasetModel(topic_id=topic_id, dataset_id=dataset_id)
        db.add(link)
        db.flush()
        return link

    @staticmethod
    def list_datasets(db: Session, topic_id: str) -> List[DatasetModel]:
        return (
            db.query(DatasetModel)
            .join(TopicDatasetModel, TopicDatasetModel.dataset_id == DatasetModel.dataset_id)
            .filter(TopicDatasetModel.topic_id == topic_id)
            .order_by(DatasetModel.created_at.desc())
            .all()
        )

    @staticmethod
    def delete_conversation_links(db: Session, conversation_id: str) -> int:
        return (
            db.query(TopicConversationModel)
            .filter(TopicConversationModel.conversation_id == conversation_id)
            .delete(synchronize_session=False)
        )

    @staticmethod
    def has_conversation_binding(db: Session, conversation_id: str) -> bool:
        return (
            db.query(TopicConversationModel)
            .filter(TopicConversationModel.conversation_id == conversation_id)
            .first()
            is not None
        )
