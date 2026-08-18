from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from server.db.session import get_db_session
from server.routers.deps import get_current_user, get_current_admin
from server.schemas.dataset import (
    DatasetResponse,
    DatasetDeleteResponse,
    PaginatedDatasetResponse,
)
from server.services import dataset_service

router = APIRouter(prefix="/api/v1", tags=["datasets"])


@router.get(
    "/datasets",
    response_model=PaginatedDatasetResponse,
    summary="查询数据集列表",
)
def list_datasets(
    keyword: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return dataset_service.list_datasets(
        db=db,
        keyword=keyword,
        limit=limit,
        offset=offset,
        current_user=current_user,
    )


@router.get(
    "/datasets/{dataset_id}",
    response_model=DatasetResponse,
    summary="获取数据集详情",
)
def get_dataset_detail(dataset_id: str, db: Session = Depends(get_db_session)):
    return dataset_service.get_dataset_detail(db, dataset_id)


@router.get(
    "/datasets/{dataset_id}/export",
    summary="导出数据集内容（jsonl 或 csv）",
)
def export_dataset(
    dataset_id: str,
    format: str = Query("jsonl", pattern="^(jsonl|csv)$", description="导出格式"),
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return dataset_service.export_dataset(
        db=db,
        dataset_id=dataset_id,
        format=format,
        current_user=current_user,
    )


@router.delete(
    "/datasets/{dataset_id}",
    response_model=DatasetDeleteResponse,
    summary="删除数据集（admin）",
)
def delete_dataset(
    dataset_id: str,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
):
    dataset_service.get_dataset_or_404(db, dataset_id)
    dataset_service.delete_dataset_and_related(db, dataset_id)
    return DatasetDeleteResponse(dataset_id=dataset_id, deleted=True)
