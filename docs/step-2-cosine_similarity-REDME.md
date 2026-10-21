# Step 2 — Cosine Similarity

In Step 1, we learned how text is converted into embeddings.

Example:

```text
"Java is a programming language"

        ↓

384-dimensional embedding
```

Now we need a way to compare two embeddings and determine how similar they are.

That is where **cosine similarity** is used.

---

# 1. Why do we need cosine similarity?

Suppose we have:

```text
A = "Java is a programming language"

B = "Java is used for software development"

C = "Bananas grow in tropical climates"
```

Each sentence is converted into an embedding:

```text
A → embedding A
B → embedding B
C → embedding C
```

Now we want to answer:

```text
How similar is A to B?

How similar is A to C?
```

We expect:

```text
A and B → more similar

A and C → less similar
```

Cosine similarity gives us a mathematical way to measure this.

---

# 2. Think of vectors as arrows

Suppose we have a simple 2-dimensional vector:

```text
A = [4, 3]
```

You can imagine it as an arrow pointing from:

```text
(0,0)
```

to:

```text
(4,3)
```

Now consider:

```text
B = [8, 6]
```

B is longer than A, but it points in exactly the same direction.

```text
A = [4,3]

B = [8,6]
```

Since:

```text
B = 2 × A
```

both vectors point in the same direction.

Cosine similarity focuses mainly on this direction.

---

# 3. Cosine similarity and angle

Cosine similarity measures the angle between two vectors.

## Same direction

If two vectors point in the same direction:

```text
angle = 0°
```

then:

```text
cosine similarity = 1
```

This means:

```text
highly similar direction
```

---

## Perpendicular

If two vectors are at 90°:

```text
angle = 90°
```

then:

```text
cosine similarity = 0
```

This means:

```text
not directionally similar
```

---

## Opposite direction

If two vectors point in opposite directions:

```text
angle = 180°
```

then:

```text
cosine similarity = -1
```

So the theoretical range is:

```text
1   → same direction

0   → perpendicular

-1  → opposite direction
```

For text embeddings, values usually fall somewhere between these extremes.

---

# 4. Cosine similarity formula

For two vectors:

```text
A
B
```

the cosine similarity formula is:

```text
                A · B
cosine(A,B) = -----------
               |A| |B|
```

There are three important parts:

```text
A · B
```

Dot product.

```text
|A|
```

Length of vector A.

```text
|B|
```

Length of vector B.

---

# 5. Dot product

Suppose:

```text
A = [4, 3]

B = [8, 6]
```

The dot product is:

```text
A · B

= (4 × 8) + (3 × 6)

= 32 + 18

= 50
```

For:

```text
A = [a1, a2]

B = [b1, b2]
```

the dot product is:

```text
(a1 × b1)
+
(a2 × b2)
```

For 3 dimensions:

```text
A = [1, 2, 3]

B = [4, 5, 6]
```

the dot product is:

```text
(1 × 4)
+
(2 × 5)
+
(3 × 6)

= 4 + 10 + 18

= 32
```

For a 384-dimensional embedding:

```text
A = [a1, a2, ..., a384]

B = [b1, b2, ..., b384]
```

the same rule applies:

```text
(a1 × b1)
+
(a2 × b2)
+
...
+
(a384 × b384)
```

---

# 6. Vector length

We already learned vector length during normalization.

For:

```text
A = [4, 3]
```

length is:

```text
|A|

= sqrt(4² + 3²)

= sqrt(16 + 9)

= sqrt(25)

= 5
```

For:

```text
B = [8, 6]
```

length is:

```text
|B|

= sqrt(8² + 6²)

= sqrt(64 + 36)

= sqrt(100)

= 10
```

---

# 7. Calculate cosine similarity

For:

```text
A = [4,3]

B = [8,6]
```

we have:

```text
A · B = 50

|A| = 5

|B| = 10
```

Now:

```text
                50
cosine(A,B) = --------
               5 × 10
```

So:

```text
cosine(A,B)

= 50 / 50

= 1
```

This makes sense because A and B point in exactly the same direction.

---

# 8. Example with unrelated directions

Consider:

```text
A = [4,3]

C = [-3,4]
```

Dot product:

```text
(4 × -3)
+
(3 × 4)

= -12 + 12

= 0
```

Vector lengths:

```text
|A| = 5

|C| = 5
```

Therefore:

```text
cosine(A,C)

= 0 / (5 × 5)

= 0
```

So:

```text
similarity = 0
```

These two vectors are perpendicular.

---

# 9. Why normalization helps

Consider:

```text
A = [4,3]

B = [8,6]
```

Normalize both:

```text
A → [0.8, 0.6]

B → [0.8, 0.6]
```

Now both vectors have length:

```text
1
```

The cosine similarity formula:

```text
                A · B
cosine(A,B) = -----------
               |A| |B|
```

becomes:

```text
                A · B
cosine(A,B) = -----------
                 1 × 1
```

So:

```text
cosine(A,B) = A · B
```

Therefore, for normalized vectors:

```text
dot product = cosine similarity
```

This is one reason normalized embeddings are convenient.

---

# 10. Implement cosine similarity manually

We implemented the calculation ourselves instead of using a built-in similarity library.

```python
import math


def vector_length(vector):
    squared_sum = 0

    for value in vector:
        squared_sum += value * value

    return math.sqrt(squared_sum)


def dot_product(vector_a, vector_b):

    if len(vector_a) != len(vector_b):
        raise ValueError(
            "Vectors must have the same dimensions"
        )

    result = 0

    for a, b in zip(vector_a, vector_b):
        result += a * b

    return result


def cosine_similarity(vector_a, vector_b):

    dot = dot_product(
        vector_a,
        vector_b
    )

    length_a = vector_length(
        vector_a
    )

    length_b = vector_length(
        vector_b
    )

    if length_a == 0 or length_b == 0:
        raise ValueError(
            "Cosine similarity cannot be calculated for a zero vector"
        )

    return dot / (
        length_a * length_b
    )
```

---

# 11. What does `zip()` do?

Suppose:

```python
vector_a = [4, 3]

vector_b = [8, 6]
```

Then:

```python
zip(vector_a, vector_b)
```

conceptually produces:

```text
(4, 8)

(3, 6)
```

So this loop:

```python
for a, b in zip(vector_a, vector_b):
```

runs like:

```text
First iteration:

a = 4
b = 8
```

Then:

```text
Second iteration:

a = 3
b = 6
```

This allows us to calculate:

```text
(4 × 8)
+
(3 × 6)
```

---

# 12. Vectors must have the same dimensions

This is valid:

```text
A = [1,2,3]

B = [4,5,6]
```

because both have:

```text
3 dimensions
```

This is invalid:

```text
A = [1,2,3]

B = [4,5]
```

because their dimensions differ.

For our embedding model:

```text
BAAI/bge-small-en-v1.5
```

every embedding has:

```text
384 dimensions
```

Therefore:

```text
384-dimensional embedding
```

must be compared with another:

```text
384-dimensional embedding
```

---

# 13. Zero vector edge case

Consider:

```text
[0,0]
```

Its length is:

```text
sqrt(
    0² +
    0²
)

= 0
```

Cosine similarity would require:

```text
dot_product
----------------
0 × other_length
```

which causes division by zero.

So cosine similarity cannot be calculated for a zero vector.

That is why our implementation checks:

```python
if length_a == 0 or length_b == 0:
    raise ValueError(
        "Cosine similarity cannot be calculated for a zero vector"
    )
```

---

# 14. Generate real embeddings

After understanding the mathematics, we connected cosine similarity with real embeddings generated using:

```text
BAAI/bge-small-en-v1.5
```

We tested:

```text
A =
"Java is a programming language"

B =
"Java is used for software development"

C =
"Bananas grow in tropical climates"
```

The model generated:

```text
384-dimensional embeddings
```

for all three sentences.

---

# 15. Real embedding pipeline

The embedding-generation flow is:

```text
Text
 ↓
Tokenizer
 ↓
Tokens
 ↓
Token IDs
 ↓
Transformer
 ↓
Context-aware token vectors
 ↓
CLS Pooling
 ↓
384-dimensional CLS vector
 ↓
L2 Normalization
 ↓
Final normalized embedding
```

---

# 16. Tokenizer output

For:

```text
Java is a programming language
```

the tokenizer produced:

```text
[CLS]
java
is
a
programming
language
[SEP]
```

with token IDs:

```text
[CLS]        → 101

java         → 9262

is           → 2003

a            → 1037

programming  → 4730

language     → 2653

[SEP]        → 102
```

So:

```text
input_ids =
[101, 9262, 2003, 1037, 4730, 2653, 102]
```

---

# 17. `input_ids`

`input_ids` answer this question:

```text
Which tokens are present?
```

Example:

```text
[CLS] → 101
java  → 9262
...
```

These IDs identify tokens in the tokenizer vocabulary.

They are not embeddings.

---

# 18. `attention_mask`

The tokenizer also produced:

```text
attention_mask =
[1,1,1,1,1,1,1]
```

The attention mask tells the Transformer:

```text
Which positions contain real tokens?
```

Typically:

```text
1 = real token

0 = padding
```

Example with padding:

```text
[CLS] Python [SEP] [PAD] [PAD]
```

could have:

```text
attention_mask =
[1, 1, 1, 0, 0]
```

This tells the model not to treat the padding positions as meaningful input.

---

# 19. `token_type_ids`

The tokenizer also produced:

```text
token_type_ids =
[0,0,0,0,0,0,0]
```

BERT-style models can process two text segments together.

Example:

```text
Sentence A:
Java is a language

Sentence B:
Spring Boot uses Java
```

Conceptually:

```text
[CLS]
Java
is
a
language
[SEP]
Spring
Boot
uses
Java
[SEP]
```

The first segment may receive:

```text
token_type_id = 0
```

and the second segment:

```text
token_type_id = 1
```

For our project, we are embedding one text at a time, so everything belongs to the same segment:

```text
[0,0,0,0,0,0,0]
```

---

# 20. Transformer output shape

For:

```text
Java is a programming language
```

there were:

```text
7 tokens
```

The model produces a 384-dimensional vector for every token.

Therefore:

```text
token_embeddings shape:

[1, 7, 384]
```

Meaning:

```text
1
=
one sentence / batch size
```

```text
7
=
seven tokens
```

```text
384
=
384 values for each token
```

Conceptually:

```text
[CLS]        → [384 values]

java         → [384 values]

is           → [384 values]

a            → [384 values]

programming  → [384 values]

language     → [384 values]

[SEP]        → [384 values]
```

---

# 21. CLS pooling

We used:

```python
cls_embedding = token_embeddings[:, 0, :]
```

The tensor has three dimensions:

```text
[
    batch,
    token,
    embedding dimension
]
```

Therefore:

```text
[:, 0, :]
```

means:

```text
First :

all sentences in the batch
```

```text
0

select token at index 0
```

Token index 0 is:

```text
[CLS]
```

```text
Last :

select all 384 values
```

So:

```python
token_embeddings[:, 0, :]
```

means:

> For every sentence, take the transformed `[CLS]` token and all 384 values of its vector.

Before CLS pooling:

```text
[1, 7, 384]
```

After CLS pooling:

```text
[1, 384]
```

---

# 22. What is CLS pooling?

CLS pooling does not average all token vectors.

Instead:

```text
Transformer output

[CLS]        → vector ← SELECT THIS

java         → vector

is           → vector

a            → vector

programming  → vector

language     → vector

[SEP]        → vector
```

The transformed `[CLS]` token is used as the sentence representation.

This is the pooling strategy used by our BGE model.

---

# 23. L2 normalization of the CLS embedding

The CLS vector before normalization had length:

```text
9.220683...
```

After L2 normalization:

```text
length = 1.0
```

Example from our actual output:

Before:

```text
[-0.32533,
  0.02716,
 -0.45516,
 ...]
```

After normalization:

```text
[-0.03528,
  0.00294,
 -0.04936,
 ...]
```

The direction remains the same.

Only the vector magnitude changes.

---

# 24. Our actual similarity results

We compared:

```text
A =
"Java is a programming language"
```

with:

```text
B =
"Java is used for software development"
```

and got approximately:

```text
0.9166
```

Then we compared:

```text
A =
"Java is a programming language"
```

with:

```text
C =
"Bananas grow in tropical climates"
```

and got approximately:

```text
0.4869
```

Therefore:

```text
similarity(A,B)
>
similarity(A,C)
```

which is exactly what we expected.

---

# 25. Important: cosine similarity is not a percentage

A similarity value such as:

```text
0.4869
```

does not mean:

```text
48.69% similar
```

Cosine similarity is a geometric score based on vector direction.

It is not a probability or percentage.

---

# 26. Why this matters for RAG

Later, we may have document chunks such as:

```text
Chunk 1:
"Kafka consumer groups divide partitions between consumers."

Chunk 2:
"Spring Boot provides dependency injection."

Chunk 3:
"Kafka consumer groups distribute message processing."
```

Each chunk will have an embedding.

The user might ask:

```text
"How does Kafka distribute messages between consumers?"
```

We generate an embedding for the question:

```text
Question
   ↓
384-dimensional embedding
```

Then compare it with all stored chunk embeddings:

```text
Question vs Chunk 1 → 0.89

Question vs Chunk 2 → 0.31

Question vs Chunk 3 → 0.92
```

We then retrieve:

```text
Chunk 3

Chunk 1
```

because they have the highest similarity.

This becomes the foundation of:

```text
Semantic Search
```

and later:

```text
RAG
```

---

# 27. Final mental model

At the end of Step 2, the complete flow is:

```text
Sentence A
   ↓
Embedding A
   ↓
            \
             \
              → Cosine Similarity → score
             /
            /
Sentence B
   ↓
Embedding B
```

For real text:

```text
Text
 ↓
Tokenizer
 ↓
Transformer
 ↓
CLS Pooling
 ↓
L2 Normalization
 ↓
384-dimensional embedding
 ↓
Cosine Similarity
 ↓
Semantic similarity score
```

---

# Key Takeaways

## Cosine similarity

Measures how closely two vectors point in the same direction.

```text
1   → same direction

0   → perpendicular

-1  → opposite direction
```

---

## Dot product

For:

```text
A = [a1, a2]

B = [b1, b2]
```

dot product is:

```text
(a1 × b1)
+
(a2 × b2)
```

---

## Normalized embeddings

If both vectors have length:

```text
1
```

then:

```text
cosine similarity
=
dot product
```

---

## Real embedding output

Our BGE model produces:

```text
384-dimensional embeddings
```

---

## Transformer output

For 7 tokens:

```text
[1, 7, 384]
```

means:

```text
1 sentence
7 tokens
384 values per token
```

---

## CLS pooling

```python
token_embeddings[:, 0, :]
```

means:

```text
all sentences
+
token 0 ([CLS])
+
all 384 dimensions
```

---

## L2 normalization

Rescales the final vector so:

```text
vector length = 1
```

without changing its direction.

---

# Next Step

**Step 3 — PostgreSQL + pgvector**

We will learn:

- What a vector database is
- How PostgreSQL stores vectors
- What pgvector adds to PostgreSQL
- How to create a `VECTOR` column
- How to store embeddings
- Cosine distance vs cosine similarity
- How PostgreSQL can perform vector search
