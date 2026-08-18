import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import quote

import pandas as pd
import requests

try:
    from .config import build_headers, get_proxies, default_output_dir
except ImportError:  # pragma: no cover - fallback for direct script run
    from config import build_headers, get_proxies, default_output_dir


def extract_bilibili_info(url: str) -> Optional[Dict]:
    """
    提取单个视频的基础信息（标题、描述、CID、AID、BVID、VID）。
    """
    headers = build_headers(referer="https://www.bilibili.com/video/")
    proxies = get_proxies()

    try:
        response = requests.get(url, headers=headers, timeout=10, proxies=proxies)
        response.raise_for_status()
        html = response.text

        # 提取 window.__INITIAL_STATE__
        match = re.search(r"window.__INITIAL_STATE__=(.*?);\(function", html)
        if not match:
            print("未能提取视频信息：缺少 __INITIAL_STATE__")
            return None

        initial_state = match.group(1)
        state_dict = json.loads(initial_state)

        video_data = state_dict.get("videoData") or {}

        title = video_data.get("title")
        description = video_data.get("desc")
        cid = video_data.get("cid")
        aid = video_data.get("aid")
        bvid = video_data.get("bvid")
        vid = aid  # 兼容字段

        return {
            "标题": title,
            "描述": description,
            "CID": cid,
            "AID": aid,
            "BVID": bvid,
            "VID": vid,
            "链接": url,
        }
    except Exception as e:
        print(f"提取视频信息时出错：{str(e)}")
        return None


def save_to_excel(video_infos: List[Dict], save_path: Optional[str] = None, save: bool = True):
    """
    将视频信息保存为 Excel；当 save=False 或 save_path=None 时，仅返回数据。
    """
    if not save:
        return None

    if not save_path:
        save_path = str(default_output_dir("video_info"))

    df = pd.DataFrame(video_infos)

    # 创建保存目录
    os.makedirs(save_path, exist_ok=True)

    # 生成文件名
    current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    file_name = f"视频信息-{current_time}.xlsx"
    file_path = os.path.join(save_path, file_name)

    # 保存到Excel
    df.to_excel(file_path, index=False, engine="openpyxl")
    print(f"视频信息已保存至 {file_path}")
    return file_path


def search_video_urls(
    keyword: str, page: int = 1, limit: Optional[int] = None, order: Optional[str] = None
) -> List[str]:
    """
    通过关键词搜索视频，返回视频链接列表（默认 B 站综合排序）。
    使用 B 站公开搜索接口，避免依赖 bilibili_tools。
    """
    params = {
        "search_type": "video",
        "keyword": keyword,
        "page": page,
    }
    if order:
        params["order"] = order  # 例如 totalrank/pubdate/click

    encoded_keyword = quote(keyword)
    headers = build_headers(referer=f"https://search.bilibili.com/all?keyword={encoded_keyword}")
    proxies = get_proxies()
    try:
        resp = requests.get(
            "https://api.bilibili.com/x/web-interface/search/type",
            params=params,
            headers=headers,
            timeout=10,
            proxies=proxies,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"关键词搜索失败：{e}")
        return []

    result_items = data.get("data", {}).get("result", []) or []
    urls: List[str] = []
    for item in result_items:
        url = item.get("arcurl") or ""
        bvid = item.get("bvid") or ""
        if not url and bvid:
            url = f"https://www.bilibili.com/video/{bvid}"
        if url:
            urls.append(url)
            if limit and len(urls) >= limit:
                break
    return urls


def fetch_video_infos_by_keyword(keyword: str, page: int = 1, limit: Optional[int] = None) -> List[Dict]:
    """
    通过关键词搜索视频并返回完整的视频信息（标题、CID、AID、BVID、链接等）。
    """
    urls = search_video_urls(keyword, page=page, limit=limit)
    if not urls:
        return []

    video_infos = []
    for url in urls:
        info = extract_bilibili_info(url)
        if info:
            video_infos.append(info)
    return video_infos


def _format_video_text(item: Dict) -> str:
    headers = [
        "类型",
        "作者",
        "分类",
        "视频链接",
        "标题",
        "描述",
        "播放量",
        "弹幕数",
        "收藏数",
        "标签",
        "评论数",
        "发布时间",
    ]
    values = [
        item.get("type", ""),
        item.get("author", ""),
        item.get("typename", ""),
        item.get("url", ""),
        item.get("title", ""),
        item.get("description", ""),
        item.get("play", 0),
        item.get("danmaku", 0),
        item.get("favorites", 0),
        ", ".join(item.get("tags", []) or []),
        item.get("comment_count", 0),
        item.get("pubdate", ""),
    ]
    return "\n".join(f"{h}: {v}" for h, v in zip(headers, values))


def search_videos(
    keyword: str,
    page: int = 1,
    limit: Optional[int] = None,
    order: Optional[str] = None,
) -> List[Dict]:
    """
    返回结构化视频信息列表，用于 API/流水线。
    """
    params = {
        "search_type": "video",
        "keyword": keyword,
        "page": page,
    }
    if order:
        params["order"] = order

    encoded_keyword = quote(keyword)
    headers = build_headers(referer=f"https://search.bilibili.com/all?keyword={encoded_keyword}")
    proxies = get_proxies()
    try:
        resp = requests.get(
            "https://api.bilibili.com/x/web-interface/search/type",
            params=params,
            headers=headers,
            timeout=10,
            proxies=proxies,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"关键词搜索失败：{e}")
        return []

    result_items = data.get("data", {}).get("result", []) or []
    videos: List[Dict] = []
    for item in result_items:
        url = item.get("arcurl") or ""
        bvid = item.get("bvid") or ""
        if not url and bvid:
            url = f"https://www.bilibili.com/video/{bvid}"

        tags_str = item.get("tag", "") or ""
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]

        pub_ts = item.get("pubdate", 0) or 0
        try:
            import datetime

            pubdate = datetime.datetime.fromtimestamp(pub_ts).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pubdate = ""

        videos.append(
            {
                "type": item.get("type", "video"),
                "author": item.get("author", ""),
                "typename": item.get("typename", ""),
                "url": url,
                "title": (item.get("title") or "").replace('<em class="keyword">', "").replace("</em>", ""),
                "description": item.get("description") or "",
                "play": int(item.get("play") or 0),
                "danmaku": int(item.get("video_review") or 0),
                "favorites": int(item.get("favorites") or 0),
                "tags": tags,
                "comment_count": int(item.get("comment") or 0),
                "pubdate": pubdate,
                "aid": item.get("aid"),
                "bvid": bvid,
                "cid": item.get("cid"),
            }
        )
        if limit and len(videos) >= limit:
            break
    return videos


def build_pipeline_results(keywords: List[str], page: int = 1, limit: Optional[int] = None) -> List[Dict]:
    """
    模拟原 bilibili_detail_pipiline，返回 [{keyword, real_data}] 供向量化。
    real_data 为可读文本，每个视频一段。
    """
    all_results: List[Dict] = []
    for kw in keywords:
        vids = search_videos(kw, page=page, limit=limit)
        real_data = "\n\n".join(_format_video_text(v) for v in vids)
        all_results.append({"keyword": kw, "real_data": real_data})
    return all_results


if __name__ == "__main__":
    urls = []
    while True:
        url = input("请输入哔哩哔哩视频链接（输入空行结束）：").strip()
        if url == "":
            break
        urls.append(url)

    video_infos = []
    for url in urls:
        video_info = extract_bilibili_info(url)
        if video_info:
            print(f"成功提取视频信息：{video_info['标题']}")
            video_infos.append(video_info)
        else:
            print(f"无法提取视频信息：{url}")

    if video_infos:
        save_flag = input("是否保存到Excel? (y/n)：").strip().lower() == "y"
        if save_flag:
            save_to_excel(video_infos)
    else:
        print("没有成功提取任何视频信息。")
