# unlike previous chunking techinque where chunk size was mandatory,
# but here chunk size is not mandatory. but important is to ensure that
# each chunk should not cross max_tokens limit
# because if we send a chunk to model to generate embeddings 
# and if that chunks contains more tokenIds than a model can take at a time
# then model might reject that chunk or it can break that chunk to reducue the tokenIds that is being sent at a time


from transformers import AutoTokenizer


MODEL_NAME = "BAAI/bge-small-en-v1.5"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


def count_tokens(text):
    """
    Count the tokens that will be sent to our BGE model.

    This includes [CLS] and [SEP].
    """

    return len(
        tokenizer.encode(
            text,
            add_special_tokens=True
        )
    )


def chunk_text(text, max_tokens, overlap_words):
    """
    Split text into word-boundary-aware chunks.

    max_tokens:
        Maximum tokens per chunk, including [CLS] and [SEP].

    overlap_words:
        Number of complete words repeated between chunks.
    """

    if max_tokens <= 2:
        raise ValueError(
            "Token budget must leave room for content and special tokens"
        )

    if overlap_words < 0:
        raise ValueError("Overlap cannot be negative")

    words = text.split()

    if not words:
        return []

    chunks = []
    start_index = 0

    while start_index < len(words):

        end_index = start_index

        # Keep adding complete words while the candidate
        # stays within our token budget.
        while end_index < len(words):

            candidate_words = words[start_index:end_index + 1]

            candidate_text = " ".join(candidate_words)

            if count_tokens(candidate_text) > max_tokens:
                break

            end_index += 1

        # If even one word cannot fit, fail explicitly.
        # We are deliberately not splitting words in this version.
        if end_index == start_index:
            raise ValueError(
                f"Word cannot fit within {max_tokens} tokens: "
                f"{words[start_index]}"
            )

        chunk = " ".join(words[start_index:end_index])

        chunks.append(chunk)

        # No more words remain.
        if end_index == len(words):
            break

        # Repeat up to overlap_words complete words,
        # but never allow overlap to prevent progress.
        next_start = max(
            start_index + 1,
            end_index - overlap_words
        )

        # Ensure the repeated words plus the next NEW word
        # can fit together. Otherwise, reduce the overlap.

        # overlap_words is the desired overlap, not a strict guarantee.
        # Reduce it only when necessary to fit at least one new word
        # within the model's token budget.
        while next_start < end_index:

            next_candidate = " ".join(
                words[next_start:end_index + 1]
            )

            if count_tokens(next_candidate) <= max_tokens:
                break

            next_start += 1

        start_index = next_start

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
        max_tokens=18,
        overlap_words=2
    )

    for index, chunk in enumerate(chunks, start=1):

        print(f"\nChunk {index}:")
        print(chunk)

        print(
            "Token count (including special tokens):",
            count_tokens(chunk)
        )
    
    '''
    output
    ~~~~~~
    Chunk 1:
    Java is a programming language. Spring Boot is widely used for building backend
    Token count (including special tokens): 17

    Chunk 2:
    building backend applications. Kafka is commonly used for event-driven
    Token count (including special tokens): 17

    Chunk 3:
    for event-driven systems. PostgreSQL is a relational database.
    Token count (including special tokens): 18
    '''