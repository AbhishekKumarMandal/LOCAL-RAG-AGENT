from transformers import AutoTokenizer
from step_04_1_chunking_basics import chunk_text

# Use the same tokenizer as our embedding generator.
MODEL_NAME = "BAAI/bge-small-en-v1.5"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

text = """
Java is a programming language.
Spring Boot is widely used for building backend applications.
Kafka is commonly used for event-driven systems.
PostgreSQL is a relational database.
"""

chunks = chunk_text(text, chunk_size=8, overlap=2)

for index, chunk in enumerate(chunks, start=1):

    # The tokenizer converts text into token IDs.
    # add_special_tokens=True includes tokens such as [CLS] and [SEP].
    encoded_input = tokenizer(
        chunk,
        add_special_token = True
    )

    token_ids = encoded_input["input_ids"]

    # Convert token IDs back into readable token strings
    # so we can inspect how the model splits the text.
    tokens = tokenizer.convert_ids_to_tokens(token_ids)

    print(f"\nChunk {index}:")
    print(chunk)

    print("Word count:", len(chunk.split()))
    print("Token count:", len(token_ids))
    print("Tokens:", tokens)
