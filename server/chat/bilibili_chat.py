#!/usr/bin/env python
# -*- coding: utf-8 -*-
# B站数据分析聊天服务
import os
import sys
import time
from typing import Dict, Any, AsyncIterable, Optional

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from server.memory.conversation_db_buffer_memory import ConversationDBBufferMemory
from server.db.session import get_db
from server.db.repository.conversation_repository import ConversationRepository
from server.db.repository.keyword_repository import KeywordRepository
from bili_server.workflow import create_workflow


class BilibiliAnalysisChat:
    """B站数据分析聊天 Agent。"""

    def __init__(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        dataset_ids: Optional[list] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
    ):
        self.user_id = user_id
        self.api_key = api_key or os.getenv("SILICON_CHAT_API_KEY") or os.getenv("SILICON_API_KEY")
        self.model = model or os.getenv("SILICON_CHAT_MODEL", "deepseek-ai/DeepSeek-V3.2")
        self.dataset_ids = dataset_ids
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

        # 获取或创建会话（只保留必要字段，避免 Session 关闭后访问 ORM 对象报错）
        with get_db() as db:
            if conversation_id:
                conversation = ConversationRepository.get_conversation_by_id(
                    db, conversation_id
                )
                if not conversation or conversation.user_id != user_id:
                    raise ValueError("会话不存在或无权访问")
            else:
                conversation = ConversationRepository.create_conversation(
                    db=db,
                    user_id=user_id,
                    conversation_name="B站数据分析对话",
                )

            # 在 Session 仍然有效时取出原始字段，避免延迟加载
            self.conversation_id = conversation.conversation_id
            self.conversation_name = conversation.conversation_name

        # 初始化记忆管理（默认保留更多轮次，配置在类内部）
        self.memory = ConversationDBBufferMemory(
            conversation_id=self.conversation_id,
            user_id=self.user_id,
        )

        # 创建工作流（LangGraph Agent）
        self.workflow = create_workflow(
            model=self.model,
            chat_api_key=self.api_key,
            judge_api_key=os.getenv("SILICON_API_KEY"),
            dataset_ids=self.dataset_ids,
            top_k=self.top_k,
            similarity_threshold=self.similarity_threshold,
        )

    async def chat(self, query: str) -> AsyncIterable[Dict[str, Any]]:
        """执行聊天，逐 token 流式输出。"""
        start_time = time.perf_counter()
        final_generation = ""
        state: Dict[str, Any] = {} # 用于 累积收集 各节点的输出结果
        history_text = self.memory.get_history_text()

        try:
            inputs = {"input": query, "history": history_text}

            async for event in self.workflow.astream_events(inputs, version="v2"):
                kind = event["event"]
                node = event.get("metadata", {}).get("langgraph_node", "")

                # LLM生成token
                if kind == "on_chat_model_stream" and node == "generate":
                     # 只处理 generate 节点的 LLM token 流
                    token = getattr(event["data"]["chunk"], "content", "") or ""
                    if token:
                        final_generation += token
                        yield {"type": "generation", "content": token, "node": "generate"}

                elif kind == "on_chain_end":
                    output = event.get("data", {}).get("output")
                    if isinstance(output, dict):
                        state.update(output)

            latency_ms = int((time.perf_counter() - start_time) * 1000)
            final_question = state.get("final_question") or query
            metrics = {
                "latency_ms": latency_ms,
                "prompt_tokens_est": len(final_question) + len(history_text or ""),
                "completion_tokens_est": len(final_generation),
                "total_tokens_est": len(final_question) + len(history_text or "") + len(final_generation),
            }

            self.memory.save_context(query, final_generation, {
                "documents_preview": str(state.get("documents", ""))[:500],
                "query_type": "bilibili_analysis",
                "metrics": metrics,
                "prompt_preview": str(state.get("prompt", ""))[:1000],
                "prompt_length": state.get("prompt_length", 0),
                "retrieval_query": state.get("retrieval_query", ""),
                "history_preview": (history_text or "")[:500],
                "final_question": final_question,
            })

            with get_db() as db:
                KeywordRepository.add_keyword_extraction(
                    db=db,
                    conversation_id=self.conversation_id,
                    user_id=self.user_id,
                    original_question=query,
                    extracted_keywords=query[:100],
                )

            yield {"type": "done", "content": "[DONE]", "metrics": metrics}

        except Exception as e:
            yield {"type": "error", "content": f"处理失败: {str(e)}"}

    def get_conversation_info(self) -> Dict[str, Any]:
        """获取会话信息"""
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "conversation_name": self.conversation_name,
        }
