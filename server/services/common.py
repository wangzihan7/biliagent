from typing import List, Optional

from sqlalchemy.orm import Session

from server.db.repository.dataset_repository import DatasetRepository
from server.db.repository.audit_repository import AuditRepository
from server.exceptions import BadRequestError


def validate_and_resolve_dataset_ids(db: Session, dataset_ids: Optional[List[str]]) -> List[str]:
    """验证并返回存在的 dataset_id 列表；空列表或无效则抛 400"""
    if not dataset_ids:
        raise BadRequestError("请先选择至少一个数据集")

    requested_ids = [d for d in dict.fromkeys(dataset_ids) if d]
    datasets = DatasetRepository.get_by_dataset_ids(db, requested_ids)
    found_ids = [d.dataset_id for d in datasets if d.dataset_id]
    missing_ids = [d for d in requested_ids if d not in found_ids]
    if missing_ids or not found_ids:
        raise BadRequestError(
            f"无效的 dataset_id: {', '.join(missing_ids or requested_ids)}。"
            "请使用 /api/v1/datasets 查看有效数据集。"
        )
    return found_ids


def audit_query_success(db: Session, user_id: str, conversation_id: str, query_text: str) -> None:
    """记录查询成功日志"""
    AuditRepository.log_query(
        db=db,
        user_id=user_id,
        topic_id=None,
        conversation_id=conversation_id,
        query_text=query_text,
        status="success",
        error_msg=None,
    )
    db.commit()
