#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 数据库初始化脚本

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from server.db.base import Base
from server.db.session import engine

# 导入模型包，让所有模型类注册到 Base.metadata。
# 只要 import 这个包，server/db/models/__init__.py 里列出的
# 全部 16 个模型都会被加载并登记，create_all 才能建全所有表。
# （不要在这里手写模型名单——加了新表容易忘记同步。）
import server.db.models  # noqa: F401


def init_database():
    """初始化数据库表"""
    print("开始创建数据库表...")
    try:
        Base.metadata.create_all(bind=engine)
        # 从 metadata 里读实际结果，而不是手写死表名 ——
        # 以后加了新表也会自动出现在这个清单里，不会脱节。
        tables = sorted(Base.metadata.tables.keys())
        print(f"数据库表创建成功，共 {len(tables)} 张:")
        for name in tables:
            print(f"  - {name}")
    except Exception as e:
        print(f"数据库表创建失败: {str(e)}")
        raise


def drop_all_tables():
    """删除所有表(谨慎使用!)"""
    print("[警告] 将删除所有数据库表，数据无法恢复!")
    confirm = input("确认删除? (yes/no): ")
    if confirm.lower() == "yes":
        try:
            Base.metadata.drop_all(bind=engine)
            print("所有表已删除")
        except Exception as e:
            print(f"删除表失败: {str(e)}")
            raise
    else:
        print("取消操作")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="数据库管理工具")
    parser.add_argument("--drop", action="store_true", help="删除所有表")
    parser.add_argument("--init", action="store_true", help="初始化数据库表")

    args = parser.parse_args()

    if args.drop:
        drop_all_tables()

    if args.init or (not args.drop):
        init_database()
