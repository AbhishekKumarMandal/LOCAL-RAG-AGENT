# fixed size chunking with overlap
# one problem with fixed chunking is: it can split sentences awkwardly.
# read readme.md for more details

def chunk_text(
        text, 
        chunk_size, 
        overlap # how many last words of previous sentence should overlap 
        # with the first words of curreent sentence.
        # eg overlap = 2 then last 2 words of sentence 1 should overlap with first 2 words of sentence 2
        # in short last 2 words of sentence 1 should be first 2 words of sentence 2
):

    """
    Split text into fixed-size word chunks
    with overlap between consecutive chunks.

    Example:

    words:
    A B C D E F G H I J

    chunk_size = 4
    overlap = 2

    output:
    [
        "A B C D",
        "C D E F",
        "E F G H",
        "G H I J"
    ]
    """
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")

    if not 0 <= overlap < chunk_size:
        raise ValueError("Overlap must be between 0 and chunk_size - 1")

    words = text.split()
    chunks = []

    step = chunk_size - overlap
    previous_end_index = 0

    for start_index in range(0, len(words), step):
        end_index = min(start_index + chunk_size, len(words))

        # The remaining words are already covered by the previous chunk.
        if previous_end_index == end_index:
            break

        chunk_words = words[start_index:end_index]
        chunks.append(" ".join(chunk_words))

        previous_end_index = end_index

    return chunks


if __name__ == "__main__":
    
    text = """
    Java is a programming language.
    Spring Boot is widely used for building backend applications.
    Kafka is commonly used for event-driven systems.
    PostgreSQL is a relational database.
    """

    chunks = chunk_text(
        text,
        chunk_size=8,
        overlap=2
    )

    for index, chunk in enumerate(
        chunks,
        start=1
    ):
        print(
            f"\nChunk {index}:"
        )

        print(
            chunk
        )