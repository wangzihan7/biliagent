#!/usr/bin/env python
# -*- coding: utf-8 -*-
# API 路由入口：聚合拆分后的各领域路由

from fastapi import APIRouter

from server.routers.auth_routes import router as auth_router
from server.routers.chat_routes import router as chat_router
from server.routers.crawl_routes import router as crawl_router
from server.routers.dataset_routes import router as dataset_router
from server.routers.topic_routes import router as topic_router
from server.routers.log_routes import router as log_router

router = APIRouter()

# 用户/认证
router.include_router(auth_router)
# 会话/聊天/关键词/创意
router.include_router(chat_router)
# 爬虫与任务
router.include_router(crawl_router)
# 数据集
router.include_router(dataset_router)
# 课题
router.include_router(topic_router)
# 日志
router.include_router(log_router)

