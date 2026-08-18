#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lightweight wrappers around the blibli_get utilities to replace bilibili_tools.
Provides async-friendly search/pipeline helpers and a DB persistence entrypoint.
"""

import asyncio
import concurrent.futures
import datetime
import os
import uuid
from typing import Any, Dict, List, Optional

from blibli_get.哔哩哔哩视频信息 import build_pipeline_results, search_videos, extract_bilibili_info
from blibli_get.bibli弹幕 import process_video_danmaku
from blibli_get.blibli评论爬取 import process_video
from server.db.repository.dataset_repository import DatasetRepository
from server.db.repository.video_repository import VideoRepository
from server.db.session import get_db

# Defaults keep parity with the previous bilibili_tools crawler limits.
MAX_RESULTS_PER_KEYWORD = int(os.getenv("BILI_CRAWLER_MAX_ITEMS", "5"))
MAX_COMMENTS_PER_VIDEO = int(os.getenv("BILI_CRAWLER_MAX_COMMENTS", "10"))
MAX_COMMENT_PAGES = int(os.getenv("BILI_CRAWLER_MAX_COMMENT_PAGES", "1"))
MAX_REPLIES_PER_COMMENT = int(os.getenv("BILI_CRAWLER_MAX_REPLIES", "3"))
MAX_DANMAKU_PER_VIDEO = int(os.getenv("BILI_CRAWLER_MAX_DANMAKU", "50"))
MAX_CRAWL_CONCURRENCY = max(1, int(os.getenv("BILI_CRAWLER_CONCURRENCY", "5")))


def _parse_pubdate(pubdate: Optional[str]) -> Optional[datetime.datetime]:
    if not pubdate:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.datetime.strptime(pubdate, fmt)
        except Exception:
            continue
    try:
        return datetime.datetime.fromisoformat(pubdate)
    except Exception:
        return None


def _collect_comments_sync(
    oid: Any,
    max_pages: int,
    max_comments: int,
    max_replies: int,
) -> List[str]:
    """
    复用带日志的 process_video，返回文本列表（含二级回复）。
    """
    comments_text: List[str] = []
    try:
        all_comments = process_video(
            oid=oid,
            title=str(oid),
            save_path=None,
            max_pages=max_pages,
            max_comments=max_comments,
            max_replies=max_replies,
        )
        for c in all_comments or []:
            msg = c.get("content", {}).get("message")
            if msg:
                comments_text.append(msg)
            for r in c.get("replies") or []:
                r_msg = r.get("content", {}).get("message")
                if r_msg:
                    comments_text.append(r_msg)
    except Exception as e:
        print(f"[comments] oid={oid} process_video error: {e}")
    if max_comments:
        comments_text = comments_text[:max_comments]
    return comments_text


def _collect_danmaku_sync(
    cid: Any,
    referer: Optional[str],
    max_items: Optional[int],
) -> List[Dict[str, Any]]:
    if cid is None:
        print("[danmaku] cid missing, skip danmaku")
        return []
    try:
        result = process_video_danmaku(
            title=str(cid),
            cid=cid,
            save_path=None,
            referer=referer,
            max_items=max_items,
        )
        raw = result.get("danmaku") if isinstance(result, dict) else result
    except Exception as e:
        print(f"[danmaku] cid={cid} error: {e}")
        raw = []
    return [{"text": text, "progress_ms": 0} for text in (raw or [])]


def _process_video_data(
    video: Dict[str, Any],
    kw: str,
    max_comment_pages: int,
    max_comments: int,
    max_replies: int,
    max_danmaku: int,
):
    """纯网络/解析阶段，便于在线程池里并发，不做任何 DB 操作。"""
    aid = video.get("aid")
    bvid = video.get("bvid")
    cid = video.get("cid")
    title = video.get("title", "") or video.get("标题", "")
    author = video.get("author", "")
    url = video.get("url", "")
    description = video.get("description", "")
    tags = ", ".join(video.get("tags", []) or [])
    play = int(video.get("play") or 0)
    favorite_count = int(video.get("favorites") or 0)
    comment_count = int(video.get("comment_count") or 0)
    danmaku_count = int(video.get("danmaku") or 0)
    pubdate = _parse_pubdate(video.get("pubdate"))

    # 如缺失 cid/aid/bvid，尝试通过页面提取补全（用于弹幕/评论）
    if (cid is None or (not aid and not bvid)) and url:
        try:
            info = extract_bilibili_info(url)
            if info:
                cid = cid or info.get("CID")
                aid = aid or info.get("AID")
                bvid = bvid or info.get("BVID")
                title = title or info.get("标题")
                print(f"[info] filled cid/aid/bvid from page url={url}: cid={cid} aid={aid} bvid={bvid}")
        except Exception as e:
            print(f"[info] extract_bilibili_info failed url={url}: {e}")

    comments = _collect_comments_sync(
        oid=aid or bvid,
        max_pages=max_comment_pages,
        max_comments=max_comments,
        max_replies=max_replies,
    )
    danmaku = _collect_danmaku_sync(
        cid=cid,
        referer=url,
        max_items=max_danmaku,
    )
    comment_count = max(comment_count, len(comments))
    danmaku_count = max(danmaku_count, len(danmaku))

    return {
        "aid": aid,
        "bvid": bvid,
        "cid": cid,
        "title": title,
        "author": author,
        "url": url,
        "description": description,
        "tags": tags,
        "play": play,
        "favorite_count": favorite_count,
        "comment_count": comment_count,
        "danmaku_count": danmaku_count,
        "pubdate": pubdate,
        "kw": kw,
        "comments": comments,
        "danmaku": danmaku,
    }


async def search_videos_async(keyword: str, page: int = 1, limit: Optional[int] = None) -> List[Dict]:
    return await asyncio.to_thread(search_videos, keyword, page, limit)


async def build_pipeline_results_async(
    keywords: List[str],
    page: int = 1,
    limit: Optional[int] = None,
) -> List[Dict]:
    return await asyncio.to_thread(build_pipeline_results, keywords, page, limit)


def _crawl_to_db_sync(
    keywords: List[str],
    page: int = 1,
    max_items: Optional[int] = None,
    dataset_name: Optional[str] = None,
    user_id: Optional[str] = None,
    task_id: Optional[str] = None,
    max_comments: Optional[int] = None,
    max_comment_pages: Optional[int] = None,
    max_replies: Optional[int] = None,
    max_danmaku: Optional[int] = None,
) -> Dict[str, Any]:
    max_items = max_items or MAX_RESULTS_PER_KEYWORD
    max_comments = max_comments if max_comments is not None else MAX_COMMENTS_PER_VIDEO
    max_comment_pages = max_comment_pages or MAX_COMMENT_PAGES
    max_replies = MAX_REPLIES_PER_COMMENT if max_replies is None else max_replies
    max_danmaku = max_danmaku if max_danmaku is not None else MAX_DANMAKU_PER_VIDEO

    total_videos = 0
    total_comments = 0
    total_danmaku = 0
    dataset_ids: List[str] = []
    details: List[Dict[str, Any]] = []

    with get_db() as db:
        for kw in keywords:
            # fetch and trim search results across pages
            results: List[Dict] = []
            max_pages = max(1, page)
            for p in range(1, max_pages + 1):
                page_results = search_videos(kw, page=p, limit=None)
                if not page_results:
                    break

                results.extend(page_results)
                if max_items and len(results) >= max_items:
                    break
            if max_items:
                results = results[:max_items]

            print(f"[crawl] keyword={kw} raw_results={len(results)} page={page} max_items={max_items}")

            # task_id 由调用方传入时，避免重复创建（由 API 预创建）
            task_obj = None
            if not task_id or len(keywords) > 1:
                task_obj = DatasetRepository.create_task(
                    db=db,
                    keyword=kw,
                    page=page,
                    max_items=max_items,
                    task_id=task_id if len(keywords) == 1 else None,
                )
                db.flush()
                task_id_in_use = task_obj.task_id
            else:
                task_id_in_use = task_id

            dataset_id = uuid.uuid4().hex if dataset_name else None
            dataset_task_id = task_id_in_use or (task_obj.task_id if task_obj else None)
            fallback_task_id = dataset_task_id or uuid.uuid4().hex
            current_dataset_name = dataset_name or f"dataset-{kw}-{fallback_task_id[:6]}"

            k_videos = 0
            k_comments = 0
            k_danmaku = 0

            # 并发抓取网络数据，再串行写 DB，避免会话跨线程问题
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CRAWL_CONCURRENCY) as executor:
                future_to_video = {
                    executor.submit(
                        _process_video_data,
                        video,
                        kw,
                        max_comment_pages,
                        max_comments,
                        max_replies,
                        max_danmaku,
                    ): video
                    for video in results
                }

                for future in concurrent.futures.as_completed(future_to_video):
                    try:
                        data = future.result()
                    except Exception as exc:
                        print(f"[video] fetch error: {exc}")
                        continue

                    aid = data.get("aid")
                    bvid = data.get("bvid")
                    cid = data.get("cid")
                    title = data.get("title", "")
                    author = data.get("author", "")
                    url = data.get("url", "")
                    description = data.get("description", "")
                    tags = data.get("tags", "")
                    play = data.get("play", 0)
                    favorite_count = data.get("favorite_count", 0)
                    comment_count = data.get("comment_count", 0)
                    danmaku_count = data.get("danmaku_count", 0)
                    pubdate = data.get("pubdate")
                    comments = data.get("comments") or []
                    danmaku = data.get("danmaku") or []

                    video_model = VideoRepository.upsert_video(
                        db=db,
                        aid=str(aid) if aid else None,
                        bvid=str(bvid) if bvid else None,
                        title=title,
                        author=author,
                        url=url,
                        description=description,
                        tags=tags,
                        play=play,
                        favorite_count=favorite_count,
                        comment_count=comment_count,
                        danmaku_count=danmaku_count,
                        pubdate=pubdate,
                        keyword=kw,
                        dataset_id=dataset_id,
                    )
                    k_videos += 1
                    saved_comments = VideoRepository.add_comments(db, video_model, aid, comments)
                    saved_danmaku = VideoRepository.add_danmaku(db, video_model, aid, danmaku)
                    k_comments += saved_comments
                    k_danmaku += saved_danmaku
                    print(
                        f"[video] kw={kw} aid={aid} bvid={bvid} cid={cid} play={play} "
                        f"comments_grabbed={len(comments)} saved={saved_comments} "
                        f"danmaku_grabbed={len(danmaku)} saved={saved_danmaku}"
                    )

            print(
                f"[crawl] keyword={kw} videos={k_videos} comments={k_comments} "
                f"danmaku={k_danmaku} dataset_id={dataset_id} task_id={dataset_task_id}"
            )

            if task_id_in_use:
                DatasetRepository.update_task(
                    db=db,
                    task_id=task_id_in_use,
                    status="success",
                    video_count=k_videos,
                    comment_count=k_comments,
                    danmaku_count=k_danmaku,
                )

            if current_dataset_name and dataset_id:
                DatasetRepository.create_dataset(
                    db=db,
                    user_id=user_id,
                    name=current_dataset_name,
                    keyword=kw,
                    task_id=dataset_task_id,
                    video_count=k_videos,
                    comment_count=k_comments,
                    danmaku_count=k_danmaku,
                    data_path=None,
                    dataset_id=dataset_id,
                )
                dataset_ids.append(dataset_id)

            details.append(
                {
                    "keyword": kw,
                    "task_id": dataset_task_id,
                    "dataset_id": dataset_id,
                    "videos": k_videos,
                    "comments": k_comments,
                    "danmaku": k_danmaku,
                }
            )
            total_videos += k_videos
            total_comments += k_comments
            total_danmaku += k_danmaku

        db.commit()

    return {
        "videos": total_videos,
        "comments": total_comments,
        "danmaku": total_danmaku,
        "dataset_ids": dataset_ids,
        "details": details,
    }


async def crawl_to_db(
    keywords: List[str],
    page: int = 1,
    max_items: Optional[int] = None,
    dataset_name: Optional[str] = None,
    user_id: Optional[str] = None,
    task_id: Optional[str] = None,
    max_comments: Optional[int] = None,
    max_comment_pages: Optional[int] = None,
    max_replies: Optional[int] = None,
    max_danmaku: Optional[int] = None,
) -> Dict[str, Any]:
    return await asyncio.to_thread(
        _crawl_to_db_sync,
        keywords,
        page,
        max_items,
        dataset_name,
        user_id,
        task_id,
        max_comments,
        max_comment_pages,
        max_replies,
        max_danmaku,
    )
