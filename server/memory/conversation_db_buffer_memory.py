#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 基于数据库的对话记忆管理

from typing import List, Dict, Any
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from server.db.session import get_db
from server.db.repository.message_repository import MessageRepository
from server.db.repository.conversation_repository import ConversationRepository


class ConversationDBBufferMemory:
    """基于数据库的对话记忆管理"""
    
    def __init__(self, conversation_id: str, user_id: str, 
                 max_token_limit: int = 2000, max_messages: int = 20):
        """
        初始化记忆管理器
        
        Args:
            conversation_id: 会话ID
            user_id: 用户ID
            max_token_limit: 最大token限制
            max_messages: 最大消息数量
        """
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.max_token_limit = max_token_limit
        self.max_messages = max_messages
    
    def save_context(self, human_input: str, ai_output: str, metadata: Dict = None):
        """保存对话上下文到数据库(单一事务,避免锁竞争)"""
        with get_db() as db:
            # 保存用户消息
            MessageRepository.add_message(
                db=db,
                conversation_id=self.conversation_id,
                user_id=self.user_id,
                role='user',
                content=human_input,
                metadata=metadata
            )
            # 保存AI回复
            MessageRepository.add_message(
                db=db,
                conversation_id=self.conversation_id,
                user_id=self.user_id,
                role='assistant',
                content=ai_output,
                metadata=metadata
            )
            # 更新会话的最后修改时间
            ConversationRepository.touch_conversation(db, self.conversation_id)
    
    def load_memory_variables(self) -> List[BaseMessage]:
        """从数据库加载历史消息"""
        with get_db() as db:
            messages = MessageRepository.get_recent_messages(
                db=db,
                conversation_id=self.conversation_id,
                limit=self.max_messages
            )
            
            result = []
            for msg in messages:
                if msg.role == 'user':
                    result.append(HumanMessage(content=msg.content))
                elif msg.role == 'assistant':
                    result.append(AIMessage(content=msg.content))
                elif msg.role == 'system':
                    result.append(SystemMessage(content=msg.content))
            
            return result
    
    def get_history_text(self, num_rounds: int = 6) -> str:
        """获取历史对话文本，保证一轮里用户在前、助手在后。"""
        messages = self.load_memory_variables()

        # 按轮配对：同一轮中先用户再助手；若缺少某一方也能兼容
        turns = []
        current_turn: Dict[str, str] = {}
        for msg in messages:
            if isinstance(msg, HumanMessage):
                # 开启新一轮
                if current_turn:
                    turns.append(current_turn)
                current_turn = {"user": msg.content}
            elif isinstance(msg, AIMessage):
                if "assistant" in current_turn:
                    # 该轮已有助手回复，另起一轮以免覆盖
                    turns.append(current_turn)
                    current_turn = {}
                current_turn.setdefault("assistant", msg.content)
        if current_turn:
            turns.append(current_turn)

        # 只保留最近 N 轮
        recent_turns = turns[-num_rounds:] if len(turns) > num_rounds else turns

        history_lines = []
        for turn in recent_turns:
            if "user" in turn:
                history_lines.append(f"用户: {turn['user']}")
            if "assistant" in turn:
                history_lines.append(f"助手: {turn['assistant']}")

        return "\n".join(history_lines) + ("\n" if history_lines else "")
    
    def clear(self):
        """清空当前会话的消息"""
        with get_db() as db:
            MessageRepository.delete_conversation_messages(db, self.conversation_id)
