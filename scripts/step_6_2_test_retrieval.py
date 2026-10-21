from step_6_1_semantic_search import semantic_search


def test_question(question, min_similarity=None):

    print("\n" + "=" * 60)
    print("Question:", question)
    print("Minimum similarity:", min_similarity)

    matches = semantic_search(
        question,
        top_k=3,
        min_similarity=min_similarity
    )

    if not matches:
        print("\nNo sufficiently similar chunks found.")
        return

    for rank, match in enumerate(matches, start=1):

        print(f"\nMatch {rank}")
        print("Document:", match["document_name"])
        print("Chunk index:", match["chunk_index"])

        print(
            "Similarity:",
            round(match["cosine_similarity"], 4)
        )

        print("Content:", match["content"])


if __name__ == "__main__":

    # Case 1: The document contains relevant information.
    test_question(
        "How do Kafka consumer groups work?",
        min_similarity=0.65
    )

    # Case 2: The document does not contain the answer.
    test_question(
        "What is the capital of France?",
        min_similarity=0.65
    )