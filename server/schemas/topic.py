from typing import List, Optional

from pydantic import BaseModel, Field

from server.schemas.dataset import DatasetResponse


class TopicCreate(BaseModel):
    name: str = Field(..., description="课题名称")
    topic_type: Optional[str] = Field(None, description="课题类型，如旅游攻略、话题分析等")
    description: Optional[str] = Field(None, description="课题描述")


class TopicUpdate(BaseModel):
    name: Optional[str] = Field(None, description="课题名称")
    topic_type: Optional[str] = Field(None, description="课题类型")
    description: Optional[str] = Field(None, description="课题描述")


class TopicResponse(BaseModel):
    topic_id: str
    name: str
    topic_type: Optional[str]
    description: Optional[str]
    created_at: str
    updated_at: str


class PaginatedTopicResponse(BaseModel):
    items: List[TopicResponse]
    total: int


class TopicDetailResponse(TopicResponse):
    conversations: List[dict] = []  # 简化为 dict，避免循环依赖
    datasets: List[DatasetResponse] = []


class TopicConversationBind(BaseModel):
    conversation_id: str = Field(..., description="会话ID")


class TopicDatasetBind(BaseModel):
    dataset_id: str = Field(..., description="数据集ID")


class TopicReportResponse(BaseModel):
    topic_id: str
    topic_name: str
    summary: str
    llm_summary: Optional[str] = None
    totals: dict
    top_tags: List[str]
    top_keywords: List[str]
    sentiment: dict
    trend: List[dict]
    key_answers: List[dict] = []
    charts: Optional[dict] = None


class TopicReportTaskResponse(BaseModel):
    task_id: str
    topic_id: str
    status: str
    created_at: str
    updated_at: Optional[str] = None
    error: Optional[str] = None
    report: Optional[TopicReportResponse] = None
