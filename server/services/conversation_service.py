from typing import List
import json

from sqlalchemy.orm import Session

from server.db.repository.conversation_repository import ConversationRepository
from server.db.repository.keyword_repository import KeywordRepository
from server.db.repository.message_repository import MessageRepository
from server.db.repository.topic_repository import TopicRepository
from server.db.repository.user_repository import UserRepository
from server.exceptions import BadRequestError, ForbiddenError, NotFoundError
from server.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageResponse,
    MessageMarkImportantRequest,
    KeywordResponse,
)


def _ensure_user_exists(db: Session, user_id: str) -> None:
    if not UserRepository.get_user_by_id(db, user_id):
        raise NotFoundError("用户不存在")


def _to_conversation_response(conversation) -> ConversationResponse:
    return ConversationResponse(
        conversation_id=conversation.conversation_id,
        user_id=conversation.user_id,
        conversation_name=conversation.conversation_name,
        topic_id=getattr(conversation, "topic_id", None),
        create_time=str(conversation.create_time),
        update_time=str(conversation.update_time),
    )


def _to_message_response(message) -> MessageResponse:
    meta_data = getattr(message, "meta_data", None)
    if isinstance(meta_data, str):
        try:
            meta_data = json.loads(meta_data)
        except Exception:
            meta_data = None
    return MessageResponse(
        message_id=message.message_id,
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content,
        create_time=str(message.create_time),
        meta_data=meta_data,
    )


def create_conversation(db: Session, conv: ConversationCreate, current_user) -> ConversationResponse:
    if current_user.user_id != conv.user_id:
        raise ForbiddenError("用户身份不匹配")

    new_conv = ConversationRepository.create_conversation(
        db, conv.user_id, conv.conversation_name
    )
    if conv.topic_id:
        TopicRepository.attach_conversation(db, conv.topic_id, new_conv.conversation_id)
    db.commit()
    return _to_conversation_response(new_conv)


def get_conversation_or_404(db: Session, conversation_id: str) -> ConversationResponse:
    conversation = ConversationRepository.get_conversation_by_id(db, conversation_id)
    if not conversation:
        raise NotFoundError("会话不存在")
    return _to_conversation_response(conversation)


def list_user_conversations(db: Session, user_id: str, limit: int) -> List[ConversationResponse]:
    _ensure_user_exists(db, user_id)
    conversations = ConversationRepository.get_user_conversations(db, user_id, limit)
    return [_to_conversation_response(c) for c in conversations]


def update_conversation(
    db: Session,
    conversation_id: str,
    update: ConversationUpdate,
    current_user=None,
) -> ConversationResponse:
    """
    更新会话名称

    - 若传入 current_user，则校验会话归属（只能修改自己的会话）
    """
    if current_user is not None:
        conv = ConversationRepository.get_conversation_by_id(db, conversation_id)
        if not conv:
            raise NotFoundError("会话不存在")
        if conv.user_id != getattr(current_user, "user_id", None):
            raise ForbiddenError("无权修改该会话")

    conversation = ConversationRepository.update_conversation_name(
        db, conversation_id, update.conversation_name
    )
    if not conversation:
        raise NotFoundError("会话不存在")
    db.commit()
    return _to_conversation_response(conversation)


def delete_conversation(db: Session, conversation_id: str) -> None:
    conversation = ConversationRepository.get_conversation_by_id(db, conversation_id)
    if not conversation:
        raise NotFoundError("会话不存在")

    MessageRepository.delete_conversation_messages(db, conversation_id)
    TopicRepository.delete_conversation_links(db, conversation_id)
    ConversationRepository.delete_conversation(db, conversation_id)
    db.commit()


def get_messages(db: Session, conversation_id: str, limit: int) -> List[MessageResponse]:
    messages = MessageRepository.get_conversation_messages(db, conversation_id, limit)
    return [_to_message_response(m) for m in messages]


def mark_message_important(
    db: Session,
    message_id: str,
    req: MessageMarkImportantRequest,
    current_user,
) -> MessageResponse:
    message = MessageRepository.get_message_by_id(db, message_id)
    if not message:
        raise NotFoundError("消息不存在")

    conv = ConversationRepository.get_conversation_by_id(db, message.conversation_id)
    if not conv:
        raise NotFoundError("会话不存在")
    if conv.user_id != current_user.user_id:
        raise ForbiddenError("无权操作该消息")

    has_topic = TopicRepository.has_conversation_binding(db, conv.conversation_id)
    if not has_topic:
        raise BadRequestError("请先在课题中绑定该会话后再标记关键回答")

    updated = MessageRepository.update_metadata(
        db, message_id, {"is_important": req.is_important}
    )
    db.commit()
    return _to_message_response(updated)


def list_conversation_keywords(db: Session, conversation_id: str) -> List[KeywordResponse]:
    keywords = KeywordRepository.get_conversation_keywords(db, conversation_id)
    return [KeywordResponse.model_validate(k) for k in keywords]
