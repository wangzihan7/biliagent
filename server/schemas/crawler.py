from typing import Optional

from pydantic import BaseModel


class CrawlerConfigResponse(BaseModel):
    use_rate_limit: bool
    max_concurrency: int
    min_interval_ms: int
    updated_at: str


class CrawlerConfigUpdate(BaseModel):
    use_rate_limit: Optional[bool] = None
    max_concurrency: Optional[int] = None
    min_interval_ms: Optional[int] = None

