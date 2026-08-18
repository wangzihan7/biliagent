import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional

import pandas as pd
import requests

try:
    from .config import build_headers, get_proxies, default_output_dir, sanitize_filename
except ImportError:  # pragma: no cover - fallback for direct script run
    from config import build_headers, get_proxies, default_output_dir, sanitize_filename


def get_bilibili_danmaku(
    cid: str,
    referer: Optional[str] = None,
    timeout: int = 10,
    max_items: Optional[int] = None,
) -> List[str]:
    """
    获取单个 cid 的弹幕，返回文本列表。
    """
    url = f"https://comment.bilibili.com/{cid}.xml"
    headers = build_headers(referer=referer or "https://www.bilibili.com")
    proxies = get_proxies()

    response = requests.get(url, headers=headers, timeout=timeout, proxies=proxies)
    response.encoding = "utf-8"

    if response.status_code != 200:
        print(f"获取弹幕失败，状态码：{response.status_code}")
        return []

    root = ET.fromstring(response.text)
    danmaku_list = [d.text for d in root.findall("d") if d.text]  # type: ignore

    if max_items is not None:
        danmaku_list = danmaku_list[:max_items]
    return danmaku_list


def save_danmaku(title: str, danmaku: List[str], save_path: Optional[str] = None):
    if not save_path:
        save_path = str(default_output_dir("danmaku"))

    current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    os.makedirs(save_path, exist_ok=True)

    # 清理文件名
    clean_title = sanitize_filename(title)
    file_name = f"{clean_title}-弹幕-{current_time}.txt"
    file_path = os.path.join(save_path, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        for d in danmaku:
            f.write(d + "\n")

    print(f"共获取到 {len(danmaku)} 条弹幕，已保存至 {file_path}")
    return file_path


def process_video_danmaku(
    title: str,
    cid: str,
    save_path: Optional[str] = None,
    referer: Optional[str] = None,
    max_items: Optional[int] = None,
):
    """
    拉取单个视频的弹幕。
    """
    print(f"正在处理视频：{title}")
    danmaku = get_bilibili_danmaku(str(cid), referer=referer, max_items=max_items)
    file_path = save_danmaku(title, danmaku, save_path)
    print(f"视频 {title} 的弹幕爬取完成")
    return {"title": title, "danmaku": danmaku, "file_path": file_path}


def process_excel_danmaku(
    excel_path: str,
    save_path: Optional[str] = None,
    max_items: Optional[int] = None,
) -> List[dict]:
    df = pd.read_excel(excel_path)
    results = []

    for _, row in df.iterrows():
        title = row["标题"]
        cid = row["CID"]
        result = process_video_danmaku(
            title,
            cid,
            save_path=save_path,
            referer=row.get("链接") if isinstance(row, dict) else None,
            max_items=max_items,
        )
        results.append(result)

    return results


def main(excel_path: str, save_path: Optional[str] = None, max_items: Optional[int] = None):
    """
    处理Excel文件中的视频信息，抓取并（可选）保存弹幕。
    """
    results = process_excel_danmaku(excel_path, save_path, max_items)
    print("所有视频的弹幕处理完成")
    return results


if __name__ == "__main__":
    excel_path = input("请输入视频信息Excel文件的路径：")
    save_path = input("请输入弹幕保存目录（留空使用默认目录）：").strip() or None
    max_items_str = input("限制弹幕条数（留空为不限制）：").strip() or None
    max_items = int(max_items_str) if max_items_str else None
    main(excel_path, save_path, max_items)
