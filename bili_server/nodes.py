

import asyncio

from bili_server.generate_chain import create_generate_chain, format_generate_prompt


class GraphNodes:
    def __init__(
        self,
        llm,
        retriever,
        retrieval_grader,
        question_rewriter,
        dataset_ids=None,
        top_k: int = 10,
        score_threshold: float = None,
    ):
        self.llm = llm
        self.retriever = retriever
        self.retrieval_grader = retrieval_grader
        self.question_rewriter = question_rewriter
        self.dataset_ids = dataset_ids
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.generate_chain = create_generate_chain(llm)

    # offline-only override: require dataset_ids, skip live retrieval
    async def retrieve(self, state):  # type: ignore[override]
        print("---node: retrieve (offline)---")
        original_question = state["input"]
        history_text = state.get("history") or ""
        retrieval_query = original_question

        print(f"[retrieve] original_question: {original_question}")

        # 预先用重写器扩充检索查询，避免“没有了吗”这类短问导致召回差
        if self.question_rewriter:
            try:
                rewritten = self.question_rewriter.invoke({"input": original_question, "history": history_text})
                if rewritten:
                    rewritten_clean = rewritten.strip()
                    for prefix in [
                        "改写后的中文问题：",
                        "改写后的问题：",
                        "改写后问题：",
                        "问题重写：",
                        "重写问题：",
                    ]:
                        if rewritten_clean.startswith(prefix):
                            rewritten_clean = rewritten_clean[len(prefix):].strip()
                            break
                    rewritten = rewritten_clean or rewritten
                    retrieval_query = rewritten
            except Exception as e:
                print(f"[retrieve] question rewrite failed, fallback to base: {e}")
        print(f"[retrieve] question_for_retrieval: {retrieval_query}")

        if self.dataset_ids:
            documents = await self.retriever.get_retriever_from_dataset(
                self.dataset_ids,
                k=self.top_k,
                score_threshold=self.score_threshold,
                query_text=retrieval_query,
            )
        else:
            print("---no dataset_ids provided, skip live retrieval---")
            documents = []
        print(f"docs retrieved: {len(documents)}")
        return {
            "documents": documents,
            "input": original_question,
            "retrieval_query": retrieval_query,
            "history": history_text,
        }

    async def generate(self, state):
        """
        Use RAG generation.
        Token-level streaming is handled by astream_events at the graph level.
        """
        print("---node: generate---")

        question = state["input"]
        documents = state["documents"]
        retrieval_query = state.get("retrieval_query")
        history_text = state.get("history")

        final_question = question

        context_text = self._format_documents(documents)
        formatted_prompt = format_generate_prompt(context_text, final_question, history_text or "")
        prompt_length = len(formatted_prompt)
        preview_limit = 4000
        prompt_preview = (
            formatted_prompt
            if prompt_length <= preview_limit
            else f"{formatted_prompt[:preview_limit]}\n...[prompt truncated, total {prompt_length} chars]"
        )
        print(f"prompt length: {prompt_length}")
        print(f"docs used for generation: {len(documents)}")

        full_generation = await self.generate_chain.ainvoke(
            {"context": context_text, "input": final_question, "history": history_text or ""}
        )

        return {
            "documents": documents,
            "input": final_question,
            "generation": full_generation,
            "retrieval_query": retrieval_query,
            "history": history_text,
            "final_question": final_question,
            "prompt": prompt_preview,
            "prompt_length": prompt_length,
        }

    async def grade_documents(self, state):
        """
        Filter docs by relevance.
        """
        print("---node: grade_documents---")
        question = state["input"]
        documents = state["documents"]
        retrieval_query = state.get("retrieval_query")
        history_text = state.get("history")

        # 打分优先使用重写/检索用的查询，避免短句带来判定偏差
        question_for_grader = retrieval_query or question
        print(f"[grade] question_for_grader: {question_for_grader}")

        filtered_docs = []

        async def _judge(doc):
            try:
                return await asyncio.to_thread(
                    self.retrieval_grader.invoke,
                    {"input": question_for_grader, "document": doc.page_content},
                )
            except Exception as e:
                # 打分模型不可用时不应中断整条链，放行文档交由生成节点处理
                print(f"[grade] grader failed, pass through: {e}")
                return {"score": "yes"}

        results = await asyncio.gather(*[_judge(d) for d in documents])
        for d, score in zip(documents, results):
            grade = score.get("score")
            if grade == "yes":
                print("---grade: relevant---")
                filtered_docs.append(d)
            else:
                print("---grade: not relevant---")
                continue

        if not filtered_docs and self.dataset_ids:
            print("---fallback: no docs passed grader, using original docs (dataset_ids)---")
            filtered_docs = documents

        return {
            "documents": filtered_docs,
            "input": question,
            "retrieval_query": retrieval_query,
            "history": history_text,
        }

    def transform_query(self, state):
        """
        Rewrite question when needed.
        """
        print("---node: transform_query---")

        question = state["input"]
        documents = state["documents"]
        retrieval_query = state.get("retrieval_query")
        history_text = state.get("history")

        better_question = self.question_rewriter.invoke({"input": question, "history": history_text})
        if better_question:
            better_question = better_question.strip()
            for prefix in [
                "改写后的中文问题：",
                "改写后的问题：",
                "改写后问题：",
                "问题重写：",
                "重写问题：",
            ]:
                if better_question.startswith(prefix):
                    better_question = better_question[len(prefix):].strip()
                    break
        print(f"rewritten question: {better_question}")
        return {
            "documents": documents,
            "input": better_question,
            "retrieval_query": retrieval_query,
            "history": history_text,
        }

    def _format_documents(self, documents):
        """Format retrieved documents with source info for generation (title/URL/dataset/keyword)."""
        formatted = []
        for idx, d in enumerate(documents, start=1):
            meta = getattr(d, "metadata", {}) or {}
            title = meta.get("title") or ""
            url = meta.get("url") or meta.get("link") or ""
            dataset_id = meta.get("dataset_id") or ""
            keyword = meta.get("keyword") or ""
            formatted.append(
                f"[Doc {idx}] Title: {title}\nURL: {url}\nDataset: {dataset_id}  Keyword: {keyword}\nContent:\n{d.page_content}"
            )
        return "\n\n".join(formatted)
