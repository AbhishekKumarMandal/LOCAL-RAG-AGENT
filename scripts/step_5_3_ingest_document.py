from pathlib import Path

from step_5_2_chunk_document import prepare_document_chunks
from step_1_3_real_embeddings import generate_embedding
from step_3_1_database_utils import get_connection
from step_3_2_store_embedding import embedding_to_pgvector


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DOCUMENT_PATH = (
    PROJECT_ROOT
    / "data"
    / "documents"
    / "backend_notes.md"
)

def ingest_document(file_path):
    """
    Read a document, generate an embedding for each chunk,
    and store the chunks and their metadata in PostgreSQL.
    """

    prepared_chunks = prepare_document_chunks(file_path)

    print("Document:", file_path.name)
    print("Chunks to ingest:", len(prepared_chunks))

    # One connection and transaction for this document.
    # If an INSERT fails, PostgreSQL rolls back the transaction.
    with get_connection() as connection:

        with connection.cursor() as cursor:

            for item in prepared_chunks:

                # Convert this chunk's text into a 384-dimensional embedding.
                embedding = generate_embedding(
                    item["content"]
                )

                # Convert our Python list into pgvector's textual format.
                vector_value = embedding_to_pgvector(
                    embedding
                )

                cursor.execute(
                    """
                    INSERT INTO document_chunks (
                        document_name,
                        chunk_index,
                        content,
                        embedding
                    )
                    VALUES (%s, %s, %s, %s::vector)
                    """,
                    (
                        item["document_name"],
                        item["chunk_index"],
                        item["content"],
                        vector_value
                    )
                )

                print(
                    f"Stored chunk {item['chunk_index']} "
                    f"({len(embedding)} dimensions)"
                )

    print("\nDocument ingestion completed.")


if __name__ == "__main__":
    ingest_document(DOCUMENT_PATH)


