from mcp.server import MCPServer

from step_09_1_tools_basics import calculator
from step_06_1_semantic_search import semantic_search
from step_07_1_build_rag_prompt import build_rag_prompt
from step_08_1_ollama_basics import generate_text


mcp = MCPServer(
    "Local RAG Agent MCP Server"
)


@mcp.tool()
def calculator_tool(
    operation: str,
    a: float,
    b: float
) -> float:
    """
    Perform basic arithmetic.

    Supported operations:
    add, subtract, multiply, divide
    """

    return calculator(
        operation=operation,
        a=a,
        b=b
    )


@mcp.tool()
def search_documents_tool(
    question: str
) -> dict:
    """
    Search the local document knowledge base
    and return a grounded answer.
    """

    matches = semantic_search(
        question,
        top_k=3,
        min_similarity=0.65
    )

    if not matches:
        return {
            "found": False,
            "answer": (
                "I don't have enough information "
                "in the provided documents."
            ),
            "results": []
        }

    results = []

    for match in matches:
        results.append({
            "document_name": match["document_name"],
            "chunk_index": match["chunk_index"],
            "content": match["content"],
            "similarity": match["cosine_similarity"]
        })

    prompt = build_rag_prompt(
        question,
        matches
    )

    answer = generate_text(
        prompt,
        temperature=0.0
    )

    return {
        "found": True,
        "answer": answer,
        "results": results
    }


if __name__ == "__main__":
    mcp.run()