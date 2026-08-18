#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LangGraph 工作流可视化脚本
运行此脚本生成BiliAgent工作流的可视化图表
"""

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from bili_server.workflow import visualize_workflow

if __name__ == '__main__':
    print("=" * 60)
    print("BiliAgent 工作流可视化")
    print("=" * 60)
    
    # 生成图表
    output_path = "bili_agent_workflow.png"
    visualize_workflow(output_path)
    
    print("\n提示:")
    print("1. 如果生成失败,请先安装依赖: pip install pygraphviz")
    print("2. Windows用户可能需要安装 Graphviz: https://graphviz.org/download/")
    print("3. 图表文件位置:", os.path.abspath(output_path))
