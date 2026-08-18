#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: MuyuCheney
# Date: 2024-10-15

import os
import hashlib
from pathlib import Path
from langchain_core.documents import Document
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv, find_dotenv
from server.db.session import get_db
from server.db.models.video_item_model import VideoItemModel
from server.db.models.video_comment_model import VideoCommentModel
from server.db.models.video_danmaku_model import VideoDanmakuModel
import datetime

load_dotenv(find_dotenv())


class DocumentLoader:
    """
    Offline-only document loader for dataset-based RAG.
    """

    def __init__(self, vector_store_dir: Optional[str] = None):
        """
        Initialize DocumentLoader.

        Args:
            vector_store_dir (str): Local vector store directory, default vectorstores.
        """
        self.vector_store_dir = Path(vector_store_dir or os.getenv("VECTOR_STORE_DIR", "vectorstores"))
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)

    def _get_embedding_model(self):
        """Pick embedding model per config."""
        base_url = os.getenv("SILICON_BASE_URL", "https://api.siliconflow.cn/v1")
        return OpenAIEmbeddings(
            base_url=base_url,
            api_key=os.getenv("SILICON_API_KEY"),
            model=os.getenv("SILICON_EMBED_MODEL", "Qwen/Qwen3-Embedding-8B"),
        )

    def _dataset_store_path(self, dataset_ids: List[str]) -> Path:
        """Generate stable local vector store path for a set of dataset_ids."""
        key = "_".join(sorted(set(dataset_ids)))
        key_hash = hashlib.md5(key.encode("utf-8")).hexdigest()
        return self.vector_store_dir / f"ds_{key_hash}"

    async def create_vector_store(self, docs, store_path: Optional[str] = None) -> "FAISS":
        """
        Creates a FAISS vector store from a list of documents.

        Args:
            docs (List[Document]): A list of Document objects containing the content to be stored.
            store_path (Optional[str]): The path to store the vector store locally. If None, the vector store will not be stored.

        Returns:
            FAISS: The FAISS vector store containing the documents.
        """
        # Split text for better embedding & recall
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=100)
        texts = text_splitter.split_documents(docs)

        embedding_model = self._get_embedding_model()
        print(f"[vector] start embeddings, docs={len(docs)}, chunks={len(texts)}")

        store = FAISS.from_documents(texts, embedding_model)
        print("[vector] embeddings + FAISS build done")

        if store_path:
            Path(store_path).mkdir(parents=True, exist_ok=True)
            store.save_local(store_path)
            print(f"[vector] saved faiss to {store_path}")
        return store

    async def get_docs_from_dataset(
        self,
        dataset_ids: List[str],
        video_limit: int = 50,
        comment_limit: int = 20,
        danmaku_limit: int = 20,
    ) -> List[Document]:
        """
        Load documents from DB datasets.
        """
        docs: List[Document] = []
        with get_db() as db:
            videos = (
                db.query(VideoItemModel)
                .filter(VideoItemModel.dataset_id.in_(dataset_ids))
                .order_by(VideoItemModel.id.desc())
                .limit(video_limit)
                .all()
            )
            for v in videos:
                comments = (
                    db.query(VideoCommentModel.content)
                    .filter(VideoCommentModel.video_id == v.id)
                    .limit(comment_limit)
                    .all()
                )
                danmaku = (
                    db.query(VideoDanmakuModel.text)
                    .filter(VideoDanmakuModel.video_id == v.id)
                    .limit(danmaku_limit)
                    .all()
                )
                comment_texts = [c[0] for c in comments]
                danmaku_texts = [d[0] for d in danmaku]
                content_parts = [
                    f"标题: {v.title or ''}",
                    f"描述: {v.description or ''}",
                    f"标签: {v.tags or ''}",
                    f"链接: {v.url or ''}",
                    f"作者: {v.author or ''}",
                    f"评论: {'; '.join(comment_texts) if comment_texts else '无'}",
                    f"弹幕: {'; '.join(danmaku_texts) if danmaku_texts else '无'}",
                ]
                docs.append(
                    Document(
                        page_content="\n".join(content_parts),
                        metadata={
                            "aid": v.aid,
                            "bvid": v.bvid,
                            "title": v.title,
                            "url": v.url,
                            "dataset_id": v.dataset_id,
                            "keyword": v.keyword,
                            "pubdate": v.pubdate.isoformat() if isinstance(v.pubdate, datetime.datetime) else None,
                        },
                    )
                )
        return docs

    async def get_retriever_from_dataset(
        self,
        dataset_ids: List[str],
        video_limit: int = 50,
        comment_limit: int = 20,
        danmaku_limit: int = 20,
        k: int = 10,
        score_threshold: Optional[float] = None,
        query_text: Optional[str] = None,
    ):
        """
        Build retriever from dataset docs; cache vector store locally to avoid repeated embedding.
        Returns retrieval results using dataset_ids as query hint.
        """
        unique_ids = sorted(set(dataset_ids))
        if not unique_ids:
            return []

        store_path = self._dataset_store_path(unique_ids)
        embedding_model = self._get_embedding_model()
        store = None

        print(f"[vector] dataset_ids={unique_ids} store_path={store_path}")
        if store_path.exists():
            try:
                store = FAISS.load_local(
                    str(store_path),
                    embeddings=embedding_model,
                    allow_dangerous_deserialization=True,
                )
                doc_count = getattr(store, "index", None)
                doc_count = getattr(doc_count, "ntotal", None) or 0
                print(f"[vector] Loaded cached vector store: {store_path} (docs: {doc_count})")
                if doc_count == 0:
                    print("[vector] Cached vector store is empty, rebuilding...")
                    store = None
            except Exception as e:
                print(f"[vector] Load cached vector store failed, rebuilding: {e}")
                store = None

        if store is None:
            print(f"[vector] building docs from DB... video_limit={video_limit} comment_limit={comment_limit} danmaku_limit={danmaku_limit}")
            docs = await self.get_docs_from_dataset(unique_ids, video_limit, comment_limit, danmaku_limit)
            print(f"[vector] docs fetched: {len(docs)}")
            if docs:
                sample = docs[0].page_content
                print(f"[vector] sample doc length={len(sample)}")
            else:
                return []
            try:
                store = await self.create_vector_store(docs, store_path=str(store_path))
                print(f"[vector] Built and cached vector store: {store_path}")
            except Exception as e:
                print(f"[vector] create_vector_store failed: {e}")
                raise

        # clamp k in [1, 30] to avoid huge pulls
        k = max(1, min(k or 10, 30))
        search_kwargs = {"k": k}
        retriever = store.as_retriever(search_kwargs=search_kwargs)
        query = query_text or " ".join(unique_ids)
        docs = retriever.invoke(query)
        if not docs:
            try:
                fallback_docs = store.similarity_search(query, k=k)
                if fallback_docs:
                    print("---fallback: retriever returned 0, using raw similarity_search---")
                    docs = fallback_docs
            except Exception as e:
                print(f"similarity_search fallback failed: {e}")
        return docs



if __name__ == '__main__':
    import asyncio

    # Simple manual test (offline-only): requires existing DB datasets & env configured.
    async def main():
        loader = DocumentLoader()
        # print(await loader.get_retriever_from_dataset(["your_dataset_id"], k=5, query_text="测试查询"))
        print("DocumentLoader is offline-only. Use get_retriever_from_dataset().")

    asyncio.run(main())
