#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Async topic report generation (in-memory task store).

from __future__ import annotations

import datetime
import threading
import uuid
from typing import Any, Dict, Optional

from server.db.session import get_db
from server.schemas.topic import TopicReportResponse
from server.services.topic_report_service import build_topic_report, build_llm_summary


_TASKS: Dict[str, Dict[str, Any]] = {}
_TOPIC_TO_TASK: Dict[str, str] = {}
_LOCK = threading.Lock()


def _now() -> str:
    return datetime.datetime.utcnow().isoformat()


def _to_report_response(report: Dict[str, Any], llm_summary: str) -> Dict[str, Any]:
    response = TopicReportResponse(
        topic_id=report["topic_id"],
        topic_name=report["topic_name"],
        summary=report["summary"],
        llm_summary=llm_summary or None,
        totals=report["totals"],
        top_tags=report["top_tags"],
        top_keywords=report["top_keywords"],
        sentiment=report["sentiment"],
        trend=report["trend"],
        key_answers=report.get("key_answers", []),
        charts=report.get("charts"),
    )
    return response.dict()


def create_task(topic_id: str, force: bool = False) -> Dict[str, Any]:
    with _LOCK:
        existing_id = _TOPIC_TO_TASK.get(topic_id)
        if existing_id and not force:
            existing = _TASKS.get(existing_id)
            if existing and existing.get("status") in {"pending", "running", "success"}:
                return dict(existing)

        task_id = str(uuid.uuid4())
        task = {
            "task_id": task_id,
            "topic_id": topic_id,
            "status": "pending",
            "created_at": _now(),
            "updated_at": _now(),
            "error": None,
            "report": None,
        }
        _TASKS[task_id] = task
        _TOPIC_TO_TASK[topic_id] = task_id
        return dict(task)


def get_task_for_topic(topic_id: str) -> Optional[Dict[str, Any]]:
    with _LOCK:
        task_id = _TOPIC_TO_TASK.get(topic_id)
        if not task_id:
            return None
        task = _TASKS.get(task_id)
        return dict(task) if task else None


def run_task(task_id: str) -> None:
    with _LOCK:
        task = _TASKS.get(task_id)
        if not task or task.get("status") not in {"pending", "failed"}:
            return
        task["status"] = "running"
        task["updated_at"] = _now()

    try:
        with get_db() as db:
            report = build_topic_report(db, task["topic_id"])
            llm_summary = build_llm_summary(report)
            report_payload = _to_report_response(report, llm_summary)
        with _LOCK:
            task = _TASKS.get(task_id)
            if not task:
                return
            task["status"] = "success"
            task["report"] = report_payload
            task["error"] = None
            task["updated_at"] = _now()
    except Exception as exc:
        with _LOCK:
            task = _TASKS.get(task_id)
            if not task:
                return
            task["status"] = "failed"
            task["error"] = str(exc)
            task["updated_at"] = _now()
