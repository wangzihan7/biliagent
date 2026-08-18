from typing import List, Optional

from pydantic import BaseModel, Field


class CrawlRequest(BaseModel):
    keyword: str = Field(..., description="抓取关键词")
    page: int = Field(1, ge=1, le=5, description="抓取页数（小规模防炸）")
    max_items: Optional[int] = Field(None, description="每关键词最多条数")
    dataset_name: Optional[str] = Field(None, description="数据集名称，可选")
    max_comments: Optional[int] = Field(None, description="单视频评论抓取上限（含二级回复）")
    max_comment_pages: Optional[int] = Field(None, description="评论页数上限")
    max_replies: Optional[int] = Field(None, description="每条评论的回复上限（0 表示不抓回复）")
    max_danmaku: Optional[int] = Field(None, description="弹幕抓取上限")


class CrawlTaskResponse(BaseModel):
    task_id: str
    status: str
    keyword: str
    page: int
    max_items: int
    video_count: int
    comment_count: int
    danmaku_count: int
    created_at: str
    updated_at: str


class DatasetResponse(BaseModel):
    dataset_id: str
    user_id: Optional[str] = None
    name: str
    keyword: str
    task_id: Optional[str]
    video_count: int
    comment_count: int
    danmaku_count: int
    data_path: Optional[str]
    created_at: str
    updated_at: str


class PaginatedDatasetResponse(BaseModel):
    items: List[DatasetResponse]
    total: int


class DatasetDeleteResponse(BaseModel):
    dataset_id: str
    deleted: bool = True

