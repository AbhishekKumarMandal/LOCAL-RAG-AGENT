import torch


def vector_length(vector):
    """
    Calculate L2 vector length.

    Formula:

    sqrt(x1² + x2² + ... + xn²)
    """

    return torch.sqrt(
        torch.sum(vector * vector)
    ).item()


def normalize_embedding(embedding):
    """
    Perform L2 normalization.

    Example:

    [4, 3]
      ↓
    length = 5
      ↓
    [4/5, 3/5]
      ↓
    [0.8, 0.6]

    The normalized vector has length 1.
    """

    squared_sum = torch.sum(
        embedding * embedding,
        dim=1,
        keepdim=True
    )

    length = torch.sqrt(squared_sum)

    return embedding / length


def print_embedding_debug_info(
    text,
    encoded_input,
    token_embeddings,
    cls_embedding,
    normalized_embedding,
    tokenizer
):
    """
    Print intermediate embedding-generation values.

    Used only for learning/debugging so that the actual
    embedding-generation method remains clean.
    """

    input_ids = encoded_input["input_ids"][0]

    tokens = tokenizer.convert_ids_to_tokens(
        input_ids
    )

    print("\n" + "=" * 60)
    print("TEXT")
    print("=" * 60)
    print(text)

    # -----------------------------------------------------
    # Tokens + Token IDs
    # -----------------------------------------------------

    print("\nTOKENS + TOKEN IDs")

    for index, (token, token_id) in enumerate(
        zip(tokens, input_ids)
    ):
        print(
            f"{index}: "
            f"{token:<15} "
            f"ID={token_id.item()}"
        )

    # -----------------------------------------------------
    # Encoded input
    # -----------------------------------------------------

    print("\nENCODED INPUT")

    print(encoded_input)

    # -----------------------------------------------------
    # Transformer output
    #
    # Shape:
    #
    # [batch_size, number_of_tokens, 384]
    # -----------------------------------------------------

    print("\nTOKEN EMBEDDINGS")

    print(
        "Shape:",
        token_embeddings.shape
    )

    # Print only the first 10 dimensions for each token.
    for index, token in enumerate(tokens):

        token_embedding = token_embeddings[
            0,
            index,
            :
        ]

        print(f"\nToken: {token}")
        print("Embedding dimensions:", token_embedding.shape[0])
        print("First 10 of 384 values:")
        print(token_embedding[:10].tolist())

    # -----------------------------------------------------
    # CLS Pooling
    #
    # [:, 0, :]
    #
    # : -> all sentences
    # 0 -> [CLS] token
    # : -> all 384 dimensions
    # -----------------------------------------------------

    print("\nCLS POOLING")

    print(
        "Selected token:",
        tokens[0]
    )

    print(
        "CLS shape:",
        cls_embedding.shape
    )

    print(
        "First 10 values:",
        cls_embedding[0, :10].tolist()
    )

    print(
        "Length before normalization:",
        vector_length(
            cls_embedding[0]
        )
    )

    # -----------------------------------------------------
    # L2 Normalization
    # -----------------------------------------------------

    print("\nL2 NORMALIZATION")

    print(
        "First 10 values:",
        normalized_embedding[0, :10].tolist()
    )

    print(
        "Length after normalization:",
        vector_length(
            normalized_embedding[0]
        )
    )