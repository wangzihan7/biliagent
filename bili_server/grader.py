
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.exceptions import OutputParserException
import os
import json
import re

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class RobustJsonOutputParser(JsonOutputParser):
    """增强的JSON解析器,能处理智谱AI等模型的非标准输出"""

    def parse_result(self, result, *, partial: bool = False):
        # JsonOutputParser 走 parse_result,不经过 parse,兜底必须在这里生效
        try:
            return super().parse_result(result, partial=partial)
        except (OutputParserException, json.JSONDecodeError):
            return self._fallback(result[0].text if result else "")

    def parse(self, text: str) -> dict:
        try:
            # 首先尝试标准JSON解析
            return super().parse(text)
        except (OutputParserException, json.JSONDecodeError):
            return self._fallback(text)

    def _fallback(self, text: str) -> dict:
        # 如果失败,尝试提取yes/no并构造JSON
        text_clean = text.strip().lower()

        # 直接检查文本内容
        if text_clean == 'yes' or text_clean == '"yes"' or text_clean == "'yes'":
            return {"score": "yes"}
        elif text_clean == 'no' or text_clean == '"no"' or text_clean == "'no'":
            return {"score": "no"}
        elif 'yes' in text_clean and 'no' not in text_clean:
            return {"score": "yes"}
        elif 'no' in text_clean and 'yes' not in text_clean:
            return {"score": "no"}
        else:
            # 尝试提取JSON对象
            json_match = re.search(r'\{[^}]+\}', text)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            # 默认返回no
            print(f"警告: 无法解析输出 '{text}', 默认返回 no")
            return {"score": "no"}

class GraderUtils:
    def __init__(self, model):
        self.model = model

    def create_retrieval_grader(self):
        """
        Creates a retrieval grader that assesses the relevance of a retrieved document to a user question.

        Returns:
            A callable function that takes a document and a question as input and returns a JSON object with a binary score indicating whether the document is relevant to the question.
        """

        # 使用的特殊标记是为了指定不同部分的开始和结束，以及明确不同类型的文本块。
        # 这些标记可以帮助大模型更好地理解和区分输入数据的不同部分，从而更精确地执行特定的任务。
        # 您是一名评分员，负责评估检索到的文档与用户问题的相关性。如果文档包含与用户问题相关的关键词，请将其评为相关。这不需要非常严格的测试。目标是过滤掉错误的检索结果。
        grade_prompt = PromptTemplate(
            template="""
            <|begin_of_text|><|start_header_id|>system<|end_header_id|>
            你是相关性评估员，请判断检索到的文档是否与用户问题相关。
            只要文档主题或关键词与问题有明显关联，就判定为 yes，不需要苛刻。
            总结/概述类问题通常都算相关。输出 JSON，仅包含键 score，值为 yes 或 no。
            <|eot_id|>
            <|start_header_id|>user<|end_header_id|>

            文档: {document}
            问题: {input}
            <|eot_id|>
            <|start_header_id|>assistant<|end_header_id|>
            """,
            input_variables=["document", "input"],
        )

        # 创建一个 评分员 的链
        retriever_grader = grade_prompt | self.model | RobustJsonOutputParser()

        return retriever_grader

    # 您是一个问题重写器，将输入的问题转换成更好的版本，优化以适应向量存储检索。请查看输入并尝试理解其潜在的语义意图/含义。
    # 覆盖：检索导向的重写器，处理序号/代词指代
    def create_question_rewriter(self):
        """
        Rewrites a question to make it clearer for vector retrieval (Chinese only, keep intent).
        Uses history to resolve pronouns/ordinals when possible.
        """
        re_write_prompt = PromptTemplate(
            template="""
            你是“检索导向”的问题重写器，目标是提升向量检索召回率。
            规则：
            - 用中文输出；保持原意，补全省略信息，避免代词/序号指代不明（如“第三个视频”应尝试替换为历史或上下文中对应的视频标题/关键词；若无法确定则保留原表述）。
            - 保留或强化关键词（人名/地名/主题/时间等），便于匹配相似文本。
            - 不添加原意以外的新信息；不改成英文。

            历史对话（可为空，仅供 disambiguation）:
            {history}

            原始问题: {input}

            请给出改写后的中文问题（仅输出改写结果）。""",
            input_variables=["input", "history"],
        )

        question_rewriter = re_write_prompt | self.model | StrOutputParser()

        return question_rewriter

