#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LangGraph 工作流可视化脚本 (Mermaid格式)
运行此脚本生成BiliAgent工作流的Mermaid图表代码
"""

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv, find_dotenv
from bili_server.workflow import create_workflow

load_dotenv(find_dotenv())

if __name__ == '__main__':
    print("=" * 60)
    print("BiliAgent 工作流可视化 (Mermaid)")
    print("=" * 60)
    
    # 创建工作流（硅基流动）
    chain = create_workflow(
        model=os.getenv('SILICON_CHAT_MODEL', 'deepseek-ai/DeepSeek-V3.2'),
        chat_api_key=os.getenv('SILICON_CHAT_API_KEY') or os.getenv('SILICON_API_KEY'),
        judge_api_key=os.getenv('SILICON_API_KEY'),
    )
    
    # 获取Mermaid图表代码
    try:
        mermaid_code = chain.get_graph().draw_mermaid()
        
        print("\nMermaid 图表代码:")
        print("-" * 60)
        print(mermaid_code)
        print("-" * 60)
        
        # 保存到文件
        with open("workflow_graph.mmd", "w", encoding="utf-8") as f:
            f.write(mermaid_code)
        
        print("\n✅ Mermaid代码已保存到: workflow_graph.mmd")
        print("\n使用方法:")
        print("1. 复制上面的代码")
        print("2. 访问 https://mermaid.live/")
        print("3. 粘贴代码即可查看可视化图表")
        print("4. 或使用支持Mermaid的Markdown编辑器")
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")
