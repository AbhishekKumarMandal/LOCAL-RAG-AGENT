from pathlib import Path


# __file__ is the location of this Python script.
#
# Example:
# local-rag-agent/scripts/step_5_1_read_document.py
#
# .resolve() gets its absolute path.
# .parent gives us the scripts/ directory.
# .parent.parent gives us the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


DOCUMENT_PATH = (
    PROJECT_ROOT
    / "data"
    / "documents"
    / "backend_notes.md"
)


def read_document(file_path):
    """
    Read a UTF-8 text/Markdown document and return its contents.

    pathlib.Path.read_text() opens the file, reads its content,
    and closes the file automatically.
    """

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Document not found: {file_path}"
        )

    content = file_path.read_text(
        encoding="utf-8"
    )

    return content


if __name__ == "__main__":

    document = read_document(
        DOCUMENT_PATH
    )

    print("Document path:")
    print(DOCUMENT_PATH)

    print("\nDocument content:")
    print(document)

    print("\nTotal characters:", len(document))

    print(
        "Total words:",
        len(document.split())
    )