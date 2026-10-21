from step_6_1_semantic_search import semantic_search

def build_rag_prompt(question, matches):

    context_parts = []

    for match in matches:
        context_parts.append(
            f"Source: {match['document_name']}, "
            f"Chunk: {match['chunk_index']}\n"
            f"Content: {match['content']}"
        )

    context = "\n\n".join(context_parts)

    prompt = (
        "You are a helpful assistant.\n\n"
        "Answer the question using only the provided context.\n"
        "If the context does not contain the answer, say:\n"
        "\"I don't have enough information in the provided documents.\"\n\n"
        "Do not invent facts.\n\n"
        "Answer using ONLY facts explicitly stated in the context.\n\n"
        "Do not use prior knowledge.\n\n"
        "Do not add explanations, assumptions, examples, or facts that are not directly supported by the context.\n\n"
        "If a statement is not explicitly present in the context, do not include it.\n\n"

        f"Context:\n{context}\n\n"
        f"Question:\n{question}\n\n"
        "Answer:"
    )

    return prompt


if __name__ == "__main__":

    question = "How do Kafka consumer groups work?"

    # Retrieve relevant chunks from PostgreSQL.
    matches = semantic_search(
        question,
        top_k=3,
        min_similarity=0.65
    )

    # Avoid asking the LLM to answer without relevant context.
    if not matches:
        print("No sufficiently relevant document chunks found.")

    else:
        prompt = build_rag_prompt(
            question,
            matches
        )

        print("\nGenerated RAG prompt:")
        print("=" * 60)
        print(prompt)

