from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from server.db.repository.conversation_repository import ConversationRepository
from server.chat.bilibili_chat import BilibiliAnalysisChat
from server.services import common


def validate_and_resolve_datasets(
    db: Session, dataset_ids: Optional[List[str]]
) -> List[str]:
    return common.validate_and_resolve_dataset_ids(db, dataset_ids)


def ensure_conversation(
    db: Session, user_id: str, conversation_id: Optional[str]
) -> str:
    if conversation_id:
        return conversation_id
    conversation = ConversationRepository.create_conversation(
        db, user_id, "B站数据分析对话"
    )
    db.commit()
    return conversation.conversation_id


def start_chat_engine(
    user_id: str, conversation_id: str, dataset_ids: List[str]
) -> BilibiliAnalysisChat:
    return BilibiliAnalysisChat(
        user_id=user_id,
        conversation_id=conversation_id,
        dataset_ids=dataset_ids,
    )


def audit_success(
    db: Session, user_id: str, conversation_id: str, query_text: str
) -> None:
    common.audit_query_success(db, user_id, conversation_id, query_text)
