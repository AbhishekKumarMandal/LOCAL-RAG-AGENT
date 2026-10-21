import torch

from transformers import AutoTokenizer, AutoModel

from step_2_1_cosine_similarity import cosine_similarity

from step_1_2_embedding_utils import (
    normalize_embedding,
    print_embedding_debug_info
)


MODEL_NAME = "BAAI/bge-small-en-v1.5"


# ---------------------------------------------------------
# Load tokenizer
#
# Responsibility:
#
# Text
#   ↓
# Tokens
#   ↓
# Token IDs
# ---------------------------------------------------------

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)


# ---------------------------------------------------------
# Load pretrained transformer model
#
# Responsibility:
#
# Token IDs
#     ↓
# Transformer
#     ↓
# Context-aware token vectors
# ---------------------------------------------------------

model = AutoModel.from_pretrained(
    MODEL_NAME
)


def generate_embedding(text, debug=False):
    """
    Convert text into a normalized 384-dimensional
    embedding using BGE-small-en-v1.5.
    """

    # -----------------------------------------------------
    # STEP 1 — Tokenization
    #
    # Example:
    #
    # "Java is a programming language"
    #
    #       ↓
    #
    # [CLS], java, is, a, programming, language, [SEP]
    #
    #       ↓
    #
    # Token IDs
    #
    #
    # tokenizer(...) returns a dictionary containing:
    #
    # {
    #     "input_ids": ...,
    #     "token_type_ids": ...,
    #     "attention_mask": ...
    # }
    #
    #
    # input_ids
    # ----------
    #
    # These are the numeric IDs assigned to each token.
    #
    # Example:
    #
    # [CLS]        -> 101
    # java         -> 9262
    # is           -> 2003
    # a            -> 1037
    # programming  -> 4730
    # language     -> 2653
    # [SEP]        -> 102
    #
    # So input_ids may look like:
    #
    # [101, 9262, 2003, 1037, 4730, 2653, 102]
    #
    #
    # attention_mask
    # --------------
    #
    # Tells the Transformer which positions contain
    # actual tokens and which positions are only padding.
    #
    # 1 = real token, pay attention to it
    # 0 = padding token, ignore it
    #
    # For our current sentence:
    #
    # [1, 1, 1, 1, 1, 1, 1]
    #
    # because every position contains a real token.
    #
    #
    # Padding becomes important when multiple sentences
    # of different lengths are processed together.
    #
    # Example:
    #
    # Sentence 1:
    # "Java is useful"
    #
    # Sentence 2:
    # "Python"
    #
    # The shorter sentence may be padded so both sequences
    # have the same length:
    #
    # Sentence 1:
    # [CLS] Java is useful [SEP]
    #
    # attention_mask:
    # [1,1,1, 1,1]
    #
    #
    # Sentence 2:
    # [CLS] Python [SEP] [PAD] [PAD]
    #
    # attention_mask:
    # [1,    1,     1,    0,    0]
    #
    # The Transformer therefore knows not to treat [PAD]
    # positions as meaningful text.
    #
    #
    # token_type_ids
    # --------------
    #
    # BERT-style models can process two text segments
    # together.
    #
    # token_type_ids tell the model which token belongs
    # to which segment.
    #
    #
    # Example:
    #
    # Sentence A:
    # "Java is a language"
    #
    # Sentence B:
    # "Spring Boot uses Java"
    #
    #
    # The combined input may conceptually look like:
    #
    # [CLS]
    # Java
    # is
    # a
    # language
    # [SEP]
    # Spring
    # Boot
    # uses
    # Java
    # [SEP]
    #
    #
    # Tokens belonging to Sentence A may receive:
    #
    # token_type_id = 0
    #
    # Tokens belonging to Sentence B may receive:
    #
    # token_type_id = 1
    #
    # Conceptually:
    #
    # [CLS] Java is a language [SEP] Spring Boot uses Java [SEP]
    #
    #   0    0   0  0    0      0     1     1    1    1    1
    #
    #
    # In our current project we are embedding only one
    # sentence at a time, so every token normally belongs
    # to the same segment:
    #
    # token_type_ids:
    #
    # [0, 0, 0, 0, 0, 0, 0]
    #
    #
    # return_tensors="pt"
    # -------------------
    #
    # Tells the tokenizer to return PyTorch tensors
    # instead of normal Python lists.
    # -----------------------------------------------------

    encoded_input = tokenizer(
        text,
        return_tensors="pt"
    )


    # -----------------------------------------------------
    # STEP 2 — Transformer
    #
    # We are performing inference, not training.
    #
    #
    # torch.no_grad()
    #
    # tells PyTorch that it does not need to track
    # gradients because we are not training the model.
    #
    #
    # **encoded_input
    #
    # unpacks the dictionary.
    #
    # For example:
    #
    # model(**encoded_input)
    #
    # behaves roughly like:
    #
    # model(
    #     input_ids=...,
    #     attention_mask=...,
    #     token_type_ids=...
    # )
    #
    #
    # model_output contains the output produced
    # by the Transformer.
    # -----------------------------------------------------

    with torch.no_grad():
        model_output = model(
            **encoded_input
        )


    # -----------------------------------------------------
    # STEP 3 — Get vectors for every token
    #
    # model_output.last_hidden_state contains the
    # contextual vector generated for every token.
    #
    #
    # Suppose there are 7 tokens.
    #
    # Shape:
    #
    # [1, 7, 384]
    #
    #
    # Means:
    #
    # 1
    # ↓
    # one sentence / batch size
    #
    #
    # 7
    # ↓
    # seven tokens
    #
    #
    # 384
    # ↓
    # 384-dimensional vector for each token
    #
    #
    # Conceptually:
    #
    # [CLS]        → [384 values]
    # java         → [384 values]
    # is           → [384 values]
    # a            → [384 values]
    # programming  → [384 values]
    # language     → [384 values]
    # [SEP]        → [384 values]
    #
    #
    # Printing the entire model_output or
    # token_embeddings would produce a very large output,
    # so detailed printing is handled separately by the
    # debug helper.
    # -----------------------------------------------------

    token_embeddings = (
        model_output.last_hidden_state
    )


    # -----------------------------------------------------
    # STEP 4 — CLS Pooling
    #
    # BGE-small-en-v1.5 uses the transformed [CLS]
    # token representation as the sentence embedding.
    #
    #
    # token_embeddings has shape:
    #
    # [batch_size, number_of_tokens, 384]
    #
    #
    # We use:
    #
    # [:, 0, :]
    #
    #
    # First :
    #     all sentences in the batch
    #
    # 0
    #     token at index 0
    #
    #     token 0 is [CLS]
    #
    # Last :
    #     all 384 dimensions of that token
    #
    #
    # So:
    #
    # token_embeddings[:, 0, :]
    #
    # means:
    #
    # "For every sentence, select the [CLS] token
    #  and return all 384 values of its vector."
    #
    #
    # Shape before:
    #
    # [1, 7, 384]
    #
    # Shape after:
    #
    # [1, 384]
    #
    #
    # IMPORTANT:
    #
    # CLS pooling does NOT average all token vectors.
    #
    # It simply selects the transformed [CLS] vector.
    # -----------------------------------------------------

    cls_embedding = token_embeddings[
        :,
        0,
        :
    ]


    # -----------------------------------------------------
    # STEP 5 — L2 Normalization
    #
    # Resize the CLS embedding so that its total
    # vector length becomes 1 while preserving
    # its direction.
    #
    #
    # Detailed normalization mathematics lives in:
    #
    # embedding_utils.py
    #
    #
    # Conceptually:
    #
    # CLS embedding
    #
    # [x1, x2, ..., x384]
    #
    #       ↓
    #
    # calculate vector length
    #
    #       ↓
    #
    # divide every value by that length
    #
    #       ↓
    #
    # normalized embedding
    #
    # length = 1
    # -----------------------------------------------------

    normalized_embedding = normalize_embedding(
        cls_embedding
    )


    # -----------------------------------------------------
    # DEBUG / LEARNING OUTPUT
    #
    # The actual embedding logic above remains simple.
    #
    # When debug=True, the helper prints:
    #
    # - tokens
    # - token IDs
    # - encoded_input
    # - token embeddings
    # - CLS pooling output
    # - CLS embedding
    # - vector length before normalization
    # - normalized embedding
    # - vector length after normalization
    #
    # Keeping this in a helper avoids mixing large amounts
    # of print code with the actual embedding algorithm.
    # -----------------------------------------------------

    if debug:
        print_embedding_debug_info(
            text,
            encoded_input,
            token_embeddings,
            cls_embedding,
            normalized_embedding,
            tokenizer
        )


    # -----------------------------------------------------
    # FINAL RESULT
    #
    # normalized_embedding currently has shape:
    #
    # [1, 384]
    #
    #
    # [0] removes the batch dimension:
    #
    # [384]
    #
    #
    # .tolist() converts the PyTorch Tensor into
    # a normal Python list.
    # -----------------------------------------------------

    return normalized_embedding[
        0
    ].tolist()


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    sentence_a = (
        "Java is a programming language"
    )

    sentence_b = (
        "Java is used for software development"
    )

    sentence_c = (
        "Bananas grow in tropical climates"
    )


    # ---------------------------------------------------------
    # Generate embeddings.
    #
    # debug=True is used only for sentence A so that we can
    # inspect the complete embedding-generation process.
    #
    # Sentence B and C are generated silently.
    # ---------------------------------------------------------

    embedding_a = generate_embedding(
        sentence_a,
        debug=True
    )

    embedding_b = generate_embedding(
        sentence_b
    )

    embedding_c = generate_embedding(
        sentence_c
    )


    print(
        "\nEmbedding dimensions:",
        len(embedding_a)
    )


    print(
        "\nFirst 10 values of embedding A:"
    )

    print(
        embedding_a[:10]
    )


    # ---------------------------------------------------------
    # Compare semantically related sentences.
    #
    # A:
    # "Java is a programming language"
    #
    # B:
    # "Java is used for software development"
    #
    # Expected:
    #
    # Higher cosine similarity.
    # ---------------------------------------------------------

    similarity_ab = cosine_similarity(
        embedding_a,
        embedding_b
    )


    # ---------------------------------------------------------
    # Compare semantically different sentences.
    #
    # A:
    # "Java is a programming language"
    #
    # C:
    # "Bananas grow in tropical climates"
    #
    # Expected:
    #
    # Lower cosine similarity than A vs B.
    # ---------------------------------------------------------

    similarity_ac = cosine_similarity(
        embedding_a,
        embedding_c
    )


    print(
        "\nJava programming vs "
        "Java software development:",
        similarity_ab
    )

    print(
        "Java programming vs bananas:",
        similarity_ac
    )