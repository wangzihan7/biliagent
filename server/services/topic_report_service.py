#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 课题报告与可视化数据汇总（统计 + 会话关键回答）
import collections
import re
import os
import datetime
import concurrent.futures
from typing import List, Dict, Any

try:
    # 传统分词/TF-IDF 关键词提取
    import jieba.analyse  # type: ignore
except Exception:
    jieba = None

from sqlalchemy.orm import Session

from server.db.repository.topic_repository import TopicRepository
from server.db.repository.message_repository import MessageRepository
from server.db.repository.video_repository import VideoRepository
from server.exceptions import NotFoundError
from server.db.models.message_model import MessageModel
from server.db.models.conversation_model import ConversationModel

from langchain_openai import ChatOpenAI


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


# 非严格情感词典，仅用于大致统计
POS_WORDS = {"好", "棒", "喜欢", "满意", "推荐", "不错", "惊艳", "优秀", "开心", "值得"}
NEG_WORDS = {"差", "坑", "失望", "难吃", "不好", "垃圾", "生气", "糟糕", "一般", "黑心"}
STOP_WORDS = {
    "我们",
    "你们",
    "他们",
    "这个",
    "那个",
    "就是",
    "然后",
    "但是",
    "还是",
    "感觉",
    "真的",
    "有点",
    "非常",
    "比较",
    "已经",
}


def _tokenize(text: str) -> List[str]:
    """按非中英文和数字切分，并去掉停用词与过短 token。"""
    tokens = re.split(r"[^0-9A-Za-z\u4e00-\u9fa5]+", text)
    return [t for t in tokens if len(t) >= 2 and t not in STOP_WORDS]


def _sentiment_score(text: str) -> int:
    """极简情感得分：命中正面词 +1，负面词 -1。"""
    score = 0
    for w in POS_WORDS:
        if w in text:
            score += 1
    for w in NEG_WORDS:
        if w in text:
            score -= 1
    return score


def _collect_key_answers(
    db: Session,
    topic_id: str,
    max_per_conversation: int = 3,
    max_total: int = 50,
) -> List[Dict[str, Any]]:
    """
    收集课题下各会话的“关键回答”：
    - 优先使用消息 metadata 中的 is_important 标记（role == assistant）
    - 若无显式标记，则回退为该会话最后一条 assistant 消息
    """
    key_answers: List[Dict[str, Any]] = []

    conversations: List[ConversationModel] = TopicRepository.list_conversations(
        db, topic_id
    )
    for conv in conversations:
        # 取该会话的最近若干条消息，避免一次性加载过多历史
        messages: List[MessageModel] = MessageRepository.get_conversation_messages(
            db, conv.conversation_id, limit=200
        )
        # 显式标记的重要回复
        explicit: List[MessageModel] = []
        for m in messages:
            if m.role != "assistant":
                continue
            meta = m.meta_data or {}
            if isinstance(meta, dict) and meta.get("is_important"):
                explicit.append(m)

        if explicit:
            selected = explicit[:max_per_conversation]
        else:
            # 回退：选择该会话最后一条 assistant 消息
            selected: List[MessageModel] = []
            for m in reversed(messages):
                if m.role == "assistant":
                    selected = [m]
                    break

        for m in selected:
            key_answers.append(
                {
                    "conversation_id": m.conversation_id,
                    "conversation_name": getattr(conv, "conversation_name", None),
                    "message_id": m.message_id,
                    "role": m.role,
                    "content": m.content,
                    "created_at": str(m.create_time) if m.create_time else None,
                }
            )
            if len(key_answers) >= max_total:
                return key_answers

    return key_answers


def build_topic_report(
    db: Session,
    topic_id: str,
    comment_limit: int = 500,
    danmaku_limit: int = 500,
    max_key_answers: int = 50,
) -> Dict[str, Any]:
    """
    按课题聚合视频/评论/弹幕的基础统计，并补充会话关键回答和图表友好数据结构。
    """
    topic = TopicRepository.get_topic(db, topic_id)
    if not topic:
        raise NotFoundError("课题不存在")
    datasets = TopicRepository.list_datasets(db, topic_id)
    if not datasets:
        raise NotFoundError("课题下暂无数据集")
    dataset_ids = [d.dataset_id for d in datasets]

    # 拉取视频
    videos = VideoRepository.list_videos_by_dataset_ids(db, dataset_ids)

    total_comments = 0
    total_danmaku = 0
    tag_counter = collections.Counter()
    keyword_counter = collections.Counter()
    sentiment_counter = collections.Counter()
    trend_counter = collections.Counter()
    corpus_texts: List[str] = []

    for v in videos:
        # tags
        if v.tags:
            for t in [x.strip() for x in v.tags.split(",") if x.strip()]:
                tag_counter[t] += 1

        # 标题与描述也参与关键词统计
        for txt in [getattr(v, "title", "") or "", getattr(v, "description", "") or ""]:
            if not txt:
                continue
            corpus_texts.append(txt)
            for tok in _tokenize(txt):
                keyword_counter[tok] += 1
            s = _sentiment_score(txt)
            if s > 0:
                sentiment_counter["positive"] += 1
            elif s < 0:
                sentiment_counter["negative"] += 1
            else:
                sentiment_counter["neutral"] += 1

        # trend by pubdate
        if getattr(v, "pubdate", None):
            try:
                date_key = v.pubdate.date().isoformat()
            except Exception:
                continue
            trend_counter[date_key] += 1

        # comments
        comments = VideoRepository.list_video_comments(db, v.id, limit=comment_limit)
        for txt in comments:
            txt = txt or ""
            total_comments += 1
            corpus_texts.append(txt)
            for tok in _tokenize(txt):
                keyword_counter[tok] += 1
            s = _sentiment_score(txt)
            if s > 0:
                sentiment_counter["positive"] += 1
            elif s < 0:
                sentiment_counter["negative"] += 1
            else:
                sentiment_counter["neutral"] += 1

        # danmaku
        danmakus = VideoRepository.list_video_danmaku(db, v.id, limit=danmaku_limit)
        for text, _progress in danmakus:
            txt = text or ""
            total_danmaku += 1
            corpus_texts.append(txt)
            for tok in _tokenize(txt):
                keyword_counter[tok] += 1
            s = _sentiment_score(txt)
            if s > 0:
                sentiment_counter["positive"] += 1
            elif s < 0:
                sentiment_counter["negative"] += 1
            else:
                sentiment_counter["neutral"] += 1

    # Top 列表（频次 + TF-IDF 结合）
    top_tag_items = tag_counter.most_common(20)
    freq_keyword_items = keyword_counter.most_common(200)

    tfidf_keywords: List[str] = []
    if "jieba" in globals() and jieba and corpus_texts:
        try:
            tfidf_keywords = jieba.analyse.extract_tags(
                "\n".join(corpus_texts), topK=100, withWeight=False
            )
        except Exception:
            tfidf_keywords = []

    combined_keywords: List[str] = []
    for w, _ in freq_keyword_items:
        if w not in combined_keywords:
            combined_keywords.append(w)
        if len(combined_keywords) >= 120:
            break
    for w in tfidf_keywords:
        if w not in combined_keywords:
            combined_keywords.append(w)
        if len(combined_keywords) >= 120:
            break

    top_tags = [t for t, _ in top_tag_items]
    top_keywords = combined_keywords[:30]

    # 文本总结（基础版）
    summary_parts: List[str] = [
        f"课题《{topic.name}》共关联数据集 {len(dataset_ids)} 个，视频 {len(videos)} 条，",
        f"累计评论 {total_comments} 条、弹幕 {total_danmaku} 条。",
    ]
    if top_tags:
        summary_parts.append("主要标签：" + ", ".join(top_tags[:10]) + "。")
    if top_keywords:
        summary_parts.append("高频词：" + ", ".join(top_keywords[:10]) + "。")
    summary = " ".join(summary_parts)

    # 时间趋势
    trend = [
        {"date": k, "count": trend_counter[k]} for k in sorted(trend_counter.keys())
    ]

    # 图表友好格式（前端可以直接喂给 ECharts/AntV 等）
    sentiment_chart = [
        {"name": "positive", "value": sentiment_counter.get("positive", 0)},
        {"name": "neutral", "value": sentiment_counter.get("neutral", 0)},
        {"name": "negative", "value": sentiment_counter.get("negative", 0)},
    ]
    tag_chart = [{"name": t, "value": c} for t, c in top_tag_items]
    keyword_chart_items: List[Dict[str, Any]] = []
    for w in combined_keywords[:80]:
        keyword_chart_items.append({"name": w, "value": keyword_counter.get(w, 1)})
    keyword_chart = keyword_chart_items

    # 会话关键回答（供报告或 LLM 总结使用）
    key_answers = _collect_key_answers(db, topic_id, max_total=max_key_answers)

    return {
        "topic_id": topic.topic_id,
        "topic_name": topic.name,
        "summary": summary,
        "totals": {
            "datasets": len(dataset_ids),
            "videos": len(videos),
            "comments": total_comments,
            "danmaku": total_danmaku,
        },
        "top_tags": top_tags,
        "top_keywords": top_keywords,
        "sentiment": {
            "positive": sentiment_counter.get("positive", 0),
            "negative": sentiment_counter.get("negative", 0),
            "neutral": sentiment_counter.get("neutral", 0),
        },
        "trend": trend,
        "key_answers": key_answers,
        "charts": {
            "sentiment": sentiment_chart,
            "top_tags": tag_chart,
            "top_keywords": keyword_chart,
            "trend": trend,
        },
    }


def build_llm_summary(report: Dict[str, Any]) -> str:
    """
    调用 LLM 生成更自然的摘要；若缺少配置或调用失败则返回空字符串。
    使用硅基流动模型。
    """
    if not _env_bool("TOPIC_REPORT_LLM_SUMMARY", True):
        return ""
    timeout_sec = _read_int_env("TOPIC_REPORT_LLM_TIMEOUT_SEC", 120)
    prompt = (
        "请根据以下课题统计信息，用中文生成一段简洁的总结，"
        "涵盖总体规模、热门标签和关键词、情感倾向（大致正向/负向）、"
        "时间趋势，以及几个关键回答的要点。\n"
        f"统计数据: {report}"
    )
    try:
        silicon_key = os.getenv("SILICON_API_KEY")
        if not silicon_key:
            print("[topic_report] llm_summary skipped: missing SILICON_API_KEY")
            return ""
        base_url = os.getenv("SILICON_BASE_URL", "https://api.siliconflow.cn/v1")
        model = os.getenv("SILICON_CHAT_MODEL", "deepseek-ai/DeepSeek-V3.2")
        started_at = datetime.datetime.utcnow()
        print(
            f"[topic_report] llm_summary start model={model} timeout={timeout_sec}s prompt_len={len(prompt)}"
        )
        llm = ChatOpenAI(
            base_url=base_url,
            api_key=silicon_key,
            model=model,
            temperature=0.2,
        )
        if timeout_sec <= 0:
            result = llm.invoke(prompt)
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(llm.invoke, prompt)
                try:
                    result = future.result(timeout=timeout_sec)
                except concurrent.futures.TimeoutError:
                    print(f"[topic_report] llm_summary timeout after {timeout_sec}s")
                    return ""
        # 智谱 / OpenAI 均返回类 ChatMessage 对象，这里做一个宽松兼容
        content = getattr(result, "content", None)
        if isinstance(content, str):
            elapsed = (datetime.datetime.utcnow() - started_at).total_seconds()
            print(f"[topic_report] llm_summary done chars={len(content)} elapsed={elapsed:.2f}s")
            return content
        # 可能是 list[dict] 等结构时，做一个简单拼接
        if isinstance(content, list):
            try:
                joined = "".join(str(x) for x in content)
                elapsed = (datetime.datetime.utcnow() - started_at).total_seconds()
                print(f"[topic_report] llm_summary done chars={len(joined)} elapsed={elapsed:.2f}s")
                return joined
            except Exception:
                print("[topic_report] llm_summary parse error: list content")
                return ""
        return ""
    except Exception as exc:
        print(f"[topic_report] llm_summary error: {exc}")
        return ""


def render_topic_report_markdown(report: Dict[str, Any], llm_summary: str = "") -> str:
    """
    将课题报告渲染为 Markdown 文本，用于前端展示或浏览器打印为 PDF。
    模板结构：
    - 封面：标题 + 时间 + 基本统计
    - 目录
    - 一、课题概览
    - 二、统计概览
    - 三、标签与高频词
    - 四、情感与时间趋势
    - 五、关键回答摘录
    """
    lines: List[str] = []

    topic_name = report.get("topic_name", "")
    topic_id = report.get("topic_id", "")
    totals = report.get("totals", {}) or {}
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # 封面
    lines.append(f"# 课题报告：{topic_name}")
    lines.append("")
    lines.append(f"> 生成时间：{now_str}  ")
    lines.append(f"> 课题ID：`{topic_id}`  ")
    lines.append(
        f"> 数据集：{totals.get('datasets', 0)} 个｜视频：{totals.get('videos', 0)} 条｜"
        f"评论：{totals.get('comments', 0)} 条｜弹幕：{totals.get('danmaku', 0)} 条"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    # 目录
    lines.append("## 目录")
    lines.append("1. 课题概览")
    lines.append("2. 统计概览")
    lines.append("3. 标签与高频词")
    lines.append("4. 情感与时间趋势")
    lines.append("5. 关键回答摘录")
    lines.append("")

    # 一、课题概览
    lines.append("## 一、课题概览")
    lines.append(report.get("summary", "（暂无统计概要）"))
    lines.append("")

    if llm_summary:
        lines.append("### LLM 总结")
        lines.append(llm_summary)
        lines.append("")

    # 二、统计概览
    lines.append("## 二、统计概览")
    lines.append("")
    lines.append("| 指标 | 数量 |")
    lines.append("| ---- | ---- |")
    lines.append(f"| 数据集数 | {totals.get('datasets', 0)} |")
    lines.append(f"| 视频数 | {totals.get('videos', 0)} |")
    lines.append(f"| 评论数 | {totals.get('comments', 0)} |")
    lines.append(f"| 弹幕数 | {totals.get('danmaku', 0)} |")
    lines.append("")

    # 三、标签与高频词
    top_tags = report.get("top_tags") or []
    top_keywords = report.get("top_keywords") or []

    lines.append("## 三、标签与高频词")
    lines.append("")
    if top_tags:
        lines.append("**主要标签**")
        lines.append(", ".join(top_tags))
        lines.append("")
    if top_keywords:
        lines.append("**高频词**")
        lines.append(", ".join(top_keywords))
        lines.append("")
    if not top_tags and not top_keywords:
        lines.append("暂无可统计的标签或高频词。")
        lines.append("")

    # 四、情感与时间趋势
    lines.append("## 四、情感与时间趋势")
    lines.append("")

    sentiment = report.get("sentiment") or {}
    if sentiment:
        lines.append("### 情感分布")
        lines.append("")
        lines.append("| 情感 | 数量 |")
        lines.append("| ---- | ---- |")
        lines.append(f"| 正向 | {sentiment.get('positive', 0)} |")
        lines.append(f"| 中性 | {sentiment.get('neutral', 0)} |")
        lines.append(f"| 负向 | {sentiment.get('negative', 0)} |")
        lines.append("")
    else:
        lines.append("暂无情感统计数据。")
        lines.append("")

    trend = report.get("trend") or []
    if trend:
        lines.append("### 时间趋势（视频发布量）")
        lines.append("")
        lines.append("| 日期 | 视频数 |")
        lines.append("| ---- | ------ |")
        for item in trend:
            lines.append(f"| {item.get('date', '')} | {item.get('count', 0)} |")
        lines.append("")
    else:
        lines.append("暂无时间趋势数据。")
        lines.append("")

    # 五、关键回答摘录
    key_answers = report.get("key_answers") or []
    lines.append("## 五、关键回答摘录")
    if key_answers:
        for idx, ans in enumerate(key_answers, start=1):
            conv_name = ans.get("conversation_name") or ans.get(
                "conversation_id", ""
            )
            created_at = ans.get("created_at") or ""
            lines.append(f"### 关键回答 {idx}")
            lines.append(f"- 会话：`{conv_name}`")
            if created_at:
                lines.append(f"- 时间：{created_at}")
            lines.append("")
            lines.append(ans.get("content", ""))
            lines.append("")
    else:
        lines.append("暂无被标记为“关键回答”的内容。")
        lines.append("")

    return "\n".join(lines)
