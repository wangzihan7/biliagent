from typing import List, Optional

from pydantic import BaseModel, Field


class VectorStoreStatus(BaseModel):
    dataset_id: str
    dataset_name: Optional[str] = None
    keyword: Optional[str] = None
    path: Optional[str] = None
    exists: bool = False
    doc_count: int = 0
    updated_at: Optional[str] = None


class PaginatedVectorStoreResponse(BaseModel):
    items: List[VectorStoreStatus]
    total: int


class VectorStoreSearchRequest(BaseModel):
    dataset_ids: List[str]
    query: str
    k: Optional[int] = 5


class VectorStoreSearchHit(BaseModel):
    text: str
    metadata: dict


class VectorStoreSearchResponse(BaseModel):
    dataset_ids: List[str]
    query: str
    hits: List[VectorStoreSearchHit] = []
