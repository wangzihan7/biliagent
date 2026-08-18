from typing import List, Optional, Tuple

import datetime

from bili_server.document_loader import DocumentLoader
from server.db.repository.dataset_repository import DatasetRepository
from server.exceptions import BadRequestError
from server.schemas.vector_store import VectorStoreStatus, VectorStoreSearchHit, VectorStoreSearchResponse


def _get_vector_store_status_for_dataset(
    loader: DocumentLoader, dataset, light: bool = False
) -> VectorStoreStatus:
    """Inspect FAISS store for a dataset."""
    path_obj = loader._dataset_store_path([dataset.dataset_id])  # type: ignore[attr-defined]
    store_path = str(path_obj)
    exists = path_obj.exists()
    doc_count = 0
    updated_at = None
    if exists and not light:
        try:
            updated_at = (
                path_obj.stat().st_mtime and datetime.datetime.fromtimestamp(path_obj.stat().st_mtime).isoformat()
            )
            from langchain_community.vectorstores import FAISS

            vs = FAISS.load_local(
                store_path,
                embeddings=loader._get_embedding_model(),
                allow_dangerous_deserialization=True,
            )
            idx = getattr(vs, "index", None)
            doc_count = getattr(idx, "ntotal", 0) or 0
        except Exception:
            doc_count = 0
    return VectorStoreStatus(
        dataset_id=dataset.dataset_id,
        dataset_name=getattr(dataset, "name", None),
        keyword=getattr(dataset, "keyword", None),
        path=store_path,
        exists=exists,
        doc_count=doc_count,
        updated_at=updated_at,
    )


def list_vector_stores(
    db,
    keyword: Optional[str],
    limit: int,
    offset: int,
    light: bool,
    user_id: Optional[str] = None,
):
    datasets, total = DatasetRepository.list_datasets_with_total(
        db,
        keyword=keyword,
        limit=limit,
        offset=offset,
        user_id=user_id,
    )
    loader = DocumentLoader()
    items = [_get_vector_store_status_for_dataset(loader, d, light=light) for d in datasets]
    return items, total


async def search_vector_store(
    dataset_ids: List[str],
    query: str,
    k: Optional[int] = 5,
) -> VectorStoreSearchResponse:
    if not dataset_ids:
        raise BadRequestError("dataset_ids 不能为空")
    loader = DocumentLoader()
    docs = await loader.get_retriever_from_dataset(
        dataset_ids,
        k=k or 5,
        query_text=query,
    )
    hits: List[VectorStoreSearchHit] = []
    query_lower = (query or "").lower()
    for idx, d in enumerate(docs or []):
        text = getattr(d, "page_content", "") or str(d)
        meta = getattr(d, "metadata", {}) or {}
        meta_str = " ".join(str(v) for v in meta.values()) if isinstance(meta, dict) else ""
        contains = 1 if query_lower and (query_lower in text.lower() or query_lower in meta_str.lower()) else 0
        hits.append(
            VectorStoreSearchHit(
                text=text,
                metadata={**meta, "_rank_contains_query": contains, "_idx": idx},
            )
        )
    # 优先包含查询词的结果，再按原顺序
    hits = sorted(hits, key=lambda h: (-h.metadata.get("_rank_contains_query", 0), h.metadata.get("_idx", 0)))
    return VectorStoreSearchResponse(
        dataset_ids=dataset_ids,
        query=query,
        hits=hits,
    )
