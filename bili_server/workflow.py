#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""LangGraph workflow utilities (moved from app/utils, without LangServe)."""

import os
from typing import Optional

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from bili_server.document_loader import DocumentLoader
from bili_server.edges import EdgeGraph
from bili_server.graph import GraphState
from bili_server.grader import GraderUtils
from bili_server.nodes import GraphNodes


def _read_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def create_parser_components(
    chat_model: str,
    chat_api_key: Optional[str] = None,
    judge_model: Optional[str] = None,
    judge_api_key: Optional[str] = None,
):
    """创建并初始化解析/打分组件。"""
    retriever = DocumentLoader()

    base_url = os.getenv("SILICON_BASE_URL", "https://api.siliconflow.cn/v1")
    chat_key = chat_api_key or os.getenv("SILICON_CHAT_API_KEY") or os.getenv("SILICON_API_KEY")
    judge_key = judge_api_key or os.getenv("SILICON_API_KEY") or chat_key
    judge_model = judge_model or os.getenv("SILICON_JUDGE_MODEL", chat_model)

    llm = ChatOpenAI(base_url=base_url, api_key=judge_key, model=judge_model, temperature=0)
    llm_generate = ChatOpenAI(base_url=base_url, api_key=chat_key, model=chat_model, temperature=0)

    grader = GraderUtils(llm)
    retrieval_grader = grader.create_retrieval_grader()
    question_rewriter = grader.create_question_rewriter()

    return {
        "llm": llm_generate,  # 生成使用对话模型
        "retriever": retriever,# 文档检索器
        "retrieval_grader": retrieval_grader,
        "question_rewriter": question_rewriter,
    }


def create_workflow(
    model: str,
    chat_api_key: Optional[str] = None,
    judge_api_key: Optional[str] = None,
    dataset_ids=None,
    top_k: Optional[int] = None,
    similarity_threshold: Optional[float] = None,
):
    """构建 LangGraph 工作流。"""
    components = create_parser_components(
        chat_model=model,
        chat_api_key=chat_api_key,
        judge_model=os.getenv("SILICON_JUDGE_MODEL"),
        judge_api_key=judge_api_key,
    )
    llm, retriever, retrieval_grader, question_rewriter = components.values()

    workflow = StateGraph(GraphState)

    env_top_k = _read_int_env("VECTOR_TOP_K", 15)
    resolved_top_k = max(1, min(top_k if top_k is not None else env_top_k, 30))
    graph_nodes = GraphNodes(
        llm,
        retriever, # 文档检索器
        retrieval_grader, # 文档给llm打分器
        question_rewriter, # 问题重写器
        dataset_ids=dataset_ids,
        top_k=resolved_top_k,
        score_threshold=similarity_threshold,
    )

    edge_graph = EdgeGraph()

    workflow.add_node("retrieve", graph_nodes.retrieve)
    workflow.add_node("grade_documents", graph_nodes.grade_documents)
    workflow.add_node("generate", graph_nodes.generate)
    workflow.add_node("transform_query", graph_nodes.transform_query)

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_conditional_edges(
        "grade_documents",
        edge_graph.decide_to_generate,
        {
            "transform_query": "transform_query",
            "generate": "generate",
        },
    )
    workflow.add_edge("transform_query", "retrieve")
    workflow.add_edge("generate", END)  # 关闭幻觉检查后直接结束

    chain = workflow.compile()
    return chain


def visualize_workflow(save_path: str = "workflow_graph.png"):
    """生成并保存 LangGraph 工作流的可视化图表。"""
    from dotenv import load_dotenv, find_dotenv

    load_dotenv(find_dotenv())

    chain = create_workflow(
        os.getenv("SILICON_CHAT_MODEL", "deepseek-ai/DeepSeek-V3.2"),
        chat_api_key=os.getenv("SILICON_CHAT_API_KEY") or os.getenv("SILICON_API_KEY"),
        judge_api_key=os.getenv("SILICON_API_KEY"),
    )

    try:
        from IPython.display import Image, display

        graph_image = chain.get_graph().draw_mermaid_png()
        with open(save_path, "wb") as f:
            f.write(graph_image)
        try:
            display(Image(graph_image))
        except Exception:
            pass
        print(f"✅ 工作流图表已保存到 {save_path}")
    except Exception as exc:  # pragma: no cover - 辅助脚本的容错提示
        print(f"❌ 生成失败: {exc}")
        print("提示: 需要安装 graphviz/pygraphviz 才能生成图片")
