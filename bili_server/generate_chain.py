#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: MuyuCheney
# Date: 2024-10-15

import os
from textwrap import dedent

from dotenv import load_dotenv, find_dotenv
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv(find_dotenv())

# 结构化的生成提示词，清晰区分上下文/历史/当前问题
GENERATE_TEMPLATE = dedent(
    """
你是名为「哔哩哔哩」的中文助理，只能依据提供的上下文回答，不得编造。

【已知信息】
- 检索上下文（仅能引用这里的内容）：
<context>
{context}
</context>
- 历史对话（仅用于理解语境，不可当成事实来源）：
<history>
{history}
</history>
- 当前问题：
<question>
{input}
</question>

【回答要求】
1) 仅用简体中文；只根据“已知信息”回答，禁止自创信息。
2) 引用视频时必须给出 Markdown 链接：[标题](链接)，链接取自“URL:”或“链接:”.
3) 结尾添加“参考视频”小节，列出本次用到的所有视频（标题+链接）；若无法回答请直接说“我不确定，需要更多相关的 B 站数据”。
"""
).strip()


def format_generate_prompt(context: str, question: str, history: str = "") -> str:
    """构建将要发给LLM的完整prompt，便于打印调试。"""
    return GENERATE_TEMPLATE.format(context=context, input=question, history=history or "")


def create_generate_chain(llm):
    """
    Creates a generate chain for answering bilibili-related questions.

    Args:
        llm (LLM): The language model to use for generating responses.

    Returns:
        A callable function that takes a context and a question as input and returns a string response.
    """
    generate_prompt = PromptTemplate(
        template=GENERATE_TEMPLATE,
        input_variables=["context", "input", "history"],
    )

    generate_chain = generate_prompt | llm | StrOutputParser()

    return generate_chain


if __name__ == '__main__':
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        base_url=os.getenv("SILICON_BASE_URL", "https://api.siliconflow.cn/v1"),
        api_key=os.getenv("SILICON_API_KEY"),
        model=os.getenv("SILICON_CHAT_MODEL", "deepseek-ai/DeepSeek-V3.2"),
    )

    generate_chain = create_generate_chain(llm)
    final_answer = generate_chain.invoke({
        "context": "这是一个示例上下文",
        "history": "用户: 上次问了什么\n助手: 回答了什么",
        "input": "请帮我总结",
    })
    print(final_answer)
