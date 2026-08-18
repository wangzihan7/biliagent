from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(..., description="用户ID")
    conversation_id: Optional[str] = Field(
        None, description="会话ID，不提供则创建新会话"
    )
    query: str = Field(..., description="用户问题或指令")
    dataset_ids: Optional[List[str]] = Field(None, description="可选，指定使用的数据集ID列表")


class ChatStreamResponseChunk(BaseModel):
    """占位，用于标注流式返回的基本结构"""

    type: str
    content: Optional[str] = None
    metrics: Optional[dict] = None

