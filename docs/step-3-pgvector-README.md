# Step 3 — PostgreSQL + pgvector

In the previous steps, we learned:

```text
Step 1
Text
 ↓
Embedding
 ↓
384-dimensional vector
```

and:

```text
Step 2
Embedding A
     +
Embedding B
     ↓
Cosine Similarity
     ↓
Similarity Score
```

Until now, all vectors existed only inside our Python application.

In this step, we introduce PostgreSQL + pgvector so that embeddings can be:

- stored permanently
- queried using SQL
- compared using vector distance
- ordered by similarity
- eventually used for semantic search and RAG

---

# 1. Why do we need a vector database?

Suppose we have only three sentences:

```text
"Java is a programming language"

"Java is used for backend development"

"Bananas grow in tropical climates"
```

We can generate embeddings in Python:

```text
Sentence A
   ↓
[384 values]

Sentence B
   ↓
[384 values]

Sentence C
   ↓
[384 values]
```

Then we can compare them using our own:

```python
cosine_similarity()
```

This is fine when we only have a few embeddings.

But imagine we have:

```text
100,000 document chunks
```

Each chunk has:

```text
384 floating-point values
```

When a user asks:

```text
"How does Kafka distribute messages?"
```

we would need to:

```text
Generate question embedding
        ↓
Load stored embeddings
        ↓
Compare question against many vectors
        ↓
Calculate similarity
        ↓
Sort results
        ↓
Return the most similar chunks
```

Instead of implementing all of this storage and searching manually, we can use a vector-capable database.

For this project we use:

```text
PostgreSQL
    +
pgvector
```

---

# 2. What is pgvector?

pgvector is an extension for PostgreSQL.

Regular PostgreSQL understands data types such as:

```text
INTEGER
TEXT
VARCHAR
BOOLEAN
TIMESTAMP
JSONB
```

After enabling pgvector, PostgreSQL also understands vector-related data types such as:

```text
vector
halfvec
sparsevec
```

The main one we currently care about is:

```text
vector
```

This allows us to create columns such as:

```sql
embedding VECTOR(384)
```

which means:

> The `embedding` column stores vectors containing exactly 384 values.

That matches the output of our embedding model:

```text
BAAI/bge-small-en-v1.5
        ↓
384-dimensional embedding
```

---

# 3. What is a PostgreSQL extension?

A PostgreSQL extension is an add-on that adds capabilities to PostgreSQL.

Think of normal PostgreSQL as:

```text
PostgreSQL
│
├── INTEGER
├── TEXT
├── BOOLEAN
├── JSONB
├── TIMESTAMP
└── ...
```

PostgreSQL does not normally provide the vector data type and vector similarity operators that we need.

pgvector adds them.

Conceptually:

```text
PostgreSQL
│
├── INTEGER
├── TEXT
├── BOOLEAN
├── JSONB
│
└── pgvector extension
      │
      ├── vector
      ├── halfvec
      ├── sparsevec
      │
      ├── vector distance operators
      ├── cosine distance
      ├── L2 distance
      ├── inner product
      │
      └── vector indexes
```

An extension can therefore add things such as:

- data types
- functions
- operators
- indexes
- database objects

---

# 4. pgvector installation vs enabling the extension

There are two separate concepts:

```text
1. pgvector installed on the PostgreSQL server

2. pgvector enabled inside a database
```

In our project we used the Docker image:

```text
pgvector/pgvector:pg17
```

This image already contains:

```text
PostgreSQL 17
+
pgvector software
```

So pgvector is already available to the PostgreSQL server.

But it is not automatically enabled inside every database.

For our database:

```text
local_rag_agent
```

we enabled it with:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

The flow is therefore:

```text
Docker image
      ↓
PostgreSQL 17
      ↓
pgvector software available
      ↓
Database: local_rag_agent
      ↓
CREATE EXTENSION vector
      ↓
vector capabilities available inside database
```

---

# 5. Why did we run `CREATE EXTENSION vector`?

We executed:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

because the pgvector software was available on the PostgreSQL server, but its database objects needed to be created inside:

```text
local_rag_agent
```

After executing this command, PostgreSQL understands things such as:

```text
VECTOR(3)

VECTOR(384)
```

and vector operators such as:

```text
<=>
```

for cosine distance.

---

# 6. What does `IF NOT EXISTS` mean?

We used:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

instead of:

```sql
CREATE EXTENSION vector;
```

`IF NOT EXISTS` means:

> Create the extension only if it has not already been created.

So if the extension already exists, PostgreSQL does not fail simply because we ran the setup query again.

This makes setup scripts safer to rerun.

---

# 7. What happens without `CREATE EXTENSION vector`?

Suppose pgvector is available on the server but we have not enabled it inside our database.

If we try:

```sql
CREATE TABLE vector_examples (
    id SERIAL PRIMARY KEY,
    description TEXT NOT NULL,
    embedding VECTOR(3) NOT NULL
);
```

PostgreSQL would not understand:

```text
VECTOR
```

and would produce an error similar to:

```text
ERROR: type "vector" does not exist
```

Conceptually PostgreSQL would be saying:

```text
INTEGER?
I know that.

TEXT?
I know that.

VECTOR?
I don't know what that is.
```

After:

```sql
CREATE EXTENSION vector;
```

PostgreSQL now knows about the `vector` type.

---

# 8. Extensions are enabled per database

Suppose one PostgreSQL server has:

```text
Database A

Database B

Database C
```

and pgvector is installed on the PostgreSQL server.

We enable pgvector inside Database A:

```sql
CREATE EXTENSION vector;
```

That does not automatically mean Database B has it enabled.

Conceptually:

```text
PostgreSQL Server
│
│
├── Database A
│      └── vector extension enabled ✅
│
├── Database B
│      └── vector extension not enabled ❌
│
└── Database C
       └── vector extension not enabled ❌
```

If Database B also requires vectors, we connect to Database B and execute:

```sql
CREATE EXTENSION vector;
```

there as well.

---

# 9. Can pgvector be used with a normal PostgreSQL database?

Yes.

Docker is not required for pgvector.

A normal PostgreSQL installation can use it too, provided pgvector is installed for that PostgreSQL server.

For example:

```text
PostgreSQL 16 installed locally
        ↓
Install pgvector for PostgreSQL 16
        ↓
Connect to database
        ↓
CREATE EXTENSION vector
```

In our case, we chose Docker because we wanted to avoid modifying the existing PostgreSQL 16 installation on the machine.

Our setup is:

```text
Existing PostgreSQL 16
localhost:5432
        ↓
existing local databases
```

and:

```text
Docker PostgreSQL 17 + pgvector
localhost:5434
        ↓
local_rag_agent
```

This keeps the learning project isolated.

---

# 10. Our Docker database setup

Our project database is running inside Docker.

Conceptually:

```text
Mac
│
├── PostgreSQL 16
│      localhost:5432
│
└── Docker
       │
       └── PostgreSQL 17 + pgvector
              localhost:5434
              │
              └── local_rag_agent
```

Docker PostgreSQL itself listens internally on:

```text
5432
```

but we mapped it to:

```text
5434
```

on our Mac.

Conceptually:

```text
Mac localhost:5434
        ↓
Docker port mapping
        ↓
Container port 5432
        ↓
PostgreSQL 17
```

---

# 11. Seeing the extension in DBeaver

After executing:

```sql
CREATE EXTENSION vector;
```

DBeaver can show the enabled extension.

Inside the database tree we can look for:

```text
local_rag_agent
    ↓
Extensions
    ↓
vector
```

If it does not immediately appear, refresh the database connection.

This tells us:

```text
The vector extension is enabled
inside local_rag_agent.
```

---

# 12. Seeing vector data types in DBeaver

After enabling the extension, under:

```text
Schemas
 ↓
public
 ↓
Data types
```

we can see types such as:

```text
vector
halfvec
sparsevec

_vector
_halfvec
_sparsevec
```

The important type for our current project is:

```text
vector
```

That type exists because the pgvector extension was enabled.

Without the extension, the pgvector-specific data types would not exist in the database.

---

# 13. Verify enabled extensions using SQL

We can list extensions enabled in the current database:

```sql
SELECT
    extname,
    extversion
FROM pg_extension;
```

We may see entries such as:

```text
plpgsql
vector
```

To specifically verify pgvector:

```sql
SELECT
    extname,
    extversion
FROM pg_extension
WHERE extname = 'vector';
```

If pgvector is enabled, we get:

```text
vector | <version>
```

---

# 14. Available extension vs installed extension

PostgreSQL can also tell us whether an extension is available on the server.

Run:

```sql
SELECT
    name,
    default_version,
    installed_version
FROM pg_available_extensions
WHERE name = 'vector';
```

Before running:

```sql
CREATE EXTENSION vector;
```

we might conceptually see:

```text
name               vector
default_version    0.x.x
installed_version  NULL
```

Meaning:

```text
pgvector is available on the server
but
not enabled in this database
```

After:

```sql
CREATE EXTENSION vector;
```

we may see:

```text
name               vector
default_version    0.x.x
installed_version  0.x.x
```

Meaning:

```text
pgvector is available
and
enabled in this database
```

---

# 15. Create our first vector table

We started with small vectors instead of immediately using 384 dimensions.

We created:

```sql
CREATE TABLE vector_examples (
    id SERIAL PRIMARY KEY,
    description TEXT NOT NULL,
    embedding VECTOR(3) NOT NULL
);
```

The important part is:

```sql
embedding VECTOR(3)
```

This means:

```text
embedding
    ↓
vector data type
    ↓
exactly 3 dimensions
```

So this is valid:

```text
[4,3,0]
```

because it contains three values.

This would not match a `VECTOR(3)` column:

```text
[4,3]
```

because it only contains two dimensions.

---

# 16. Why did we use `VECTOR(3)` first?

Our actual embedding model produces:

```text
384 dimensions
```

But displaying 384 values while learning the database concepts would make the examples difficult to understand.

So we used:

```text
VECTOR(3)
```

with vectors such as:

```text
Vector A = [4,3,0]

Vector B = [8,6,0]

Vector C = [-3,4,0]
```

These are based on the same simple vectors we used while learning cosine similarity.

Later we will use:

```sql
VECTOR(384)
```

for our real BGE embeddings.

---

# 17. Insert vectors into PostgreSQL

We inserted:

```sql
INSERT INTO vector_examples (
    description,
    embedding
)
VALUES
    ('Vector A', '[4,3,0]'),
    ('Vector B', '[8,6,0]'),
    ('Vector C', '[-3,4,0]');
```

Our table now contains conceptually:

```text
id | description | embedding
---+-------------+-----------
1  | Vector A    | [4,3,0]

2  | Vector B    | [8,6,0]

3  | Vector C    | [-3,4,0]
```

PostgreSQL is not treating these values as normal text.

The `embedding` column is a real:

```text
vector
```

data type.

---

# 18. Vector A, B and C

We intentionally chose:

```text
A = [4,3,0]

B = [8,6,0]

C = [-3,4,0]
```

because:

```text
B = 2 × A
```

Therefore A and B point in exactly the same direction.

Their cosine similarity should be:

```text
1
```

A and C are perpendicular in the first two dimensions:

```text
A = [4,3]

C = [-3,4]
```

Their dot product is:

```text
(4 × -3)
+
(3 × 4)

= -12 + 12

= 0
```

Therefore their cosine similarity should be:

```text
0
```

Adding a third value of `0` does not change this relationship.

---

# 19. Cosine similarity vs cosine distance

In Step 2 we calculated:

```text
cosine similarity
```

where:

```text
1 = same direction / highly similar
```

pgvector provides the operator:

```text
<=>
```

which calculates:

```text
cosine distance
```

For cosine distance:

```text
0 = same direction
```

The relationship is:

```text
cosine_similarity
=
1 - cosine_distance
```

So:

```text
similarity = 1
```

corresponds to:

```text
distance = 0
```

---

# 20. Calculate cosine distance in PostgreSQL

We can compare each stored vector against:

```text
[4,3,0]
```

using:

```sql
SELECT
    description,
    embedding <=> '[4,3,0]' AS cosine_distance
FROM vector_examples;
```

The operator:

```text
<=>
```

means:

```text
cosine distance
```

Conceptually we expect:

```text
Vector A
distance ≈ 0

Vector B
distance ≈ 0

Vector C
distance ≈ 1
```

because A and B point in the same direction as the query vector, while C is perpendicular.

---

# 21. Convert cosine distance to cosine similarity

Because we already learned cosine similarity, we can convert pgvector's distance:

```sql
SELECT
    description,
    1 - (
        embedding <=> '[4,3,0]'
    ) AS cosine_similarity
FROM vector_examples;
```

Conceptually:

```text
Vector A → 1

Vector B → 1

Vector C → 0
```

This is equivalent in concept to our Python implementation:

```python
cosine_similarity(
    vector_a,
    vector_b
)
```

So now we have connected:

```text
Python
    ↓
our cosine_similarity() function
```

with:

```text
PostgreSQL + pgvector
    ↓
1 - (embedding <=> query_vector)
```

---

# 22. Order vectors by similarity

Suppose we want to find the vectors most similar to:

```text
[4,3,0]
```

We can run:

```sql
SELECT
    description,
    1 - (
        embedding <=> '[4,3,0]'
    ) AS cosine_similarity
FROM vector_examples
ORDER BY embedding <=> '[4,3,0]';
```

Notice that we order using:

```sql
embedding <=> '[4,3,0]'
```

which is distance.

Why?

Because:

```text
smaller distance
=
more similar
```

So:

```text
distance 0.01
```

is closer than:

```text
distance 0.70
```

The closest vectors appear first.

---

# 23. This is the beginning of vector search

Our tiny example:

```text
Query vector
    ↓
[4,3,0]
    ↓
compare with stored vectors
    ↓
sort by distance
    ↓
closest vectors first
```

is exactly the basic idea behind vector search.

Later instead of:

```text
[4,3,0]
```

we will have:

```text
User question

"How does Kafka distribute messages?"

        ↓

Embedding model

        ↓

[384-dimensional query vector]
```

And instead of three example vectors, PostgreSQL will contain embeddings of document chunks.

---

# 24. pgvector does not generate embeddings

This is an important distinction.

pgvector does not convert:

```text
"Java is a programming language"
```

into:

```text
[384-dimensional vector]
```

That is the responsibility of our embedding model.

Our architecture is:

```text
Text
 ↓
Python embedding code
 ↓
BGE embedding model
 ↓
384-dimensional vector
 ↓
PostgreSQL + pgvector
 ↓
Store vector
 ↓
Search / compare vectors
```

So:

```text
Embedding model
    =
generate vectors
```

while:

```text
pgvector
    =
store and search vectors
```

---

# 25. Our real embedding table

Our actual model produces:

```text
384 dimensions
```

Therefore the real table can use:

```sql
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL
);
```

Now:

```text
content
```

stores the original text.

For example:

```text
Java is a programming language
```

and:

```text
embedding
```

stores its 384-dimensional representation.

Conceptually:

```text
id
1

content
"Java is a programming language"

embedding
[-0.03528, 0.00294, -0.04936, ..., -0.04297]
```

---

# 26. Why store both text and embedding?

We need the embedding for:

```text
mathematical similarity search
```

but after finding the closest vector, we need the actual text to give to the LLM.

For example:

```text
Question
 ↓
Question embedding
 ↓
Search PostgreSQL
 ↓
Closest embedding found
 ↓
Retrieve associated content
 ↓
Send content to LLM
```

The vector helps us find the row.

The text is the information we actually want to retrieve.

---

# 27. What our RAG table will eventually contain

The table will eventually become more detailed.

Instead of only:

```text
id
content
embedding
```

we may store:

```text
id
document_name
chunk_index
content
embedding
```

Example:

```text
id:
21

document_name:
kafka.md

chunk_index:
4

content:
"Kafka consumer groups allow consumers to divide partitions..."

embedding:
[384 values]
```

This will happen after we learn:

```text
Step 4 — Chunking
```

and:

```text
Step 5 — Ingestion
```

---

# 28. Complete architecture so far

After Step 3, our understanding is:

```text
                         STEP 1
                           │
Text                       │
  │                        │
  ▼                        │
Tokenizer                  │
  │                        │
  ▼                        │
Transformer                │
  │                        │
  ▼                        │
CLS Pooling                │
  │                        │
  ▼                        │
L2 Normalization           │
  │                        │
  ▼                        │
384-dimensional embedding  │
                           │
                           ▼

                         STEP 2
                           │
                   Cosine Similarity
                           │
                           ▼
                    Similarity Score
                           │
                           ▼

                         STEP 3
                           │
                      PostgreSQL
                           +
                       pgvector
                           │
                           ▼
                  Store embeddings
                           │
                           ▼
                  Search embeddings
```

---

# 29. Complete mental model

The simplest mental model for this step is:

```text
pgvector installed
        =
PostgreSQL server has the vector extension software available
```

```text
CREATE EXTENSION vector
        =
enable/create pgvector objects inside the current database
```

```text
VECTOR(384)
        =
column capable of storing one 384-dimensional vector
```

```text
<=>
        =
cosine distance operator
```

```text
1 - cosine_distance
        =
cosine similarity
```

---

# Key Takeaways

## PostgreSQL extension

An extension adds additional capabilities to PostgreSQL.

pgvector adds vector-related capabilities.

---

## pgvector

pgvector allows PostgreSQL to:

- store vectors
- compare vectors
- calculate vector distances
- perform nearest-neighbor searches
- create vector indexes

---

## `CREATE EXTENSION vector`

```sql
CREATE EXTENSION vector;
```

enables pgvector inside the current database.

Without it, PostgreSQL does not know the pgvector `vector` type.

---

## Extensions are database-specific

Enabling:

```sql
CREATE EXTENSION vector;
```

inside one database does not automatically enable it in every database on the server.

---

## `VECTOR(3)`

```sql
embedding VECTOR(3)
```

means:

```text
embedding must contain exactly 3 dimensions
```

---

## `VECTOR(384)`

```sql
embedding VECTOR(384)
```

matches our BGE model because it produces:

```text
384-dimensional embeddings
```

---

## Cosine distance operator

```text
<=>
```

is pgvector's cosine-distance operator.

---

## Distance vs similarity

```text
cosine_similarity
=
1 - cosine_distance
```

---

## Vector search

The basic vector-search flow is:

```text
Query vector
 ↓
Compare against stored vectors
 ↓
Calculate distance
 ↓
Sort by smallest distance
 ↓
Return nearest vectors
```

---

## Embedding model vs vector database

```text
Embedding model
    ↓
creates vectors
```

```text
pgvector
    ↓
stores and searches vectors
```

These are different responsibilities.

---

# Next Step

Before moving fully into **Step 4 — Chunking**, we will connect our Python embedding generator to PostgreSQL.

The flow will become:

```text
"Java is a programming language"
        ↓
Python
        ↓
BGE-small-en-v1.5
        ↓
384-dimensional embedding
        ↓
PostgreSQL
        ↓
VECTOR(384)
```

This will connect Steps 1, 2 and 3 end-to-end.


# Step 3 Addendum — Python + PostgreSQL Vector Search

This section connects our Python embedding code with PostgreSQL + pgvector.

---

## 1. `psycopg[binary]`

```text
psycopg[binary]
```

means:

```text
psycopg
+
optional precompiled binary support
```

The part inside:

```text
[binary]
```

is called an **extra**.

It makes installation easier because native PostgreSQL client components usually do not need to be compiled manually.

---

## 2. What is a database cursor?

A connection represents the connection between Python and PostgreSQL.

```text
Python
  ↓
connection
  ↓
PostgreSQL
```

A cursor is the object used to:

- execute SQL
- fetch query results

Example:

```python
with get_connection() as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM embeddings"
        )

        results = cursor.fetchall()
```

`with` automatically closes the cursor when the block finishes.

---

## 3. Converting Python embeddings to pgvector

Our embedding is a Python list:

```python
[0.12, -0.03, 0.44]
```

We convert it to:

```text
[0.12,-0.03,0.44]
```

using:

```python
def embedding_to_pgvector(embedding):
    return "[" + ",".join(
        str(value)
        for value in embedding
    ) + "]"
```

We do this because we have not installed a dedicated pgvector Python adapter.

PostgreSQL arrays and pgvector vectors are different.

```text
FLOAT[]
    = normal PostgreSQL array

VECTOR
    = pgvector type used for similarity search
```

We use `VECTOR` because it supports operations such as:

```sql
embedding <=> query_vector
```

---

## 4. What does `%s::vector` mean?

`%s` is a Psycopg parameter placeholder.

Example:

```python
cursor.execute(
    "SELECT %s",
    ("hello",)
)
```

In our code:

```sql
%s::vector
```

means:

```text
take the supplied parameter
        ↓
cast it to pgvector VECTOR
```

PostgreSQL casting syntax is:

```sql
value::type
```

Example:

```sql
'123'::INTEGER
```

For vectors:

```sql
'[1,2,3]'::vector
```

We use the explicit cast because the question vector arrives from Python as a string.

---

## 5. Vector distance order

These are equivalent for cosine distance:

```sql
embedding <=> %s::vector
```

and:

```sql
%s::vector <=> embedding
```

Cosine distance is symmetric:

```text
distance(A, B)
=
distance(B, A)
```

We prefer:

```sql
embedding <=> %s::vector
```

because it reads naturally as:

```text
stored embedding
vs
query embedding
```

---

## 6. What does `enumerate(results, start=1)` do?

Suppose:

```python
results = [
    "Java",
    "Python",
    "Go"
]
```

This:

```python
for index, result in enumerate(
    results,
    start=1
):
```

produces:

```text
1, Java
2, Python
3, Go
```

So:

```python
print(f"Match {index}")
```

prints:

```text
Match 1
Match 2
Match 3
```

---

## 7. Our first real semantic search

Question:

```text
which language is used for software development
```

Result:

```text
Match 1
Java is used for software development
Similarity: 0.8226

Match 2
Java is a programming language
Similarity: 0.7429

Match 3
Bananas grow in tropical climates
Similarity: 0.5130
```

This proves that PostgreSQL + pgvector can rank stored text by semantic similarity.

The full flow is:

```text
Question
   ↓
generate_embedding()
   ↓
384-dimensional vector
   ↓
convert to pgvector format
   ↓
PostgreSQL
   ↓
embedding <=> question_vector
   ↓
cosine distance
   ↓
ORDER BY distance
   ↓
nearest semantic matches
```

