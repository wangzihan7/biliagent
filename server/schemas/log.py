from typing import List, Optional

from pydantic import BaseModel


class QueryLogItem(BaseModel):
    user_id: str
    topic_id: Optional[str]
    conversation_id: Optional[str]
    status: str
    error_msg: Optional[str]
    query_text: str
    created_at: str


class CrawlLogItem(BaseModel):
    user_id: str
    task_id: Optional[str]
    keyword: Optional[str]
    status: str
    error_msg: Optional[str]
    video_count: int
    comment_count: int
    danmaku_count: int
    created_at: str


class PaginatedCrawlLogResponse(BaseModel):
    items: List[CrawlLogItem]
    total: int

