# Local RAG Agent

A hands-on Python project for learning how modern RAG, AI agents, tool calling, and MCP work by implementing the important concepts from the ground up.

The project intentionally avoids hiding the core logic behind high-level frameworks such as LangChain or LangGraph.

Instead, concepts such as embedding generation, chunking, semantic search, RAG, agent loops, tool execution, and MCP communication are implemented and explored directly.

---

## Project Overview

The project starts with basic text embeddings and gradually builds a complete local RAG and agent system.

The final application can:

1. Load and chunk local documents.
2. Generate embeddings for document chunks.
3. Store embeddings in PostgreSQL using pgvector.
4. Perform semantic similarity search.
5. Retrieve relevant document context.
6. Generate grounded answers using a local LLM through Ollama.
7. Expose tools such as a calculator and document search.
8. Let an AI agent decide which tool to use.
9. Maintain tool-call history across multi-step tasks.
10. Expose tools through an MCP server.
11. Discover and invoke those tools through an MCP client.
12. Run an MCP-based agent loop with Python-side validation and feedback.

---

## Architecture

```text
                          User
                            |
                            v
                           LLM
                            |
                     Agent Decision
                            |
                            v
                  Python Agent / Validator
                            |
                            v
                       MCP Client
                            |
                          stdio
                            |
                            v
                       MCP Server
                    /               \
                   v                 v
          calculator_tool     search_documents_tool
                                     |
                                     v
                              Semantic Search
                                     |
                                     v
                              PostgreSQL
                               + pgvector
                                     |
                                     v
                           Relevant Document Chunks
                                     |
                                     v
                              RAG Prompt
                                     |
                                     v
                              Ollama / Qwen
                                     |
                                     v
                              Grounded Answer
```

---

## Technology Stack

- Python 3.11
- PyTorch
- Hugging Face Transformers
- NumPy
- PostgreSQL
- pgvector
- psycopg
- Ollama
- Qwen2.5 3B Instruct
- MCP Python SDK

Embedding model:

```text
BAAI/bge-small-en-v1.5
```

Embedding dimension:

```text
384
```

---

## What Was Implemented

### 1. Embeddings

Learned how text becomes numerical vectors using:

```text
Text
  ↓
Tokenizer
  ↓
Token IDs
  ↓
Transformer
  ↓
Token Embeddings
  ↓
CLS Pooling
  ↓
L2 Normalization
  ↓
Embedding
```

Topics explored:

- tokens and token IDs
- attention masks
- token type IDs
- CLS and SEP tokens
- CLS pooling
- normalization
- embedding dimensions

---

### 2. Cosine Similarity

Implemented cosine similarity manually and used it to compare semantic similarity between embeddings.

Example:

```text
Java programming
vs
Java software development
```

produces a much higher similarity score than an unrelated sentence.

---

### 3. PostgreSQL + pgvector

PostgreSQL is used as the vector database.

The pgvector extension allows embeddings to be stored using:

```sql
VECTOR(384)
```

Semantic search uses cosine distance through pgvector.

Conceptually:

```text
similarity = 1 - cosine_distance
```

---

### 4. Chunking

Implemented multiple chunking approaches:

- word-based chunking
- overlapping chunks
- token-based chunking
- token debugging
- smarter token-aware chunking

This step also explored how subword tokenization affects chunk sizes.

---

### 5. Document Ingestion

Documents are:

```text
read
  ↓
chunked
  ↓
embedded
  ↓
stored in PostgreSQL
```

Each stored record keeps both the original text and its embedding.

---

### 6. Semantic Search

User questions are converted into embeddings and compared against stored document embeddings.

```text
Question
  ↓
Embedding
  ↓
pgvector similarity search
  ↓
Most relevant chunks
```

A minimum similarity threshold can be used to reject unrelated results.

---

### 7. Retrieval-Augmented Generation

Retrieved chunks are inserted into a grounded prompt before calling the LLM.

```text
Question
  ↓
Semantic Search
  ↓
Relevant Context
  ↓
RAG Prompt
  ↓
Local LLM
  ↓
Answer
```

The prompt instructs the model to answer only from the supplied context and return an explicit response when the documents do not contain enough information.

---

### 8. Local LLM with Ollama

Ollama is used as the local model runtime.

The project communicates directly with its local HTTP API instead of using a high-level LLM framework.

Model used:

```text
qwen2.5:3b-instruct
```

Topics explored include:

- prompt tokens
- generated tokens
- model context
- prompt caching
- temperature
- raw Ollama JSON responses

---

### 9. Tools

Two main tools were created:

```text
calculator
search_documents
```

The project demonstrates that an LLM does not execute Python directly.

Instead:

```text
LLM generates a tool request
        ↓
Python parses it
        ↓
Python executes the tool
        ↓
Tool result is returned to the LLM
```

---

### 10. Agent Loop

A manual agent loop was built without LangChain or LangGraph.

The loop supports:

```text
LLM decision
    ↓
tool call
    ↓
tool result
    ↓
history update
    ↓
next LLM decision
```

The project also explores:

- multi-step calculations
- operator precedence
- tool-call validation
- duplicate calls
- deterministic tool result reuse
- maximum iteration limits
- Python-side orchestration

---

### 11. MCP Server

The existing tools are exposed through an MCP server.

Current MCP tools:

```text
calculator_tool
search_documents_tool
```

The MCP server allows compatible clients to discover tool schemas and invoke tools without directly importing their Python implementations.

The project also explores:

- JSON-RPC
- stdio transport
- MCP initialization
- MCP Inspector
- tool discovery

---

### 12. MCP Client and MCP Agent

A Python MCP client was built using:

```python
ClientSession
StdioServerParameters
stdio_client
```

The client can:

```text
start the MCP server
initialize the MCP session
discover tools
call tools
receive MCP results
```

The final agent combines:

```text
LLM
+
Python orchestration
+
MCP client
+
MCP server
+
tools
```

Python performs deterministic validation while the LLM handles flexible tool selection and planning.

---

## Important Design Principle

The project follows this separation of responsibilities:

```text
LLM
= decides what to do

Python
= validates and orchestrates

MCP
= standardizes communication

MCP Server
= exposes capabilities

Tool
= performs the actual work
```

This was especially important when working with a small local model, because valid JSON does not necessarily mean the model's decision is logically correct.

---

## Project Structure

The main scripts follow a step-by-step learning sequence:

```text
scripts/
├── step_01_*   embeddings
├── step_02_*   cosine similarity
├── step_03_*   PostgreSQL + pgvector
├── step_04_*   chunking
├── step_05_*   document ingestion
├── step_06_*   semantic search
├── step_07_*   RAG
├── step_08_*   Ollama
├── step_09_*   tools
├── step_10_*  agent loop
├── step_11_*  MCP server
└── step_12_*  MCP client and MCP agent
```

Detailed READMEs are available for individual steps and contain the deeper explanations and experiments performed during development.

---

## Environment Setup

Create a Python 3.11 virtual environment:

```bash
python3.11 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Verify:

```bash
python --version
```

Expected:

```text
Python 3.11.x
```

---

## External Services

### PostgreSQL

The project uses PostgreSQL with the pgvector extension enabled.

The database stores document chunks and vector embeddings.

### Ollama

Ollama must be running locally.

The project currently uses:

```text
qwen2.5:3b-instruct
```

---

## Learning Philosophy

This repository focuses on understanding how the underlying components work rather than hiding them behind frameworks.

For example:

```text
Instead of:

SentenceTransformer.encode()

We explored:

tokenization
→ transformer inference
→ CLS pooling
→ normalization
→ embedding
```

And instead of using an agent framework:

```text
LLM
→ JSON tool decision
→ Python validation
→ tool execution
→ history
→ next LLM call
```

was implemented manually.

---

## Current Status

The core learning project is complete through:

```text
Embeddings
→ Vector Search
→ RAG
→ Local LLM
→ Tools
→ Agent
→ MCP Server
→ MCP Client
```

One remaining area for experimentation is improving the mathematical planning reliability of the small local LLM during complex multi-step calculator tasks.

---

## Possible Future Improvements

- Hybrid semantic + keyword search
- Reranking
- RAG evaluation
- conversation memory
- improved agent planning
- structured output enforcement
- LangChain comparison
- LangGraph workflow implementation
- Dockerized setup
- web interface
- additional MCP tools
- multimodal / video RAG