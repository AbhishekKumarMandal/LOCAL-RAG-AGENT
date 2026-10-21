# Step 8 — Ollama and Local LLMs

## 1. What is Ollama?

Ollama is **not an LLM**.

Ollama is an application/runtime used to:

- download models
- manage local models
- load models into memory
- run inference
- expose a local API

Think of it as:

```text
Ollama
    = model runtime / model manager
```

The actual LLM is something like:

```text
qwen2.5:3b-instruct
```

So:

```text
Ollama
    ↓
runs
    ↓
Qwen2.5:3b-instruct
```

---

## 2. Ollama vs Qwen

A useful analogy is Docker:

```text
Docker
    = runs containers

PostgreSQL image
    = actual software running in Docker
```

Similarly:

```text
Ollama
    = runs language models

qwen2.5:3b-instruct
    = actual language model
```

In our project:

```text
BAAI/bge-small-en-v1.5
    = embedding model

PostgreSQL + pgvector
    = vector storage and retrieval

Ollama
    = local model runtime

qwen2.5:3b-instruct
    = generative LLM
```

---

## 3. What does `3B` mean?

In:

```text
qwen2.5:3b
```

`3B` means approximately:

```text
3 billion learned parameters
```

It does **not** mean:

```text
3 billion pieces of training data
```

A parameter is a learned numerical value inside the neural network.

For example, a tiny mathematical model could be:

```text
output =
(input1 × w1)
+
(input2 × w2)
+
bias
```

If:

```text
w1 = 0.7
w2 = -0.2
bias = 0.1
```

then this tiny model has three learned parameters.

A 3B model contains roughly:

```text
3,000,000,000 learned parameters
```

Most of these are neural-network weights.

Training data is used to adjust these parameters.

---

## 4. Parameters vs training data

The relationship is:

```text
Training data
      ↓
Training algorithm
      ↓
Adjust model parameters
      ↓
Trained model
```

So:

```text
3B parameters
```

and:

```text
number of training tokens
```

are completely different measurements.

A 3B model may be trained using far more than 3 billion training tokens.

---

## 5. Parameters are not function arguments

In normal programming:

```python
def add(a, b):
    ...
```

`a` and `b` are function parameters.

Model parameters are different.

A simplified LLM can be represented as:

```text
output = f(input; θ)
```

Where:

```text
input
    = user's prompt

θ
    = billions of learned model parameters
```

The user does not pass those billions of numbers.

They are already stored inside the trained model.

---

## 6. Model weights

The words:

```text
parameters
weights
```

are often used almost interchangeably in simple explanations.

A precise statement is:

> A 3B model has roughly 3 billion learned parameters, most of which are neural-network weights.

This connects to the message:

```text
Loading weights...
```

When a model starts, its learned numerical parameters are loaded into memory so inference can run.

---

## 7. Running Ollama locally

Our Ollama installation reports:

```text
ollama version 0.34.4
```

Ollama runs a local HTTP service, typically at:

```text
http://localhost:11434
```

For text generation we use:

```text
POST /api/generate
```

The flow is:

```text
Python
   ↓
HTTP POST
   ↓
localhost:11434
   ↓
Ollama
   ↓
Qwen2.5:3b-instruct
   ↓
Generated response
```

---

## 8. Calling Ollama from Python

We deliberately used Python's built-in HTTP tools instead of a high-level Ollama SDK.

The important components are:

```python
json.dumps(...)
request.Request(...)
request.urlopen(...)
json.loads(...)
```

This lets us see the actual API interaction.

A high-level SDK might hide those details behind something like:

```python
ollama.generate(...)
```

We used direct HTTP first so we could understand what happens underneath.

---

## 9. Request payload

The basic request sent to Ollama looks like:

```python
payload = {
    "model": "qwen2.5:3b-instruct",
    "prompt": prompt,
    "stream": False
}
```

### `model`

Specifies which local LLM should generate the answer.

```text
qwen2.5:3b-instruct
```

### `prompt`

The text sent to the language model.

### `stream=False`

Tells Ollama:

> Wait until generation is complete and return the result in one response.

With streaming enabled, Ollama can send generated tokens incrementally.

---

## 10. Why did the HTTP response start with `b'...'`?

When we printed:

```python
response_body
```

we saw:

```text
b'{"model":"qwen2.5:3b-instruct", ...}'
```

The prefix:

```text
b
```

means the value is a Python `bytes` object.

HTTP response bodies arrive as bytes.

We therefore convert:

```text
bytes
  ↓
UTF-8 decode
  ↓
string
  ↓
JSON parse
  ↓
Python dictionary
```

Using:

```python
response_body.decode("utf-8")
```

followed by:

```python
json.loads(...)
```

---

## 11. Important Ollama response fields

Our response contained fields such as:

```text
model
created_at
response
done
done_reason
context
total_duration
load_duration
prompt_eval_count
eval_count
```

### `model`

Example:

```text
qwen2.5:3b-instruct
```

The model that generated the answer.

### `response`

The generated text.

This is the main field we use:

```python
response_json["response"]
```

### `done`

```text
true
```

means generation has completed.

### `done_reason`

Example:

```text
stop
```

means the model stopped normally because it reached a stop condition.

---

## 12. Timing information

Ollama returns durations in nanoseconds.

For example:

```text
total_duration = 2515257333
```

is approximately:

```text
2.52 seconds
```

### `load_duration`

Time spent loading or preparing the model.

### `prompt_eval_duration`

Time spent processing input tokens.

### `eval_duration`

Time spent generating output tokens.

These metrics are useful for performance testing.

---

## 13. Prompt tokens vs generated tokens

Our response contained:

```text
prompt_eval_count = 37
eval_count = 27
```

Meaning approximately:

```text
37 input-side tokens processed
27 output tokens generated
```

The model first processes the prompt and then generates output tokens.

---

## 14. What is the `context` array?

The Ollama response included:

```text
context:
[
    151644,
    8948,
    198,
    ...
]
```

These are token IDs representing the accumulated model context.

They can include:

```text
system message tokens
+
user message tokens
+
special chat-template tokens
+
generated assistant tokens
```

The context array is therefore not simply the user's visible prompt.

---

## 15. Decoding Qwen context tokens

We used:

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(
    "Qwen/Qwen2.5-3B-Instruct"
)
```

Then:

```python
tokens = tokenizer.convert_ids_to_tokens(context)
```

This showed the structure clearly.

Example:

```text
0  <|im_start|>
1  system
...
19 <|im_end|>

21 <|im_start|>
22 user
...
32 <|im_end|>

34 <|im_start|>
35 assistant
36 newline

37 K
38 afka
...
```

This revealed:

```text
0–36
    = input / prompt-side context

37 onward
    = generated assistant response
```

This matched:

```text
prompt_eval_count = 37
```

---

## 16. Qwen chat-template tokens

We observed:

```text
<|im_start|>
<|im_end|>
```

These are special tokens used to mark message boundaries.

Conceptually:

```text
<|im_start|>
system
...
<|im_end|>

<|im_start|>
user
...
<|im_end|>

<|im_start|>
assistant
...
```

They help the model distinguish system, user, and assistant messages.

---

## 17. What do `Ġ` and `Ċ` mean?

When inspecting Qwen's tokenizer output, we saw tokens such as:

```text
Ġis
Ġa
Ġhigh
```

The `Ġ` typically represents a preceding space.

For example:

```text
Ġis
```

roughly corresponds to:

```text
" is"
```

We also saw:

```text
Ċ
```

which represents a newline.

These are tokenizer representations and are not literal characters from the user's sentence.

---

## 18. Why did Hugging Face appear?

We used:

```python
from transformers import AutoTokenizer
```

and:

```python
AutoTokenizer.from_pretrained(
    "Qwen/Qwen2.5-3B-Instruct"
)
```

`Qwen/Qwen2.5-3B-Instruct` is a repository identifier on the Hugging Face Hub.

That does not mean Hugging Face created Qwen.

Think:

```text
Alibaba Cloud
    = creator of Qwen

Hugging Face Hub
    = hosts model/tokenizer files
```

This is similar to:

```text
Company
    = owns source code

GitHub
    = hosts repository
```

---

## 19. Why were tokenizer files downloaded even though Ollama already had Qwen?

Ollama and Hugging Face use separate caches/storage.

Ollama already had the model needed to run Qwen.

But our Transformers debugging script needed Qwen's tokenizer files.

It downloaded files such as:

```text
config.json
tokenizer_config.json
vocab.json
merges.txt
tokenizer.json
```

These are tokenizer/configuration files.

It did not download the complete 3B model weights for that debugging script.

---

## 20. Token IDs are model/tokenizer specific

Suppose:

```text
BGE tokenizer:
"java" → token ID 9262
```

Qwen may use:

```text
Qwen tokenizer:
"java" → another token ID
```

Token IDs do not have universal meaning.

They only make sense together with the tokenizer vocabulary that created them.

A good analogy:

```text
Company A:
employee 123 = Alice

Company B:
employee 123 = Bob
```

Therefore:

```text
BGE token IDs
    → decode using BGE tokenizer

Qwen token IDs
    → decode using Qwen tokenizer
```

---

## 21. Is tokenization deterministic?

Yes, for the same tokenizer/version and exactly the same input text.

However:

```text
Kafka
 kafka
KAFKA
Kafka.
```

may tokenize differently because:

- spaces matter
- punctuation matters
- capitalization can matter
- surrounding text can affect segmentation

The safe rule is:

> The same tokenizer given exactly the same text produces the same tokenization.

---

## 22. Can one tokenizer decode another model's token IDs?

Generally, no.

Token ID:

```text
9262
```

may mean completely different things in different vocabularies.

Some models intentionally share a tokenizer, but we should never assume token compatibility unless we know they do.

---

## 23. Can embeddings be decoded back into original text?

No.

Tokenization is approximately reversible:

```text
Text
   ↓
Token IDs
   ↓
decode()
   ↓
Text
```

Embeddings are different:

```text
Text
   ↓
Neural network
   ↓
Semantic vector
```

An embedding is a lossy semantic representation.

For example:

```text
"Java is used for backend development"

        ↓

[-0.035, 0.002, ..., 384 values]
```

There is no normal operation such as:

```text
decode_embedding(...)
```

that returns the original sentence.

This is why our database stores both:

```sql
content TEXT
embedding VECTOR(384)
```

The vector helps us find the row.

The `content` column gives us the original text.

---

## 24. Temperature

We added:

```python
"options": {
    "temperature": temperature
}
```

Temperature controls how much variation/randomness the model uses while choosing output tokens.

Conceptually:

```text
temperature = 0.0
    → highly deterministic

temperature = 0.2
    → focused, small variation

temperature = 0.8
    → more creative and varied
```

For RAG, we generally prefer a lower temperature because the goal is to stay close to retrieved context rather than generate creative answers.

Example:

```python
generate_text(
    prompt,
    temperature=0.1
)
```

---

## 25. Error handling

We added handling for:

```text
HTTPError
URLError
```

For example:

```text
URLError
```

can happen when Python cannot connect to:

```text
localhost:11434
```

This usually means Ollama is not running.

A reusable client should produce a clear error such as:

```text
Could not connect to Ollama.
Make sure Ollama is running.
```

---

# Final Mental Model

```text
                     LOCAL LLM SETUP

                      Python app
                          │
                          ▼
                     HTTP request
                          │
                          ▼
                 localhost:11434
                          │
                          ▼
                        Ollama
                 model runtime/server
                          │
                          ▼
               qwen2.5:3b-instruct
                   actual 3B LLM
                          │
                          ▼
                  Generate tokens
                          │
                          ▼
                  HTTP JSON response
                          │
                          ▼
                       Python
```

## Key Takeaways

**Ollama is not an LLM. It is a local model runtime and manager.**

**Qwen2.5:3b-instruct is the actual generative language model.**

**3B means roughly 3 billion learned model parameters, not 3 billion training examples.**

**Model parameters are learned numerical values, not normal function arguments.**

**Ollama exposes a local HTTP API that Python can call.**

**The raw HTTP response arrives as bytes and is decoded into JSON.**

**Prompt tokens and generated tokens are counted separately.**

**The `context` array contains token IDs representing conversation state, including chat-template and generated tokens.**

**Token IDs belong to a particular tokenizer and are not universally interchangeable between models.**

**Embeddings cannot normally be decoded back into the original text.**

**Lower temperature is useful for focused, grounded RAG generation.**

---

# Step 8 Status

We now understand and have implemented:

```text
Ollama installation ✅
Local model execution ✅
Direct HTTP API calls ✅
Raw response parsing ✅
Token/context inspection ✅
Model parameters and weights ✅
Tokenizer differences ✅
Reusable Ollama client ✅
Basic generation configuration ✅
```

The next step is:

```text
Step 9 — Tools
```

where we move from:

```text
LLM → generate text
```

to:

```text
LLM → decide to use a tool → receive result → generate answer
```