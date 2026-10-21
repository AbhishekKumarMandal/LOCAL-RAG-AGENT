# Step 1 — Embeddings

This step introduces the basic concepts required to understand how text is converted into numbers that a computer can compare mathematically.

The main concepts covered are:

- Tokens
- Token IDs
- Transformers
- Embeddings
- Pooling
- Normalization

---

## 1. Why do we need embeddings?

Computers do not understand the meaning of text the same way humans do.

For example:

```text
"The car battery is charging"

"The EV battery is receiving power"

"Java uses garbage collection"
```

A human can immediately understand that the first two sentences are related, while the third sentence is about a different topic.

To allow a computer to compare meaning mathematically, we convert text into a list of numbers called a **vector**.

Example:

```text
"The car battery is charging"

        ↓

[0.82, 0.71, 0.15]
```

Another similar sentence might become:

```text
"The EV battery is receiving power"

        ↓

[0.79, 0.74, 0.18]
```

An unrelated sentence might become:

```text
"Java uses garbage collection"

        ↓

[-0.31, 0.12, 0.91]
```

The first two vectors are more similar to each other than the third vector.

That is the basic idea behind embeddings.

---

# 2. What is a vector?

A vector is simply a list of numbers.

Example:

```text
[0.82, 0.71, 0.15]
```

This vector contains three values, so it is called a:

```text
3-dimensional vector
```

The embedding model we will use later:

```text
BAAI/bge-small-en-v1.5
```

produces:

```text
384-dimensional vectors
```

An actual embedding may look like:

```text
[
  0.0214,
 -0.0371,
  0.0627,
  ...
  0.0192
]
```

There are 384 numbers in the vector.

We normally do not say things like:

```text
dimension 1 = vehicle
dimension 2 = battery
dimension 3 = charging
```

The meaning is distributed across the entire vector.

---

# 3. Why convert text into vectors?

Once text becomes numbers, we can use mathematics to compare two pieces of text.

Suppose we have:

```text
A = "Java is a programming language"

B = "Java is used for software development"

C = "Bananas grow in tropical climates"
```

The embedding model converts them into:

```text
A → vector A

B → vector B

C → vector C
```

Later we can calculate:

```text
similarity(A, B)

similarity(A, C)
```

We expect:

```text
similarity(A, B) → high

similarity(A, C) → low
```

This idea becomes the foundation for:

- Semantic search
- Vector databases
- RAG

---

# 4. How is an embedding generated?

The simplified flow is:

```text
Text
  ↓
Tokenization
  ↓
Token IDs
  ↓
Transformer
  ↓
One vector per token
  ↓
Pooling
  ↓
One vector for the entire text
  ↓
Normalization
  ↓
Final embedding
```

---

# 5. Tokens

Consider:

```text
Java is a programming language
```

Before sending this sentence to a transformer, a tokenizer breaks it into smaller pieces called **tokens**.

Conceptually:

```text
Java
is
a
programming
language
```

However, a token is not always exactly one word.

A tokenizer may split a word into smaller pieces.

For example, conceptually:

```text
programming
```

could become something like:

```text
program
##ming
```

The exact tokenization depends on the tokenizer used by the model.

---

# 6. Token IDs

A transformer does not directly receive words such as:

```text
Java
programming
language
```

The tokenizer has a vocabulary where every token has a numeric identifier.

Conceptually:

```text
Java         → 1994

is           → 2003

a            → 1037

programming  → 4730

language     → 2653
```

The sentence can therefore become something like:

```text
[1994, 2003, 1037, 4730, 2653]
```

These numbers are called:

```text
Token IDs
```

An important distinction is:

```text
Token ID ≠ Embedding
```

For example:

```text
programming → token ID 4730
```

does **not** mean that the embedding of `programming` is `4730`.

`4730` is only an identifier that tells the model which token from its vocabulary is being used.

A useful analogy is:

```text
Employee ID = 1234
```

The number `1234` identifies the employee.

It does not describe the employee's skills, personality, experience, etc.

A token ID works similarly.

---

# 7. Special tokens

When we tokenize:

```text
Java is a programming language
```

the model may actually receive something similar to:

```text
[CLS]
Java
is
a
programming
language
[SEP]
```

The tokenizer may therefore return token IDs such as:

```text
[101, ..., ..., ..., ..., 102]
```

Here, IDs such as `101` and `102` may represent special tokens.

Conceptually:

```text
101 → [CLS]

102 → [SEP]
```

These are special tokens used by some transformer models for internal processing.

---

# 8. Transformer

After tokenization we have token IDs.

Example:

```text
[1994, 2003, 1037, 4730, 2653]
```

These token IDs are passed into the transformer.

```text
Token IDs
    ↓
Transformer
    ↓
Context-aware vectors
```

The transformer produces a vector for each token.

For learning purposes, imagine that each token produces only three values:

```text
Java         → [0.4, 0.1, 0.7]

is           → [0.2, 0.3, 0.1]

a            → [0.1, 0.1, 0.2]

programming  → [0.8, 0.6, 0.5]

language     → [0.7, 0.5, 0.6]
```

Real transformer models produce much larger vectors.

The important idea is:

```text
Token ID
    ↓
Transformer
    ↓
Vector representation
```

---

# 9. Embeddings

An embedding is a numerical vector that represents information about the meaning of some text.

Example:

```text
"The car battery is charging"

        ↓

Embedding model

        ↓

[0.82, 0.71, 0.15]
```

In our real project, the final vector will contain:

```text
384 values
```

instead of only three.

The goal is that semantically similar text should produce vectors that are close to each other in vector space.

---

# 10. Why do we need pooling?

After the transformer runs, we may have one vector for every token.

For example:

```text
Java         → [0.4, 0.1, 0.7]

is           → [0.2, 0.3, 0.1]

programming  → [0.8, 0.6, 0.5]
```

But we usually want one embedding representing the complete sentence:

```text
"Java is a programming language"
```

So we need to combine the token vectors into one vector.

This process is called:

```text
Pooling
```

---

# 11. Mean pooling

One simple pooling technique is **mean pooling**.

Suppose we have:

```text
Java         → [0.4, 0.1, 0.7]

is           → [0.2, 0.3, 0.1]

programming  → [0.8, 0.6, 0.5]
```

We calculate the average value for each dimension.

### Dimension 1

```text
(0.4 + 0.2 + 0.8) / 3
= 0.466...
```

### Dimension 2

```text
(0.1 + 0.3 + 0.6) / 3
= 0.333...
```

### Dimension 3

```text
(0.7 + 0.1 + 0.5) / 3
= 0.433...
```

The resulting sentence vector is approximately:

```text
[0.466, 0.333, 0.433]
```

So:

```text
Multiple token vectors
        ↓
Mean pooling
        ↓
One sentence vector
```

Later in the project, we will implement this logic ourselves instead of calling a high-level embedding helper such as:

```python
model.encode(text)
```

---

# 12. Normalization

After creating the final vector, embeddings are often normalized.

Normalization means:

> Keep the same direction of the vector but resize it so that its length becomes 1.

Consider:

```text
[4, 3]
```

The length of this vector is:

```text
sqrt(4² + 3²)

= sqrt(16 + 9)

= sqrt(25)

= 5
```

To normalize the vector, divide every value by its length:

```text
[4/5, 3/5]

=

[0.8, 0.6]
```

Now calculate the new length:

```text
sqrt(0.8² + 0.6²)

= sqrt(0.64 + 0.36)

= sqrt(1)

= 1
```

Therefore:

```text
Before normalization:

[4, 3]

length = 5
```

```text
After normalization:

[0.8, 0.6]

length = 1
```

The direction remains the same.

---

# 13. Why is normalization useful?

Consider:

```text
A = [4, 3]

B = [8, 6]
```

Vector B is exactly twice as large as vector A:

```text
B = 2 × A
```

Their lengths are:

```text
length(A) = 5

length(B) = 10
```

But both point in exactly the same direction.

After normalization:

```text
A → [0.8, 0.6]

B → [0.8, 0.6]
```

This makes it easier to compare direction rather than raw magnitude.

For embeddings, we are usually interested in questions like:

```text
Are these two pieces of text pointing in a similar semantic direction?
```

rather than:

```text
Which embedding contains larger numbers?
```

---

# 14. Normalization with many dimensions

The same normalization formula works regardless of how many dimensions a vector has.

For a 2-dimensional vector:

```text
[x1, x2]
```

the length is:

```text
sqrt(x1² + x2²)
```

For a 4-dimensional vector:

```text
[x1, x2, x3, x4]
```

the length is:

```text
sqrt(x1² + x2² + x3² + x4²)
```

For our 384-dimensional embedding:

```text
[x1, x2, x3, ..., x384]
```

the length is:

```text
sqrt(
    x1² +
    x2² +
    x3² +
    ...
    x384²
)
```

Then every element is divided by the same length:

```text
[
    x1 / length,
    x2 / length,
    x3 / length,
    ...
    x384 / length
]
```

The result is still a 384-dimensional vector, but its total length becomes `1`.

---

# 15. Four-dimensional normalization example

Consider:

```text
[1, 2, 2, 4]
```

Its length is:

```text
sqrt(
    1² +
    2² +
    2² +
    4²
)

= sqrt(1 + 4 + 4 + 16)

= sqrt(25)

= 5
```

Normalize every value:

```text
[
    1/5,
    2/5,
    2/5,
    4/5
]
```

Result:

```text
[0.2, 0.4, 0.4, 0.8]
```

Check the length:

```text
sqrt(
    0.2² +
    0.4² +
    0.4² +
    0.8²
)

= sqrt(
    0.04 +
    0.16 +
    0.16 +
    0.64
)

= sqrt(1)

= 1
```

So the same idea works for:

```text
2 dimensions

3 dimensions

384 dimensions

1536 dimensions

or more
```

---

# 16. Complete embedding flow learned in Step 1

The complete mental model for this step is:

```text
"Java is a programming language"

            ↓

        Tokenizer

            ↓

Tokens

[CLS]
Java
is
a
programming
language
[SEP]

            ↓

Token IDs

[101, ..., ..., ..., ..., 102]

            ↓

       Transformer

            ↓

One vector for every token

            ↓

       Mean Pooling

            ↓

One 384-dimensional sentence vector

            ↓

       L2 Normalization

            ↓

Final normalized embedding
```

---

# 17. First tokenizer experiment

The first script used in this step is:

```python
from transformers import AutoTokenizer


MODEL_NAME = "BAAI/bge-small-en-v1.5"


tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


text = "Java is a programming language"


tokens = tokenizer.tokenize(text)

token_ids = tokenizer.encode(text)


print("Original text:")
print(text)

print("\nTokens:")
print(tokens)

print("\nToken IDs:")
print(token_ids)
```

Run it with:

```bash
python scripts/embedding_basics.py
```

The important output to inspect is:

```text
Original text
    ↓
Tokens
    ↓
Token IDs
```

At this point, remember:

```text
Tokens
≠
Token IDs
≠
Embeddings
```

They are three different things.

---

# Key Takeaways

### Token

A small piece of text understood by the tokenizer.

```text
"Java is programming"

↓

["java", "is", "programming"]
```

### Token ID

A numeric identifier for a token in the tokenizer's vocabulary.

```text
"java" → 1994
```

It is only an ID, not an embedding.

### Transformer

Takes token IDs and produces context-aware numerical representations for the tokens.

### Embedding

A vector representing the semantic meaning of text.

```text
"text"

↓

[0.021, -0.037, ..., 0.019]
```

### Pooling

Combines multiple token vectors into one vector representing the complete text.

### Normalization

Rescales a vector so its length becomes `1` while keeping the same direction.

```text
Take this vector:

[4, 3]

You can imagine it as an arrow starting from (0,0) and ending at (4,3).

Its length is:

√(4² + 3²)
= √(16 + 9)
= √25
= 5

So:

vector = [4, 3]
length = 5

Normalization means: divide every value in the vector by its length.

[4/5, 3/5]

= [0.8, 0.6]

Now calculate the length of the new vector:

√(0.8² + 0.6²)

= √(0.64 + 0.36)

= √1

= 1

So:

Before normalization:

[4, 3]
length = 5


After normalization:

[0.8, 0.6]
length = 1

The important part is that the direction hasn't changed.

Think of two arrows:

              ● (4,3)
             /
            /
           /
          ● (0.8,0.6)
         /
        /
       ●
     (0,0)

Both point in exactly the same direction. One arrow is simply longer.

So normalization is basically:

"Keep the direction of this vector, but resize it so its length becomes exactly 1."

Why do we do this for embeddings? Suppose we have:

A = [4, 3]
B = [8, 6]

These vectors point in exactly the same direction, but:

length(A) = 5
length(B) = 10

The second vector is twice as large:

B = 2 × A

But semantically, if direction is what represents meaning, we don't want that size difference to affect our comparison.

After normalization:

A → [0.8, 0.6]
B → [0.8, 0.6]

Now it's obvious mathematically that they have the same direction.

This becomes very useful with embeddings because we're mostly interested in:

"Are these two pieces of text pointing in a similar semantic direction?"

rather than:

"Which embedding has bigger numbers?"
```

---

# Next Step

**Step 2 — Cosine Similarity**

We will learn how to mathematically compare two embeddings and determine whether two pieces of text are semantically similar.
