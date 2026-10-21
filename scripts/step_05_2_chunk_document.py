from pathlib import Path

from step_05_1_read_document import read_document
from step_04_4_smart_chunking import chunk_text, count_tokens


# Resolve the project root relative to this script.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DOCUMENT_PATH = (
    PROJECT_ROOT
    / "data"
    / "documents"
    / "backend_notes.md"
)


def prepare_document_chunks(file_path):
    """
    Read a document, split it into chunks, and attach metadata.

    Each result contains:
        document_name: source filename
        chunk_index:  zero-based position in the document
        content:      actual chunk text

    No embeddings or database operations happen here.
    """

    document_content = read_document(file_path)

    chunks = chunk_text(
        document_content,
        max_tokens=100,
        overlap_words=10
    )

    prepared_chunks = []

    for chunk_index, content in enumerate(chunks):

        prepared_chunks.append({
            "document_name": file_path.name,
            "chunk_index": chunk_index,
            "content": content
        })

    return prepared_chunks


if __name__ == "__main__":

    prepared_chunks = prepare_document_chunks(
        DOCUMENT_PATH
    )

    print("Document:", DOCUMENT_PATH.name)
    print("Total chunks:", len(prepared_chunks))

    for item in prepared_chunks:

        print("\n" + "-" * 60)

        print("Document:", item["document_name"])
        print("Chunk index:", item["chunk_index"])

        print(
            "Token count:",
            count_tokens(item["content"])
        )

        print("\nContent:")
        print(item["content"])