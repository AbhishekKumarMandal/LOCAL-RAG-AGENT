# Step 4 — Document Chunking

## 1. What is chunking?

Chunking means splitting a large document into smaller pieces called **chunks**.

Suppose we have a document:

```text
Java is a programming language.
Spring Boot is widely used for building backend applications.
Kafka is commonly used for event-driven systems.
PostgreSQL is a relational database.
```

Instead of generating one embedding for the entire document, we split it into smaller chunks:

```text
Document
   ↓
Chunk 1
Chunk 2
Chunk 3
   ↓
One embedding per chunk
```

### Why is chunking required?

There are two main reasons:

1. **Model input limits:** Embedding models cannot process an unlimited number of tokens.
2. **Better retrieval:** A small, focused chunk can match a specific user question more effectively than one embedding representing many unrelated topics.

For example, if a user asks:

```text
How does Kafka work?
```

we want to retrieve the Kafka-related content rather than an entire document covering Java, Kafka, and PostgreSQL.

---

## 2. Fixed-size word chunking

Our first implementation splits text into chunks containing a maximum number of words.

Example:

```text
A B C D E F G H I J
```

With:

```python
chunk_size = 4
```

the result is:

```text
Chunk 1: A B C D
Chunk 2: E F G H
Chunk 3: I J
```

### Implementation

```python
def chunk_text(text, chunk_size):

    words = text.split()
    chunks = []

    for start_index in range(
        0,
        len(words),
        chunk_size
    ):

        end_index = start_index + chunk_size

        chunk_words = words[start_index:end_index]

        chunks.append(" ".join(chunk_words))

    return chunks
```

### Limitation

Fixed-size chunking may split a sentence at an awkward position.

For example:

```text
Chunk 1:
Spring Boot is widely used for building

Chunk 2:
backend applications. Kafka is commonly used
```

The information about Spring Boot is divided between two chunks.

---

## 3. Overlapping chunking

Overlap means repeating some words between consecutive chunks to preserve context.

Suppose:

```python
chunk_size = 4
overlap = 2
```

For:

```text
A B C D E F G H I J
```

we get:

```text
Chunk 1: A B C D
Chunk 2: C D E F
Chunk 3: E F G H
Chunk 4: G H I J
```

The important formula is:

```python
step = chunk_size - overlap
```

For example:

```text
chunk_size = 8
overlap = 2

step = 6
```

So chunk starting indexes become:

```text
0, 6, 12, 18, ...
```

### Implementation

```python
def chunk_text(text, chunk_size, overlap):

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")

    if not 0 <= overlap < chunk_size:
        raise ValueError(
            "Overlap must be between 0 and chunk_size - 1"
        )

    words = text.split()
    chunks = []

    step = chunk_size - overlap
    previous_end_index = 0

    for start_index in range(0, len(words), step):

        # min() ensures that the actual end never exceeds
        # the number of words in the document.
        end_index = min(
            start_index + chunk_size,
            len(words)
        )

        # If the previous chunk already covered the end
        # of the document, another chunk would be redundant.
        if previous_end_index == end_index:
            break

        chunk_words = words[start_index:end_index]

        chunks.append(" ".join(chunk_words))

        previous_end_index = end_index

    return chunks
```

### Why track `previous_end_index`?

Consider a 26-word document:

```text
chunk_size = 8
overlap = 2
step = 6
```

| Start index | Actual end index | Action |
|---:|---:|---|
| 0 | 8 | Add chunk |
| 6 | 14 | Add chunk |
| 12 | 20 | Add chunk |
| 18 | 26 | Add chunk |
| 24 | 26 | Stop |

At the final iteration, the end index has not changed. The remaining words were already included in the previous chunk.

Therefore, we avoid generating a chunk containing only repeated content.

---

## 4. Why do we need token-based chunking?

Our word-based implementation counts words using:

```python
words = text.split()
```

However, embedding models process **tokens**, not words.

Our embedding model is:

```text
BAAI/bge-small-en-v1.5
```

It uses a tokenizer that can split one word into multiple subword tokens.

For example, in our actual experiment:

```text
backend
    ↓
['back', '##end']

Kafka
    ↓
['ka', '##fk', '##a']

PostgreSQL
    ↓
['post', '##gre', '##s', '##q', '##l']
```

We observed:

| Chunk | Word count | Token count |
|---|---:|---:|
| 1 | 8 | 11 |
| 2 | 8 | 12 |
| 3 | 8 | 16 |
| 4 | 8 | 18 |

The token counts include `[CLS]` and `[SEP]`.

Although all four chunks contained eight words, their token counts were different.

### What problem does token-based chunking solve?

A word limit does not guarantee that text will fit within the embedding model's token limit.

For example:

```text
500 words
```

could produce more than:

```text
512 tokens
```

depending on the text.

Token-based chunking lets us control chunk size using the unit the model actually processes.

---

## 5. What are `[CLS]` and `[SEP]`?

**`[CLS]`** is a special token placed at the beginning of the text. Our BGE model uses its final embedding to represent the entire sentence.

**`[SEP]`** marks the end of a text segment or separates two segments.

For example:

```text
Java is a programming language
```

becomes:

```text
[CLS] java is a programming language [SEP]
```

When choosing a token budget, we must reserve room for these special tokens.

---

## 6. What does `##` mean in a token?

Our BGE tokenizer uses WordPiece-style subword tokens.

The `##` marker means:

> This token continues the preceding word.

For example:

```text
backend
    ↓
back + ##end
```

Compare:

```text
backend
    → ['back', '##end']

back end
    → ['back', 'end']
```

The marker helps distinguish a continuation piece from a piece that starts a new word.

It is not part of the original word.

---

## 7. Basic token-based chunking

Instead of splitting whitespace-separated words, we can split token IDs.

```python
token_ids = tokenizer.encode(
    text,
    add_special_tokens=False
)
```

We exclude special tokens during chunking because each chunk will receive its own special tokens later when passed to the embedding model.

The basic process is:

```text
Text
  ↓
Token IDs
  ↓
Split into token windows
  ↓
Apply overlap
  ↓
Decode each window into text
```

For example:

```text
Tokens:
A B C D E F G H

chunk_size = 4
overlap = 2
```

The chunks are:

```text
Chunk 1: A B C D
Chunk 2: C D E F
Chunk 3: E F G H
```

### Simplified implementation

```python
def chunk_text_by_tokens(text, chunk_size, overlap):

    token_ids = tokenizer.encode(
        text,
        add_special_tokens=False
    )

    chunks = []

    step = chunk_size - overlap
    previous_end_index = 0

    for start_index in range(0, len(token_ids), step):

        end_index = min(
            start_index + chunk_size,
            len(token_ids)
        )

        if previous_end_index == end_index:
            break

        chunk_token_ids = token_ids[start_index:end_index]

        chunk_text = tokenizer.decode(
            chunk_token_ids,
            skip_special_tokens=True
        )

        chunks.append(chunk_text)

        previous_end_index = end_index

    return chunks
```

This example illustrates the algorithm. A production implementation should also validate `chunk_size` and `overlap`, as we did in our word-based version.

---

## 8. Problem with naive token-based chunking

Our token-based chunker produced:

```text
Chunk 3:
##fka is commonly used for event - driven systems. post
```

This happened because the token window split a word in the middle.

For example:

```text
Kafka
    ↓
['ka', '##fk', '##a']
```

One chunk could contain:

```text
['ka']
```

while the next starts with:

```text
['##fk', '##a']
```

When decoded independently, the second chunk cannot reliably reconstruct the original word.

Therefore, simple token slicing can produce awkward or malformed text.

---

## 9. Why did a 12-token chunk become 14 tokens?

In our experiment, we:

1. Split the original token IDs into a 12-token window.
2. Decoded those IDs into text.
3. Tokenized the decoded text again to count it.

These two tokenizations are not guaranteed to produce the same count.

For example:

```text
Original token window
       ↓
12 tokens
       ↓
Decode
       ↓
"##fka is commonly used ..."
       ↓
Tokenize again
       ↓
14 tokens
```

The text now contains literal `##` characters that were not present in the original word.

**To inspect the original token count, count the original token IDs instead of retokenizing decoded text.**

```python
print(len(chunk_token_ids))
```

---

## 10. `convert_ids_to_tokens()` vs `decode()`

These methods are related but have different purposes.

For the word:

```text
backend
```

### `convert_ids_to_tokens()`

```python
tokens = tokenizer.convert_ids_to_tokens(token_ids)
```

Result:

```text
['back', '##end']
```

It preserves individual tokens, making it useful for debugging.

### `decode()`

```python
text = tokenizer.decode(token_ids)
```

Result:

```text
backend
```

It attempts to reconstruct readable text from token IDs.

**Remember:**

```text
convert_ids_to_tokens()
    → inspect individual tokens

decode()
    → reconstruct readable text
```

Decoding an incomplete word may not reconstruct the original text correctly.

---

## 11. Smart chunking: token budget + word boundaries

To avoid splitting words, our final learning implementation uses a hybrid approach:

- **Words determine where we can split.**
- **Tokens determine whether a chunk fits within the budget.**
- **Overlap repeats some complete words between chunks.**

The algorithm is:

```text
Take a word
     ↓
Add the next word
     ↓
Count tokens
     ↓
Within max_tokens?
     ├── Yes → continue adding words
     └── No  → finish current chunk
                    ↓
              Repeat some words
                    ↓
              Start next chunk
```

This avoids breaking words such as `Kafka`, `backend`, and `PostgreSQL` across chunk boundaries.

---

## 12. Final smart chunking implementation

File:

```text
scripts/smart_chunking.py
```

```python
from transformers import AutoTokenizer


MODEL_NAME = "BAAI/bge-small-en-v1.5"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


def count_tokens(text):
    """
    Count tokens including [CLS] and [SEP].
    """

    return len(
        tokenizer.encode(
            text,
            add_special_tokens=True
        )
    )


def chunk_text(text, max_tokens, overlap_words):
    """
    Split text into chunks using complete word boundaries.

    max_tokens:
        Maximum tokens per chunk, including special tokens.

    overlap_words:
        Desired number of complete words repeated between chunks.
        Actual overlap may be reduced to keep chunks within the limit.
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

        # Keep adding whole words while the candidate
        # stays within the model's token budget.
        while end_index < len(words):

            candidate_words = words[start_index:end_index + 1]

            candidate_text = " ".join(candidate_words)

            if count_tokens(candidate_text) > max_tokens:
                break

            end_index += 1

        # Even one word cannot fit in the configured budget.
        if end_index == start_index:
            raise ValueError(
                f"Word cannot fit within {max_tokens} tokens: "
                f"{words[start_index]}"
            )

        # Python slicing excludes end_index.
        chunk = " ".join(words[start_index:end_index])

        chunks.append(chunk)

        # Entire document has been covered.
        if end_index == len(words):
            break

        # Start within the previous chunk to repeat
        # the desired number of complete words.
        next_start = max(
            start_index + 1,
            end_index - overlap_words
        )

        # Reduce overlap if repeating all desired words
        # leaves insufficient space for the next new word.
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
            "Token count:",
            count_tokens(chunk)
        )
```

---

## 13. Why is `end_index` excluded from the chunk?

Our code uses:

```python
chunk = " ".join(words[start_index:end_index])
```

Python slicing includes `start_index` but excludes `end_index`.

Example:

```text
Index:  0 1 2 3 4 5 6 7
Word:   A B C D E F G H
```

With:

```python
start_index = 0
end_index = 5
```

the slice:

```python
words[0:5]
```

contains:

```text
A B C D E
```

To repeat the last two words:

```text
D E
```

the next chunk starts at:

```python
next_start = end_index - overlap_words

# 5 - 2 = 3
```

Index `3` points to `D`.

This is why our overlap calculation uses:

```python
end_index - overlap_words
```

rather than subtracting an additional `1`.

---

## 14. Why can actual overlap be smaller than requested?

Suppose:

```text
max_tokens = 10
overlap_words = 2
```

The last two words of a chunk might already consume many tokens.

If repeating them leaves no space for the next new word, the chunker reduces the overlap.

Our code does this using:

```python
while next_start < end_index:

    next_candidate = " ".join(
        words[next_start:end_index + 1]
    )

    if count_tokens(next_candidate) <= max_tokens:
        break

    next_start += 1
```

For example:

```text
Chunk 1 → Chunk 2: 2 overlapping words
Chunk 2 → Chunk 3: 1 overlapping word
Chunk 3 → Chunk 4: 2 overlapping words
```

This is acceptable for our learning implementation.

The priorities are:

1. Do not exceed the token budget.
2. Do not skip original content.
3. Avoid generating redundant chunks.
4. Preserve natural word boundaries.

---

## 15. Limitations of our implementation

Our smart chunker is suitable for learning and initial experiments, but it is not a complete production document parser.

It currently:

- Uses whitespace to identify words.
- Does not explicitly preserve sentence or paragraph boundaries.
- Reconstructs text with `" ".join(...)`, which changes original whitespace.
- Uses a word-based overlap target rather than a fixed token overlap.
- Rejects a single word that cannot fit within the token budget.

For our next step, these limitations are acceptable.

We will use this chunker to understand document ingestion before adding more sophisticated document-processing features.

---

# Final Mental Model

```text
                   DOCUMENT
                      │
                      ▼
                 Basic chunking
                      │
         Split large text into pieces
                      │
                      ▼
                Add overlap
                      │
         Preserve boundary context
                      │
                      ▼
             Token-based chunking
                      │
         Control model input size
                      │
                      ▼
        Respect natural word boundaries
                      │
         Avoid broken words like ##fka
                      │
                      ▼
              FINAL TEXT CHUNKS
                      │
                      ▼
             Generate embeddings
                      │
                      ▼
                PostgreSQL
```

## Key Takeaways

**Chunking** splits large documents into smaller, more focused pieces.

**Overlap** repeats some content so context is not lost between chunks.

**Token-based chunking** controls the amount of text according to the embedding model's actual input units.

**Word-boundary-aware chunking** prevents the token window from splitting words into malformed text.

For our project, the final approach combines a token budget with complete-word boundaries and a desired overlap.

---

# Next Step — Step 5: Document Ingestion

We will build the following pipeline:

```text
Local document (.txt or .md)
            ↓
Read file content
            ↓
Smart chunking
            ↓
Generate embedding for each chunk
            ↓
Store chunk + embedding in PostgreSQL
```

After ingestion, we will be ready to perform semantic search over actual documents rather than only the three example sentences.