from transformers import AutoTokenizer


MODEL_NAME = "BAAI/bge-small-en-v1.5"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


def chunk_text_by_tokens(text, chunk_size, overlap):
    """
    Split text into overlapping token-based chunks.

    chunk_size:
        Maximum number of content tokens in a chunk.
        Does not include [CLS] and [SEP].
        during chunking, we only want to split the actual document content. 
        If we included [CLS] and [SEP] in our token list, they could end up inside individual chunks unnecessarily.

    overlap:
        Number of content tokens repeated between chunks.
    """

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")

    if not 0 <= overlap < chunk_size:
        raise ValueError(
            "Overlap must be between 0 and chunk_size - 1"
        )

    # Convert the entire input into token IDs.
    #
    # We exclude special tokens because we are splitting
    # the document, not preparing a model input yet.
    token_ids = tokenizer.encode(
        text,
        add_special_tokens=False
    )

    all_tokens = tokenizer.convert_ids_to_tokens(
        token_ids
    )
    print('all tokens\n', all_tokens)

    chunks = []

    step = chunk_size - overlap

    previous_end_index = 0

    for start_index in range(0, len(token_ids), step):

        # Keep the actual end within the token list.
        end_index = min(
            start_index + chunk_size,
            len(token_ids)
        )

        # Avoid creating a final chunk that contains
        # only tokens already covered by the previous one.
        if previous_end_index == end_index:
            break

        chunk_token_ids = token_ids[
            start_index:end_index
        ]

        tokens = tokenizer.convert_ids_to_tokens(chunk_token_ids)

        # Convert token IDs back into readable text.
        chunk_text = tokenizer.decode(
            chunk_token_ids,
            skip_special_tokens=True
        )

        chunks.append({
            "text": chunk_text,
            "token_ids": chunk_token_ids
        })

        previous_end_index = end_index

    return chunks


if __name__ == "__main__":

    text = """
    Java is a programming language.
    Spring Boot is widely used for building backend applications.
    Kafka is commonly used for event-driven systems.
    PostgreSQL is a relational database.
    """

    chunks = chunk_text_by_tokens(
        text,
        chunk_size=12,
        overlap=3
    )

    for index, chunk in enumerate(chunks, start=1):

        print(f"\nChunk {index}:")
        print(chunk["text"])

        print(
            "Original content token count:",
            len(chunk["token_ids"])
        )

        print(
            "Original tokens:",
            tokenizer.convert_ids_to_tokens(
                chunk["token_ids"]
            )
        )

    '''
    output (with overlap value as 3)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    all tokens
    ['java', 'is', 'a', 'programming', 'language', '.', 
    'spring', 'boot', 'is', 'widely', 'used', 'for', 'building', 'back', '##end', 'applications', '.', 
    'ka', '##fk', '##a', 'is', 'commonly', 'used', 'for', 'event', '-', 'driven', 'systems', '.', 
    'post', '##gre', '##s', '##q', '##l', 'is', 'a', 'relational', 'database', '.']

    Chunk 1:
    java is a programming language. spring boot is widely used for
    Original content token count: 12
    Original tokens: ['java', 'is', 'a', 'programming', 'language', '.', 'spring', 'boot', 'is', 'widely', 'used', 'for']

    Chunk 2:
    widely used for building backend applications. kafka is
    Original content token count: 12
    Original tokens: ['widely', 'used', 'for', 'building', 'back', '##end', 'applications', '.', 'ka', '##fk', '##a', 'is']

    Chunk 3:
    ##fka is commonly used for event - driven systems. post
    Original content token count: 12
    Original tokens: ['##fk', '##a', 'is', 'commonly', 'used', 'for', 'event', '-', 'driven', 'systems', '.', 'post']

    Chunk 4:
    systems. postgresql is a relational database.
    Original content token count: 12
    Original tokens: ['systems', '.', 'post', '##gre', '##s', '##q', '##l', 'is', 'a', 'relational', 'database', '.']
    '''
    