from step_1_3_real_embeddings import generate_embedding
from step_3_1_database_utils import get_connection
from step_3_2_store_embedding import embedding_to_pgvector


def semantic_search(question, top_k=3, min_similarity=None):
    """
    Search previously ingested document chunks.

    1. Generate an embedding for the user's question.
    2. Convert the embedding to pgvector's text format.
    3. Retrieve the top_k chunks with the smallest cosine distance.
    4. Return the matching chunks and their source metadata.
    """

    # Step 1: Convert the question into a 384-dimensional vector.
    question_embedding = generate_embedding(question)

    question_vector = embedding_to_pgvector(
        question_embedding
    )

    # Step 2: Search the document_chunks table.
    with get_connection() as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    document_name,
                    chunk_index,
                    content,
                    1 - (embedding <=> %s::vector) AS cosine_similarity
                FROM document_chunks
                WHERE (
                    %s::double precision IS NULL
                    OR 1 - (embedding <=> %s::vector) >= %s::double precision
                )
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (
                    question_vector,
                    min_similarity,
                    question_vector,
                    min_similarity,
                    question_vector,
                    top_k
                )
            )

            # Fetch all rows returned by the query.
            results = cursor.fetchall()

    # Step 3: Convert database tuples into descriptive dictionaries.
    matches = []

    for row in results:

        matches.append({
            "document_name": row[0],
            "chunk_index": row[1],
            "content": row[2],
            "cosine_similarity": row[3]
        })

    return matches


if __name__ == "__main__":

    question = "what is the capital of france?"

    matches = semantic_search(
        question,
        top_k=3,
        min_similarity = 0.65
    )

    print("\nQuestion:")
    print(question)

    if not matches:
        print("No sufficiently similar document chunks found.")
    else:
        print("\nRetrieved chunks:")
        for rank, match in enumerate(matches, start=1):
            print("\n" + "-" * 60)
            print(f"\nRank: {rank}")
            print("Document:", match["document_name"])
            print("Chunk:", match["chunk_index"])
            print("Similarity:", match["cosine_similarity"])
            print("Content:", match["content"])
    
