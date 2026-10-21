# Step 7 — Retrieval-Augmented Generation (RAG)

## 1. What is RAG?

RAG stands for:

```text
Retrieval-Augmented Generation
```

It combines:

```text
Retrieval
    +
Generation
```

The idea is:

```text
User question
      ↓
Retrieve relevant information
      ↓
Give retrieved information to an LLM
      ↓
Generate an answer
```

In our project:

```text
User question
      ↓
Generate question embedding
      ↓
PostgreSQL + pgvector
      ↓
Retrieve relevant document chunks
      ↓
Build a prompt
      ↓
Send prompt to local LLM
      ↓
Generate answer
```

---

## 2. Why do we need RAG?

An LLM does not automatically know about the documents stored in our PostgreSQL database.

The LLM cannot directly read:

```text
document_chunks
```

or understand:

```text
VECTOR(384)
```

Our Python application must first retrieve the relevant text and then provide that text to the LLM.

For example:

```text
Question:
How do Kafka consumer groups work?

        ↓

Semantic search

        ↓

Retrieved context:
Kafka consumer groups allow multiple consumers
to share the work of processing topic partitions.

        ↓

LLM

        ↓

Generated answer
```

---

## 3. RAG vs semantic search

In Step 6, our application returned relevant chunks:

```text
Question
    ↓
Vector search
    ↓
Relevant chunk
```

That is **retrieval**.

RAG adds another step:

```text
Relevant chunk
    +
Question
    ↓
LLM
    ↓
Natural-language answer
```

So:

```text
Semantic search
    = retrieves information

RAG
    = retrieves information + generates an answer
```

---

## 4. Step 7.1 — Build the RAG prompt

We created:

```text
scripts/step_07_1_build_rag_prompt.py
```

The purpose of this step was to construct the exact text that would be sent to the LLM.

A RAG prompt contains three main parts:

```text
Instructions
+
Retrieved context
+
User question
```

Example:

```text
You are a helpful assistant.

Answer the question using only the provided context.

Context:
Kafka consumer groups allow multiple consumers to share
the work of processing topic partitions.

Question:
How do Kafka consumer groups work?

Answer:
```

---

## 5. Why do we include the retrieved context in the prompt?

The LLM has no direct connection to PostgreSQL.

Our application retrieves the relevant chunks and adds them to the prompt:

```text
PostgreSQL
    ↓
Retrieved text
    ↓
Prompt
    ↓
LLM
```

The LLM sees plain text, not vectors.

The vector is only used to find the correct database row.

---

## 6. Include source metadata in the context

We included:

```text
Source: backend_notes.md
Chunk: 1
```

alongside the content.

Example:

```text
Source: backend_notes.md, Chunk: 1
Content: Kafka consumer groups allow multiple consumers...
```

This is useful because later we can:

- display citations
- show where an answer came from
- trace retrieved information
- debug incorrect retrieval

---

## 7. Prompt formatting issue

Initially, our prompt used an indented triple-quoted string.

That caused output such as:

```text
    Answer the question...
    Context:
    Question:
```

because Python preserves indentation inside triple-quoted strings.

We changed the prompt construction to explicit string concatenation:

```python
prompt = (
    "You are a helpful assistant.\n\n"
    "Answer the question using only the provided context.\n"
    ...
)
```

This produced cleaner prompt formatting.

---

## 8. Step 7.2 — Complete RAG generation

We connected:

```text
semantic_search()
```

with:

```text
build_rag_prompt()
```

and then:

```text
generate_text()
```

The complete flow became:

```text
Question
   ↓
BGE embedding
   ↓
PostgreSQL semantic search
   ↓
Relevant chunks
   ↓
Build RAG prompt
   ↓
Ollama
   ↓
Qwen2.5:3b-instruct
   ↓
Generated answer
```

---

## 9. Our first generated RAG answer

We asked:

```text
How do Kafka consumer groups work?
```

The model initially generated:

```text
Kafka consumer groups allow multiple consumers to share
the work of processing topic partitions.

If a consumer within the group fails, another consumer
can take over that consumer's assigned partitions...
```

The first statement was present in our document.

However, the failure/rebalancing explanation was **not present in the retrieved context**.

The LLM added that information from its own pretrained knowledge.

---

## 10. Important concept — grounding

A grounded answer should only contain information supported by the retrieved context.

Our first prompt said:

```text
Answer using only the provided context.
Do not invent facts.
```

But the LLM still added extra Kafka knowledge.

Why?

Because an LLM always generates tokens using the knowledge encoded in its trained parameters.

A prompt can strongly instruct the model not to use prior knowledge, but it cannot literally remove that knowledge from the model.

---

## 11. Strict grounding prompt

We improved the prompt:

```text
Answer using ONLY facts explicitly stated in the context.

Do not use prior knowledge.

Do not add explanations, assumptions, examples,
or facts that are not directly supported by the context.

If a statement is not explicitly present in the context,
do not include it.
```

Our final prompt was similar to:

```python
prompt = (
    "You are a helpful assistant.\n\n"
    "Answer the question using only the provided context.\n"
    "If the context does not contain the answer, say:\n"
    "\"I don't have enough information in the provided documents.\"\n\n"
    "Do not invent facts.\n\n"
    "Answer using ONLY facts explicitly stated in the context.\n\n"
    "Do not use prior knowledge.\n\n"
    "Do not add explanations, assumptions, examples, or facts "
    "that are not directly supported by the context.\n\n"
    "If a statement is not explicitly present in the context, "
    "do not include it.\n\n"
    f"Context:\n{context}\n\n"
    f"Question:\n{question}\n\n"
    "Answer:"
)
```

---

## 12. Result after stricter grounding

With the stricter prompt, the answer became:

```text
Kafka consumer groups allow multiple consumers
to share the work of processing topic partitions.
```

This answer was directly supported by the retrieved document.

No extra Kafka behavior was added.

---

## 13. Can prompt instructions guarantee grounding?

No.

A stricter prompt improves behavior, but does not provide a mathematical guarantee that the LLM will never add unsupported information.

Production RAG systems may add extra safeguards such as:

```text
Generated answer
      ↓
Grounding check
      ↓
Verify every claim against context
      ↓
Final answer
```

Other approaches include:

- requiring citations
- claim verification
- second-pass validation
- structured outputs
- rejecting unsupported statements

For our learning project, the strict prompt provides sufficient grounding.

---

## 14. What happens when retrieval finds no relevant context?

Our semantic search already supports:

```text
min_similarity
```

If no chunks pass the threshold, we do not need to call the LLM.

Instead, we can directly return:

```text
I don't have enough information in the provided documents.
```

Conceptually:

```text
Question
   ↓
Semantic search
   ↓
Any relevant chunks?
   │
   ├── No
   │    ↓
   │  Return "not enough information"
   │
   └── Yes
        ↓
      Build prompt
        ↓
      Call LLM
```

This avoids asking the LLM to answer when no useful context was retrieved.

---

## 15. RAG does not mean the LLM reads vectors

The LLM does not receive:

```text
[-0.03, 0.01, ...]
```

The vector database is used only during retrieval.

The pipeline is:

```text
Question
   ↓
Question embedding
   ↓
Vector search
   ↓
Database row found
   ↓
Retrieve TEXT from row
   ↓
Send TEXT to LLM
```

This is why our database stores both:

```sql
content TEXT
embedding VECTOR(384)
```

The embedding finds the row.

The content is what the LLM actually reads.

---

## 16. Why not simply send the whole document to the LLM?

For a small document, we absolutely can.

For example:

```text
Document
+
Question
   ↓
LLM
   ↓
Answer
```

For our tiny `backend_notes.md`, this would work.

RAG becomes useful when the knowledge base grows.

For example:

```text
10,000 documents
5,000,000 tokens
```

We cannot efficiently send all of that to the LLM every time.

Instead:

```text
Question
   ↓
Vector search over all documents
   ↓
Retrieve 3 relevant chunks
   ↓
Send only those chunks to LLM
```

Benefits:

- smaller prompts
- lower latency
- less computation
- works with knowledge bases larger than the model context window
- easier to update knowledge without retraining the LLM

---

## 17. Tokenization does not replace retrieval

An LLM also tokenizes its input.

However:

```text
Tokenization
    ≠
Semantic search
```

These are different operations:

```text
Tokenization
    = convert text into token IDs

Embedding
    = represent semantic meaning as a vector

Vector search
    = find similar information

LLM generation
    = generate output tokens
```

If the entire document fits inside the model's context window, retrieval may not be necessary.

If the knowledge base is large, RAG selects the relevant subset before sending text to the LLM.

---

# Final Mental Model

```text
                       RAG

                  User question
                        │
                        ▼
                Generate embedding
                        │
                        ▼
              PostgreSQL + pgvector
                        │
                        ▼
              Retrieve relevant chunks
                        │
                        ▼
                  Build RAG prompt
                        │
          ┌─────────────┴─────────────┐
          │                           │
      Instructions                Context
                                      +
                                  Question
          │                           │
          └─────────────┬─────────────┘
                        ▼
                       LLM
                        │
                        ▼
              Grounded natural-language
                       answer
```

## Key Takeaways

**RAG = Retrieval + Generation.**

**Semantic search retrieves relevant text.**

**The LLM receives text, not vector embeddings.**

**Prompt grounding is important because the LLM can otherwise add information from its pretrained knowledge.**

**A strict prompt reduces unsupported information but cannot guarantee perfect grounding.**

**Small documents can be passed directly to an LLM. RAG becomes especially useful for large knowledge bases.**

---

# Step 7 Status

The complete RAG pipeline is now working:

```text
Document ingestion ✅
Semantic retrieval ✅
Prompt construction ✅
Local LLM generation ✅
Strict grounded answering ✅
```