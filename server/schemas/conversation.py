from typing import Optional, List

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    user_id: str = Field(..., description="用户ID")
    conversation_name: Optional[str] = Field(
        "B站数据分析对话", description="会话名称"
    )
    topic_id: Optional[str] = Field(None, description="可选，绑定到课题")


class ConversationResponse(BaseModel):
    conversation_id: str
    user_id: str
    conversation_name: str
    topic_id: Optional[str] = None
    create_time: str
    update_time: str

    class Config:
        from_attributes = True


class ConversationUpdate(BaseModel):
    conversation_name: str = Field(..., description="新的会话名称")


class MessageResponse(BaseModel):
    message_id: str
    conversation_id: str
    role: str
    content: str
    create_time: str
    meta_data: Optional[dict] = None

    class Config:
        from_attributes = True


class MessageMarkImportantRequest(BaseModel):
    """标记/取消某条消息为课题报告中的关键回答"""

    is_important: bool = Field(True, description="是否标记为关键回答")


class KeywordResponse(BaseModel):
    extraction_id: str
    conversation_id: str
    original_question: str
    extracted_keywords: str
    create_time: str

    class Config:
        from_attributes = True
