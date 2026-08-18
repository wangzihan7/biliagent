#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 数据库会话管理

import os
from contextlib import contextmanager

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv(find_dotenv())

# 从环境变量读取数据库配置（默认值保持旧版兼容）
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "123456")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "bilibili_analysis")

SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@"
    f"{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    f"?charset=utf8mb4"
)

POOL_SIZE = int(os.getenv("MYSQL_POOL_SIZE", 10))
MAX_OVERFLOW = int(os.getenv("MYSQL_MAX_OVERFLOW", 20))
POOL_RECYCLE = int(os.getenv("MYSQL_POOL_RECYCLE", 3600))
POOL_PRE_PING = os.getenv("MYSQL_POOL_PRE_PING", "true").lower() == "true"

# 创建数据库引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_recycle=POOL_RECYCLE,
    pool_pre_ping=POOL_PRE_PING,
    echo=False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_db_session():
    """FastAPI依赖注入使用的数据库会话获取函数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
