import json
import os
import time
from datetime import datetime
from typing import List, Tuple

import pandas as pd
import requests

try:
    from .config import build_headers, get_proxies, default_output_dir, sanitize_filename
except ImportError:  # pragma: no cover - fallback for direct script run
    from config import build_headers, get_proxies, default_output_dir, sanitize_filename


def get_bilibili_comments(
    oid, pn: int = 1, type: int = 1, page_size: int = 20, timeout: int = 10
) -> Tuple[List, int]:
    """
    拉取指定页面的评论。
    """
    url = "https://api.bilibili.com/x/v2/reply"
    params = {"pn": pn, "ps": page_size, "type": type, "oid": oid, "sort": 2}
    headers = build_headers(referer="https://www.bilibili.com/video/")
    proxies = get_proxies()

    response = requests.get(url, headers=headers, params=params, timeout=timeout, proxies=proxies)

    if response.status_code == 200:
        data = json.loads(response.text)
        replies = data.get("data", {}).get("replies", []) or []
        total = data.get("data", {}).get("page", {}).get("count", 0)
        return replies, total
    else:
        print(f"获取评论失败，状态码：{response.status_code}")
        return [], 0


def get_replies(
    oid,
    root,
    pn: int = 1,
    type: int = 1,
    page_size: int = 10,
    timeout: int = 10,
):
    """
    拉取二级回复。
    """
    url = "https://api.bilibili.com/x/v2/reply/reply"
    params = {"oid": oid, "pn": pn, "ps": page_size, "root": root, "type": type}
    headers = build_headers(referer="https://www.bilibili.com/video/")
    proxies = get_proxies()

    response = requests.get(url, headers=headers, params=params, timeout=timeout, proxies=proxies)

    if response.status_code == 200:
        data = json.loads(response.text)
        return data.get("data", {}).get("replies", []) or []
    else:
        print(f"获取回复失败，状态码：{response.status_code}")
        return []


def save_comments_to_excel(title, comments, save_path=None):
    current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    if not save_path:
        save_path = str(default_output_dir("comments"))

    clean_title = sanitize_filename(title)
    file_name = f"{clean_title}-评论--{current_time}.xlsx"
    file_path = os.path.join(save_path, file_name)

    all_comments = []
    for comment in comments:
        all_comments.append(
            {
                "用户": comment["member"]["uname"],
                "内容": comment["content"]["message"],
                "时间": time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(comment["ctime"])
                ),
                "点赞数": comment["like"],
                "层级": "一级评论",
            }
        )

        if "replies" in comment and comment["replies"]:
            for reply in comment["replies"]:
                all_comments.append(
                    {
                        "用户": reply["member"]["uname"],
                        "内容": reply["content"]["message"],
                        "时间": time.strftime(
                            "%Y-%m-%d %H:%M:%S", time.localtime(reply["ctime"])
                        ),
                        "点赞数": reply["like"],
                        "层级": "二级回复",
                    }
                )

    if save_path:
        df = pd.DataFrame(all_comments)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        try:
            df.to_excel(file_path, index=False, engine="openpyxl")
            print(f"评论已保存至 {file_path}")
        except PermissionError:
            print(
                f"无法保存文件，可能是因为文件 {file_path} 已经打开。请关闭文件后重试。"
            )
        except Exception as e:
            print(f"保存文件时发生错误：{str(e)}")
        return file_path
    return None


def process_video(
    oid,
    title,
    save_path=None,
    max_pages=None,
    max_comments=None,
    max_replies=3,
    page_size=20,
    reply_page_size=10,
    delay_seconds=1.0,
):
    """
    爬取单个视频的评论。

    Args:
        oid: 视频 AID 或 BVID
        title: 视频标题
        save_path: 传入路径则保存为 Excel；为 None 则只返回数据
        max_pages: 限制最大页数（None 表示不限制）
        max_comments: 限制最大一级评论数（None 表示不限制）
        max_replies: 每条评论抓取的二级回复上限（0 表示不抓取回复）
        page_size: 评论页大小
        reply_page_size: 回复页大小
        delay_seconds: 每页抓取间隔，避免过于频繁
    """
    all_comments = []
    page = 1
    total = 0
    while True:
        if max_pages and page > max_pages:
            break

        comments, total = get_bilibili_comments(
            oid, page, page_size=page_size
        )
        if not comments:
            break

        for comment in comments:
            if max_comments and len(all_comments) >= max_comments:
                break

            if comment.get("rcount", 0) > 0 and max_replies != 0:
                replies = get_replies(
                    oid,
                    comment["rpid"],
                    page_size=reply_page_size,
                )
                if max_replies and len(replies) > max_replies:
                    replies = replies[:max_replies]
                comment["replies"] = replies
            all_comments.append(comment)

        print(f"已获取{len(all_comments)}/{total} 条评论")

        if max_comments and len(all_comments) >= max_comments:
            break

        page += 1
        time.sleep(delay_seconds)  # 避免请求过于频繁

    if save_path is None:
        save_path = str(default_output_dir("comments"))

    save_comments_to_excel(title, all_comments, save_path)
    print(f"共获取到 {len(all_comments)} 条一级评论及其回复")
    return all_comments


def main():
    video_info_file = input("请输入视频信息Excel文件的路径：")
    save_path = input("请输入评论保存目录（留空则不保存）：").strip() or None
    if save_path and not os.path.exists(save_path):
        os.makedirs(save_path)

    # 读取Excel文件
    df = pd.read_excel(video_info_file)

    # 遍历每一行
    for _, row in df.iterrows():
        oid = row["AID"] if "AID" in row else row["BVID"]
        title = row["标题"]
        print(f"正在处理视频：{title}")
        process_video(oid, title, save_path, max_pages=5, max_replies=3)
        print(f"视频 {title} 的评论爬取完成")
        time.sleep(2)  # 在处理下一个视频之前稍作暂停

    print("所有视频的评论爬取完成")


if __name__ == "__main__":
    main()
