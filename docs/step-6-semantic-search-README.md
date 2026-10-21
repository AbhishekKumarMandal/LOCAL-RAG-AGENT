# Step 6 — Semantic Search

## 1. What is semantic search?

Semantic search retrieves information based on the **meaning of a question**, rather than relying only on matching keywords.

In Step 5, we ingested `backend_notes.md` into PostgreSQL. Each document chunk has:

- Its original text
- A document name and chunk index
- A 384-dimensional embedding

Now, when a user asks a question, we generate its embedding and compare it against the stored chunk embeddings.

Our retrieval pipeline is:

```text
User question
      ↓
Generate question embedding
      ↓
PostgreSQL + pgvector
      ↓
Compare question against stored embeddings
      ↓
Rank chunks by cosine distance
      ↓
Return relevant chunks and metadata
```

**Semantic search retrieves relevant text. It does not generate an answer.**

Answer generation will be added in Step 7 — RAG.

---

## 2. Files used in this step

| File | Responsibility |
|---|---|
| `scripts/step_06_1_semantic_search.py` | Generate question embeddings and retrieve matching document chunks |
| `scripts/step_06_2_test_retrieval.py` | Test relevant and unrelated questions with a similarity threshold |

We reused:

- `step_01_3_real_embeddings.py` — Generate embeddings.
- `step_03_1_database_utils.py` — Connect to PostgreSQL.
- `step_03_2_store_embedding.py` — Convert embeddings into pgvector format.

The complete implementations remain in the numbered Python scripts.

---

## 3. Our existing database

We search the `document_chunks` table created in Step 5:

```sql
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_name TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL
);
```

We previously ingested `backend_notes.md` and stored three chunks:

```text
backend_notes.md
       ↓
Chunk 0
Chunk 1
Chunk 2
       ↓
Three 384-dimensional embeddings
       ↓
document_chunks
```

We do not regenerate these document embeddings for every question.

---

## 4. Step 6.1 — Generate the question embedding

Suppose the user asks:

```text
How do Kafka consumer groups work?
```

We use our existing embedding generator:

```python
question_embedding = generate_embedding(question)
```

This converts the question into a normalized, 384-dimensional vector.

We then convert the Python list into pgvector's accepted textual representation:

```python
question_vector = embedding_to_pgvector(
    question_embedding
)
```

The resulting vector will be compared against the embeddings already stored in PostgreSQL.

### Why use the same embedding model?

The document chunks and user questions must be represented in a compatible vector space.

In this project, both are embedded using:

```text
BAAI/bge-small-en-v1.5
```

This lets us compare their vectors using cosine distance.

---

## 5. Cosine distance in PostgreSQL

In Step 2, we learned cosine similarity.

In Step 3, we learned that pgvector provides the cosine-distance operator:

```sql
<=>
```

The relationship is:

```text
cosine_similarity = 1 - cosine_distance
```

Therefore:

```sql
1 - (embedding <=> %s::vector)
```

calculates cosine similarity between a stored chunk embedding and the user's question embedding.

### Why `%s::vector`?

`%s` is a Psycopg parameter placeholder.

The `::vector` cast tells PostgreSQL to interpret the supplied vector string as a pgvector `vector` value.

For example:

```sql
'[1,2,3]'::vector
```

---

## 6. Retrieve the nearest chunks

Our basic semantic-search query is:

```sql
SELECT
    document_name,
    chunk_index,
    content,
    1 - (embedding <=> %s::vector) AS cosine_similarity
FROM document_chunks
ORDER BY embedding <=> %s::vector
LIMIT %s;
```

We pass the parameters in order:

```python
(
    question_vector,
    question_vector,
    top_k
)
```

### Why is `question_vector` passed twice?

Each `%s` represents a separate SQL parameter.

The first vector calculates the similarity returned in the result:

```sql
1 - (embedding <=> %s::vector)
```

The second vector is used for ordering:

```sql
ORDER BY embedding <=> %s::vector
```

Both represent the same question embedding.

### Why order by distance?

Smaller cosine distance means the vectors are closer.

```text
Smaller distance
       ↓
Higher cosine similarity
       ↓
Closer semantic match
```

Therefore, we use:

```sql
ORDER BY embedding <=> %s::vector
```

to retrieve the nearest chunks first.

---

## 7. What is `top_k`?

`top_k` controls the maximum number of chunks to retrieve.

For example:

```python
semantic_search(
    question,
    top_k=3
)
```

corresponds to:

```sql
LIMIT 3
```

With only three stored chunks, `top_k=3` returns all three, ordered by distance.

Later, when we have many documents, we can retrieve only a small number of the closest chunks.

---

## 8. Why return dictionaries?

Psycopg's `fetchall()` returns database rows as tuples by default.

For example:

```python
(
    "backend_notes.md",
    1,
    "Kafka consumer groups allow multiple consumers...",
    0.7495
)
```

Instead of requiring other parts of the application to remember column positions, we convert the row into a dictionary:

```python
{
    "document_name": "backend_notes.md",
    "chunk_index": 1,
    "content": "Kafka consumer groups allow multiple consumers...",
    "cosine_similarity": 0.7495
}
```

Later, our RAG code can access:

```python
match["content"]
```

to retrieve the text.

It can also use:

```python
match["document_name"]
```

to identify the source.

---

## 9. Our first semantic-search result

We searched for:

```text
How do Kafka consumer groups work?
```

Our actual results were:

| Rank | Chunk index | Cosine similarity |
|---:|---:|---:|
| 1 | 1 | 0.7495 |
| 2 | 0 | 0.5482 |
| 3 | 2 | 0.5480 |

Chunk 1 ranked first.

It contained:

```text
Kafka consumer groups allow multiple consumers to share the work
of processing topic partitions.
```

This was the information relevant to the question.

### Observation

Our current chunks can contain information from multiple topics because the Step 4 chunker does not preserve Markdown heading or paragraph boundaries.

For example, Chunk 1 contains Kafka information followed by PostgreSQL information.

This is a chunking-quality limitation, not necessarily a search error.

---

## 10. The problem with nearest-neighbor search

Suppose the user asks:

```text
What is the capital of France?
```

Our document only discusses Java, Spring Boot, Kafka, and PostgreSQL.

However, this SQL still returns the nearest stored chunks:

```sql
ORDER BY embedding <=> %s::vector
LIMIT 3;
```

Why?

Because it means:

> Return the three closest vectors.

It does not mean:

> Return only chunks that contain the answer.

**The nearest chunk is not necessarily relevant or sufficient to answer a question.**

To handle this, we experimented with a minimum similarity threshold.

---

## 11. Optional similarity threshold

We extended our search function:

```python
def semantic_search(
    question,
    top_k=3,
    min_similarity=None
):
```

The parameter has two possible behaviors:

```python
min_similarity = None
```

means no similarity filtering.

And:

```python
min_similarity = 0.65
```

means only return chunks whose cosine similarity is at least `0.65`.

For example:

```python
matches = semantic_search(
    question,
    top_k=3,
    min_similarity=0.65
)
```

**The value `0.65` is an experimental threshold, not a universal recommendation for the BGE model.**

---

## 12. Applying the threshold in PostgreSQL

Our SQL uses:

```sql
WHERE (
    %s::double precision IS NULL
    OR 1 - (embedding <=> %s::vector) >= %s::double precision
)
```

### How does it work?

If:

```python
min_similarity = None
```

then the first condition is true:

```sql
NULL::double precision IS NULL
```

Therefore, no similarity filtering is applied.

If:

```python
min_similarity = 0.65
```

the first condition is false, so PostgreSQL checks:

```sql
cosine_similarity >= 0.65
```

Only qualifying chunks are returned.

### Why is there no `min_similarity` column?

`min_similarity` is a Python function parameter, not a database column.

We send its value into the query using `%s`.

The database compares the calculated similarity against that supplied value.

---

## 13. The `IndeterminateDatatype` error

During our experiment, we initially wrote:

```sql
%s IS NULL
```

and passed:

```python
min_similarity = None
```

PostgreSQL produced:

```text
psycopg.errors.IndeterminateDatatype:
could not determine data type of parameter $2
```

### Why?

Psycopg sent Python `None` as SQL `NULL`.

In:

```sql
%s IS NULL
```

PostgreSQL had no information about the intended type of the parameter.

The `IS NULL` check alone does not tell PostgreSQL whether the value should be an integer, text, float, or another type.

### How did we fix it?

We explicitly cast the parameter:

```sql
%s::double precision IS NULL
```

Now PostgreSQL knows the parameter's intended type even when the value is `NULL`.

`double precision` is PostgreSQL's floating-point type, suitable for our similarity threshold.

---

## 14. Our corrected threshold query

The corrected query is:

```sql
SELECT
    document_name,
    chunk_index,
    content,
    1 - (embedding <=> %s::vector) AS cosine_similarity
FROM document_chunks
WHERE (
    %s::double precision IS NULL
    OR 1 - (embedding <=> %s::vector) >= %s::double precision
)
ORDER BY embedding <=> %s::vector
LIMIT %s;
```

The parameters are:

```python
(
    question_vector,
    min_similarity,
    question_vector,
    min_similarity,
    question_vector,
    top_k
)
```

Each parameter corresponds to one `%s`, in the order it appears in the SQL query.

---

## 15. Step 6.2 — Test relevant and unrelated questions

We created:

```text
scripts/step_06_2_test_retrieval.py
```

We tested two questions with:

```python
min_similarity = 0.65
```

### Test 1 — Relevant question

```text
How do Kafka consumer groups work?
```

Actual output:

```text
Match 1

Document: backend_notes.md
Chunk index: 1
Similarity: 0.7495
```

The matching chunk contained the explanation of Kafka consumer groups.

### Test 2 — Unrelated question

```text
What is the capital of France?
```

Actual output:

```text
No sufficiently similar chunks found.
```

None of our stored chunks passed the similarity threshold for that question.

This demonstrates how optional threshold filtering can prevent some unrelated chunks from being returned.

---

## 16. Does a similarity threshold guarantee the answer exists?

No.

Cosine similarity measures the closeness of embeddings, not whether a chunk actually answers the question.

A chunk can be semantically related to a question without containing the requested fact.

Likewise, a useful chunk might have a relatively low similarity score.

Therefore:

```text
High similarity ≠ guaranteed answer
```

Our threshold worked for the two questions we tested, but it needs evaluation with more documents and questions.

Later, our RAG application should also instruct the language model not to invent information when the retrieved context is insufficient.

---

## 17. Understanding the model-loading messages

When running our scripts, we observed:

```text
Loading weights: 100% ... 199/199
```

This means the BGE model's saved numerical parameters are being loaded into memory.

It does not mean the model is being trained.

The `199/199` represents the tracked weight-loading entries, not 199 individual numerical parameters or 199 tokens.

We also observed:

```text
Warning: You are sending unauthenticated requests to the HF Hub.
```

This means the Hugging Face library accessed the Hub without an authentication token.

Public models can generally be accessed without signing in, but unauthenticated requests have stricter rate limits.

The warning does not indicate a PostgreSQL or embedding error.

After the model has been downloaded, its files are normally cached locally.

---

# Final Mental Model

```text
                  SEMANTIC SEARCH

                  User question
                        │
                        ▼
                 BGE embedding model
                        │
                        ▼
               384-dimensional vector
                        │
                        ▼
                 PostgreSQL + pgvector
                        │
                        ▼
             Compare with stored embeddings
                        │
                        ▼
                 Calculate cosine distance
                        │
                        ▼
                Order by smallest distance
                        │
                        ▼
                    Apply top_k
                        │
                        ▼
             Optional similarity threshold
                        │
                        ▼
              Return matching document chunks
                        │
                        ▼
                Content + source metadata
```

## Key Takeaways

**Semantic search** retrieves text based on vector similarity.

**Cosine distance** is calculated using pgvector's `<=>` operator.

**Cosine similarity** can be calculated as `1 - cosine_distance`.

**Top-k** limits the maximum number of retrieved chunks.

**Similarity threshold** optionally filters out chunks below a chosen score.

**Metadata** identifies the source document and position of each retrieved chunk.

**Nearest does not always mean relevant:** retrieval similarity alone cannot guarantee that a chunk contains the answer.

---

# Next Step — Step 7: Retrieval-Augmented Generation (RAG)

We now have two important parts of the system:

```text
Step 5: Ingestion
Document → Chunks → Embeddings → PostgreSQL

Step 6: Retrieval
Question → Embedding → Nearest document chunks
```

In Step 7, we will combine retrieval with answer generation:

```text
User question
      ↓
Semantic search
      ↓
Retrieved document chunks
      ↓
Build a prompt containing the question and context
      ↓
Send the prompt to an LLM
      ↓
Generate an answer grounded in the retrieved context
```

This is the foundation of our local RAG application.