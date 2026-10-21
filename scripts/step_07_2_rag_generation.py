from step_06_1_semantic_search import semantic_search
from step_07_1_build_rag_prompt import build_rag_prompt
from step_08_1_ollama_basics import generate_text


def answer_question(question):
    """
    Complete RAG flow:

    1. Retrieve relevant document chunks.
    2. Build a RAG prompt.
    3. Send the prompt to the local LLM.
    4. Return the generated answer.
    """

    matches = semantic_search(
        question,
        top_k=3,
        min_similarity=0.65
    )

    if not matches:
        return (
            "I don't have enough information "
            "in the provided documents."
        )

    prompt = build_rag_prompt(
        question,
        matches
    )

    answer = generate_text(
        prompt
    )

    return answer


if __name__ == "__main__":

    question = (
        "How do Kafka consumer groups work?"
    )

    answer = answer_question(
        question
    )

    print("\nQuestion:")
    print(question)

    print("\nAnswer:")
    print(answer)