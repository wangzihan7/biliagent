from typing_extensions import TypedDict


class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        documents: list of documents
    """

    input: str
    history: str
    generation: str
    documents: str
    retrieval_query: str
    final_question: str
    context_preview: str
    prompt: str
    prompt_length: int
