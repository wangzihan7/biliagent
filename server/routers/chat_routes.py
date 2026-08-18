import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session

from server.db.session import get_db_session
from server.routers.deps import get_current_user
from server.schemas.chat import ChatRequest
from server.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageResponse,
    MessageMarkImportantRequest,
    KeywordResponse,
)
from server.services import chat_service
from server.services import conversation_service

router = APIRouter(prefix="/api/v1", tags=["chat"])


# ========= 会话管理 =========


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    summary="创建会话",
)
def create_conversation(
    conv: ConversationCreate,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return conversation_service.create_conversation(db, conv, current_user)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="获取会话详情",
)
def get_conversation(conversation_id: str, db: Session = Depends(get_db_session)):
    return conversation_service.get_conversation_or_404(db, conversation_id)


@router.get(
    "/users/{user_id}/conversations",
    response_model=List[ConversationResponse],
    summary="获取用户的会话列表",
)
def get_user_conversations(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db_session),
):
    return conversation_service.list_user_conversations(db, user_id, limit)


@router.put(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="更新会话名称",
)
def update_conversation(
    conversation_id: str,
    update: ConversationUpdate,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return conversation_service.update_conversation(db, conversation_id, update, current_user)


@router.patch(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="更新会话名称（PATCH兼容）",
)
def patch_conversation(
    conversation_id: str,
    update: ConversationUpdate,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return conversation_service.update_conversation(db, conversation_id, update, current_user)


@router.delete(
    "/conversations/{conversation_id}",
    summary="删除会话（含消息与课题绑定）",
)
def delete_conversation(conversation_id: str, db: Session = Depends(get_db_session)):
    conversation_service.delete_conversation(db, conversation_id)
    return {"success": True}


# ========= 聊天与消息 =========


@router.post("/chat/stream", summary="流式聊天接口")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    if current_user.user_id != request.user_id:
        raise HTTPException(status_code=403, detail="用户身份不匹配")

    dataset_ids = chat_service.validate_and_resolve_datasets(db, request.dataset_ids)
    conversation_id = chat_service.ensure_conversation(
        db, request.user_id, request.conversation_id
    )

    chat_engine = chat_service.start_chat_engine(
        user_id=request.user_id,
        conversation_id=conversation_id,
        dataset_ids=dataset_ids,
    )

    async def event_generator():
        async for chunk in chat_engine.chat(request.query):
            yield {
                "event": "message",
                "data": json.dumps(chunk, ensure_ascii=False),
            }

    response = EventSourceResponse(event_generator())
    chat_service.audit_success(
        db=db,
        user_id=current_user.user_id,
        conversation_id=conversation_id,
        query_text=request.query,
    )
    return response


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=List[MessageResponse],
    summary="获取会话消息历史",
)
def get_conversation_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_session),
):
    return conversation_service.get_messages(db, conversation_id, limit)


@router.post(
    "/messages/{message_id}/important",
    response_model=MessageResponse,
    summary="标记/取消关键回答（用于课题报告汇总）",
)
def mark_message_important(
    message_id: str,
    req: MessageMarkImportantRequest,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return conversation_service.mark_message_important(db, message_id, req, current_user)


@router.get(
    "/conversations/{conversation_id}/keywords",
    response_model=List[KeywordResponse],
    summary="获取会话关键词记录",
)
def get_conversation_keywords(
    conversation_id: str,
    db: Session = Depends(get_db_session),
):
    return conversation_service.list_conversation_keywords(db, conversation_id)
