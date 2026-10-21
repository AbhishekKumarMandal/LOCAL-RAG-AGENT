# Step 5 — Document Ingestion

## 1. What is document ingestion?

Document ingestion is the process of reading information from a source, preparing it for retrieval, generating embeddings, and storing the results in a vector database.

In our project, the pipeline is:

```text
Local document (.md / .txt)
          ↓
Read document
          ↓
Split into chunks
          ↓
Generate one embedding per chunk
          ↓
Store chunks + metadata + embeddings in PostgreSQL
```

**Ingestion happens before the user asks a question.**

We process and store documents in advance so that we do not need to read and embed them again for every search.

---

## 2. Files used in this step

| File | Responsibility |
|---|---|
| `data/documents/backend_notes.md` | Sample knowledge document |
| `scripts/step_05_1_read_document.py` | Read the document |
| `scripts/step_05_2_chunk_document.py` | Split the document and attach metadata |
| `scripts/step_05_3_ingest_document.py` | Generate embeddings and insert chunks into PostgreSQL |

We also reused functionality from earlier steps:

- `step_01_3_real_embeddings.py` — embedding generation.
- `step_03_1_database_utils.py` — PostgreSQL connection.
- `step_03_2_store_embedding.py` — conversion to pgvector format.
- `step_04_4_smart_chunking.py` — token-aware chunking.

The complete implementations remain in these Python files.

---

## 3. Our sample document

We created:

```text
data/documents/backend_notes.md
```

It contains short sections about:

- Java
- Spring Boot
- Apache Kafka
- PostgreSQL and pgvector

For example:

```md
## Apache Kafka

Apache Kafka is a distributed event-streaming platform. Producers
publish messages to topics, and consumers read messages from those
topics.

Kafka consumer groups allow multiple consumers to share the work
of processing topic partitions.
```

Later, we want to retrieve this information when someone asks:

```text
How do Kafka consumer groups work?
```

---

## 4. Step 5.1 — Read the document

We used Python's `pathlib` library to locate and read the Markdown file.

### Locating the project root

```python
PROJECT_ROOT = Path(__file__).resolve().parent.parent
```

Here:

- `__file__` refers to the current Python file.
- `resolve()` returns its absolute path.
- The first `.parent` moves from the script to the `scripts/` directory.
- The second `.parent` moves to the project root.

For example:

```text
local-rag-agent/
└── scripts/
    └── step_05_1_read_document.py
```

The expression returns the path to:

```text
local-rag-agent/
```

For a more deeply nested script, we can use `parents[index]`. For example, `parents[2]` moves three directory levels upward from the file.

### Reading the file

The important operation is:

```python
content = file_path.read_text(encoding="utf-8")
```

This reads the complete file into a Python string.

We also check whether the file exists before reading it:

```python
if not file_path.is_file():
    raise FileNotFoundError(...)
```

### Actual output

Our experiment produced:

```text
Document: backend_notes.md

Total characters: 881
Total words: 122
```

This confirmed that Python successfully read the document.

---

## 5. Why do we need document metadata?

In Step 3, we created a table for experimenting with individual sentences:

```sql
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL
);
```

However, our ingestion pipeline needs to support documents from multiple sources.

Imagine:

```text
data/documents/
├── backend_notes.md
├── kafka_notes.md
└── spring_boot_notes.md
```

Each document may produce several chunks.

If we only store the chunk text and embedding, we won't know which document each chunk came from.

Therefore, we attach **metadata**.

For our current project:

```text
document_name
chunk_index
content
embedding
```

The source document and chunk index allow us to identify where a retrieved piece of information came from.

---

## 6. The `document_chunks` table

We created a separate table for document ingestion:

```sql
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_name TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL
);
```

### Column meanings

| Column | Purpose |
|---|---|
| `id` | Unique row identifier |
| `document_name` | Source filename |
| `chunk_index` | Position of the chunk within the document |
| `content` | Text belonging to the chunk |
| `embedding` | 384-dimensional embedding of that text |

Example:

```text
id:
1

document_name:
backend_notes.md

chunk_index:
0

content:
# Backend Engineering Notes ## Java Java is...

embedding:
[-0.030858362, 0.030681029, ...]
```

We retained the original `embeddings` table for the experiments from Step 3.

### Why store `chunk_index`?

A document can be represented as:

```text
backend_notes.md
    │
    ├── Chunk 0
    ├── Chunk 1
    └── Chunk 2
```

The index helps us identify the original order of chunks and can later help retrieve neighboring content.

### Limitation of storing only the filename

Two different files could both be named `notes.md`.

For a larger project, we could store a relative source path or introduce a separate `documents` table with a unique document ID.

For our learning project, we are using unique filenames.

---

## 7. Step 5.2 — Prepare document chunks

We reused the smart chunker developed in Step 4:

```python
chunks = chunk_text(
    document_content,
    max_tokens=100,
    overlap_words=10
)
```

### What does `max_tokens=100` mean?

Each chunk must contain at most 100 tokens according to our BGE tokenizer, including `[CLS]` and `[SEP]`.

It does not mean every chunk must contain exactly 100 tokens.

### What does `overlap_words=10` mean?

The chunker tries to repeat up to ten complete words between consecutive chunks.

This helps preserve context near chunk boundaries.

The actual overlap may be smaller if repeating all ten words would leave insufficient room for new content within the token limit.

These values are learning settings, not universal RAG defaults.

---

## 8. Attach metadata to each chunk

Our smart chunker returns a list of text strings:

```python
[
    "Chunk 0 text",
    "Chunk 1 text",
    "Chunk 2 text"
]
```

We then create a dictionary for each chunk:

```python
{
    "document_name": "backend_notes.md",
    "chunk_index": 0,
    "content": "Chunk 0 text"
}
```

The key operation is:

```python
for chunk_index, content in enumerate(chunks):

    prepared_chunks.append({
        "document_name": file_path.name,
        "chunk_index": chunk_index,
        "content": content
    })
```

`enumerate(chunks)` provides both the index and the chunk content.

By default, indexing starts at `0`, which is the convention we use for `chunk_index`.

At this stage, no embeddings or database inserts have happened.

---

## 9. Our actual chunking results

We obtained:

| Chunk index | Token count |
|---:|---:|
| 0 | 100 |
| 1 | 100 |
| 2 | 27 |

The final chunk was shorter because it contained the remaining document text, including overlap from the previous chunk.

This is expected behavior.

### Observation: Markdown formatting was flattened

Our current smart chunker uses:

```python
words = text.split()
```

and reconstructs text using:

```python
" ".join(words[start_index:end_index])
```

Therefore, original line breaks are replaced by spaces.

For example:

```md
# Backend Engineering Notes

## Java

Java is a programming language.
```

becomes:

```text
# Backend Engineering Notes ## Java Java is a programming language.
```

This is acceptable for our current learning experiment, but it does not preserve the original Markdown layout.

Later, we can improve the chunker to respect paragraphs and headings.

---

## 10. Step 5.3 — Generate embeddings

For every prepared chunk, we call our existing embedding generator:

```python
embedding = generate_embedding(
    item["content"]
)
```

Our model is:

```text
BAAI/bge-small-en-v1.5
```

It produces a normalized, 384-dimensional embedding for each chunk.

Conceptually:

```text
Chunk 0 → Embedding 0 (384 values)

Chunk 1 → Embedding 1 (384 values)

Chunk 2 → Embedding 2 (384 values)
```

### Why one embedding per chunk?

Each embedding represents a smaller portion of the document.

When a user asks about Kafka, the search can identify a Kafka-related chunk instead of treating the entire document as a single representation.

---

## 11. Store chunks in PostgreSQL

We convert each Python embedding into pgvector's accepted textual representation using our earlier helper:

```python
vector_value = embedding_to_pgvector(
    embedding
)
```

For example:

```text
Python list:

[0.12, -0.03, 0.44]
```

becomes:

```text
pgvector textual representation:

[0.12,-0.03,0.44]
```

Then we insert the metadata, text, and vector.

The important SQL is:

```sql
INSERT INTO document_chunks (
    document_name,
    chunk_index,
    content,
    embedding
)
VALUES (%s, %s, %s, %s::vector);
```

### Why `%s::vector`?

`%s` is Psycopg's parameter placeholder.

The `::vector` cast tells PostgreSQL to interpret the supplied vector string as the pgvector `vector` type.

We use SQL parameters instead of manually inserting Python values into an SQL string.

---

## 12. Why use one database connection?

We open one connection for the document and reuse it while inserting the chunks:

```python
with get_connection() as connection:
    with connection.cursor() as cursor:
        # Insert chunks here.
```

This avoids creating a new database connection for every chunk.

The connection context also manages the transaction:

- If the block completes successfully, Psycopg commits the transaction.
- If an exception occurs, the transaction is rolled back.

This lets us handle the document's database inserts as a single transaction.

---

## 13. Our actual ingestion results

We ran:

```bash
python scripts/step_05_3_ingest_document.py
```

The terminal displayed:

```text
Document: backend_notes.md
Chunks to ingest: 3

Stored chunk 0 (384 dimensions)
Stored chunk 1 (384 dimensions)
Stored chunk 2 (384 dimensions)

Document ingestion completed.
```

We also inspected the `document_chunks` table using DBeaver and confirmed that the generated data was stored.

---

## 14. Verify data using SQL

Instead of selecting all 384 embedding values, we can display a short preview:

```sql
SELECT
    id,
    document_name,
    chunk_index,
    LEFT(content, 100) AS content_preview,
    vector_dims(embedding) AS dimensions
FROM document_chunks
ORDER BY document_name, chunk_index;
```

Here:

```sql
LEFT(content, 100)
```

displays the first 100 characters of each chunk.

And:

```sql
vector_dims(embedding)
```

returns the dimensionality of the stored vector.

For our model, each row should return:

```text
384
```

---

## 15. Current limitation: duplicate ingestion

Our script currently performs a normal `INSERT`.

If we run the script again, PostgreSQL inserts another copy of each chunk.

For example:

```text
First run  → 3 rows
Second run → 6 rows
Third run  → 9 rows
```

We have not implemented duplicate prevention or document updates yet.

Later, we can introduce a document identifier and a strategy to replace or update previously ingested chunks.

---

# Final Mental Model

```text
                    DOCUMENT INGESTION

                    backend_notes.md
                           │
                           ▼
                      Read file
                           │
                           ▼
                 Smart token chunking
                           │
                           ▼
                      Three chunks
                           │
               ┌───────────┼───────────┐
               ▼           ▼           ▼
            Chunk 0     Chunk 1     Chunk 2
               │           │           │
               ▼           ▼           ▼
           BGE Model   BGE Model   BGE Model
               │           │           │
               ▼           ▼           ▼
          Embedding 0  Embedding 1  Embedding 2
               │           │           │
               └───────────┼───────────┘
                           ▼
                  PostgreSQL + pgvector
                           │
                           ▼
                     document_chunks
```

## Key Takeaways

**Document ingestion:** Reads, prepares, embeds, and stores documents for future retrieval.

**Chunking:** Divides a document into smaller pieces.

**Metadata:** Identifies the source and position of each chunk.

**One embedding per chunk:** Enables retrieval of relevant document portions.

**PostgreSQL + pgvector:** Stores chunk text and embeddings for vector search.

**Ingestion and search are separate:** We ingest documents in advance and search them when a user asks a question.

---

# Next Step — Step 6: Semantic Search

We will implement:

```text
User question
       ↓
Generate question embedding
       ↓
Search document_chunks
       ↓
Calculate cosine distance
       ↓
Order by nearest embeddings
       ↓
Return relevant chunks + source metadata
```

This will allow our application to retrieve information from `backend_notes.md` using natural-language questions.

In Step 7, we will pass the retrieved chunks to an LLM to generate an answer using the document as context.