# Step 10 — Agent Loop

## 1. What is an Agent Loop?

In Step 9, our LLM could select a tool once:

```text
User
  ↓
LLM
  ↓
Tool call
  ↓
Tool result
  ↓
Final answer
```

That works for simple tasks.

But some problems require multiple tool calls.

Example:

```text
Multiply 17 by 23 plus 9
```

This requires:

```text
17 * 23 = 391
391 + 9 = 400
```

So we need:

```text
LLM
 ↓
tool call
 ↓
tool result
 ↓
LLM decides again
 ↓
another tool call
 ↓
tool result
 ↓
LLM decides again
 ↓
final answer
```

This repeated decision-making process is the **agent loop**.

---

# 2. Basic Agent Loop

The core idea is:

```text
while task is not complete:

    ask LLM what to do

    if LLM says:
        final_answer
            → stop

    if LLM says:
        tool_call
            → execute tool
            → store result
            → ask LLM again
```

In Python we used a bounded loop:

```python
for iteration in range(max_iterations):
```

instead of:

```python
while True:
```

because we need protection against infinite loops.

---

# 3. Why `max_iterations` is Important

An LLM may behave incorrectly and repeatedly request tools.

For example:

```text
tool call
→ result
→ same tool call
→ result
→ same tool call
→ ...
```

Without a limit, the application could run forever.

So we keep something like:

```python
max_iterations = 10
```

If the agent does not finish:

```text
RuntimeError:
Agent exceeded maximum iterations
```

This is an important safety boundary.

---

# 4. LLM vs Python Responsibilities

An important design decision was:

```text
LLM
= decides what should happen next

Python
= owns state and executes tools

Tool
= performs the actual operation
```

The LLM should NOT be responsible for maintaining the authoritative history.

Python should maintain:

```python
history = []
```

and append actual tool operations after they are executed.

Example:

```json
[
  {
    "tool": "calculator",
    "arguments": {
      "operation": "multiply",
      "a": 17,
      "b": 23
    },
    "result": 391
  }
]
```

This is safer because Python knows what actually happened.

---

# 5. Why Python Should Own History

Initially, we considered asking the LLM to send:

```json
{
  "current": {...},
  "previous": [...]
}
```

But that creates a problem.

The LLM could accidentally modify previous results.

For example:

```text
actual result:
391

LLM accidentally remembers:
392
```

That corrupts the agent state.

So the better architecture is:

```text
Python
→ authoritative history

LLM
→ reads history and decides next action
```

---

# 6. Structured Agent Responses

We use two response types.

## Tool call

```json
{
  "type": "tool_call",
  "tool": "calculator",
  "arguments": {
    "operation": "multiply",
    "a": 17,
    "b": 23
  }
}
```

## Final answer

```json
{
  "type": "final_answer",
  "answer": 400
}
```

This lets Python clearly understand whether it should:

```text
execute another tool
```

or:

```text
stop the loop
```

---

# 7. Multi-Step Calculation Example

User:

```text
Multiply 17 by 23 plus 9
```

Iteration 1:

```json
{
  "type": "tool_call",
  "tool": "calculator",
  "arguments": {
    "operation": "multiply",
    "a": 17,
    "b": 23
  }
}
```

Tool result:

```text
391
```

Iteration 2:

```json
{
  "type": "tool_call",
  "tool": "calculator",
  "arguments": {
    "operation": "add",
    "a": 391,
    "b": 9
  }
}
```

Tool result:

```text
400
```

Iteration 3:

```json
{
  "type": "final_answer",
  "answer": 400
}
```

---

# 8. Problem — Duplicate JSON Keys

We observed output such as:

```json
{
  "arguments": {
    "a": 9,
    "b": 17,
    "b": 44
  }
}
```

This is problematic.

Python's normal:

```python
json.loads(...)
```

may accept duplicate keys and keep the last value.

So:

```json
{
  "b": 17,
  "b": 44
}
```

can become:

```python
{
    "b": 44
}
```

We therefore added duplicate-key detection using:

```python
object_pairs_hook
```

and reject duplicate fields.

---

# 9. JSON Parsing is Not Validation

Even valid JSON may still contain invalid values.

Example:

```json
{
  "tool": "calculator",
  "arguments": {
    "operation": "multiply",
    "a": "five",
    "b": 3
  }
}
```

This is valid JSON.

But `"five"` is not a valid calculator operand.

So the flow should be:

```text
LLM output
   ↓
parse JSON
   ↓
check duplicate keys
   ↓
validate schema
   ↓
validate argument types
   ↓
execute tool
```

---

# 10. Multi-Tool Agent

We later expanded the agent to support:

```text
calculator
search_documents
```

Now the LLM can decide which capability is needed.

Example:

```text
"What is 17 * 23?"
        ↓
calculator
```

Example:

```text
"How do Kafka consumer groups work?"
        ↓
search_documents
```

So:

```text
                    User
                      ↓
                     LLM
                 ┌────┴────┐
                 ↓         ↓
           calculator  search_documents
                 ↓         ↓
                 └────┬────┘
                      ↓
                    result
                      ↓
                     LLM
```

---

# 11. Document Search as a Tool

The `search_documents` tool performs:

```text
question
   ↓
semantic_search()
   ↓
PostgreSQL + pgvector
   ↓
matching chunks
   ↓
build_rag_prompt()
   ↓
Qwen
   ↓
grounded answer
```

This means the tool does more than raw retrieval.

It returns both:

```text
raw search results
```

and:

```text
grounded refined answer
```

Example:

```json
{
  "found": true,
  "answer": "Kafka consumer groups allow multiple consumers to share the work of processing topic partitions.",
  "results": [
    {
      "document_name": "backend_notes.md",
      "chunk_index": 1,
      "content": "...",
      "similarity": 0.7494
    }
  ]
}
```

---

# 12. Why Reuse the Step 7 RAG Logic?

Initially, the agent returned almost the entire retrieved chunk.

That caused unrelated PostgreSQL content to appear in the final Kafka answer.

So we reused:

```text
build_rag_prompt()
```

from Step 7.

This lets us:

```text
retrieve raw chunks
        ↓
refine them using strict grounded prompt
        ↓
return only relevant answer
```

This improved answer quality significantly.

---

# 13. Repeated Search Calls

We decided NOT to cache `search_documents`.

Why?

Because the database may change.

For the same query:

```text
How do Kafka consumer groups work?
```

later:

```text
new documents may exist
new embeddings may exist
ranking may change
documents may be updated
```

So:

```text
search_documents
→ always execute fresh
```

This includes:

```text
fresh semantic search
+
fresh RAG generation
```

---

# 14. Repeated Calculator Calls

Calculator is different.

The calculator is deterministic.

Example:

```text
multiply(5, 3)
```

will always produce:

```text
15
```

So if the exact same calculator request appears again:

```text
same tool
+
same operation
+
same operands
```

we can reuse the previous result.

Example:

```text
multiply(5,3)
→ first call = execute calculator
→ result 15

multiply(5,3)
→ later call = reuse 15
```

This is effectively **tool-result caching**.

---

# 15. Deterministic vs Dynamic Tools

This led to an important concept.

## Deterministic tool

Same input always gives same output.

Example:

```text
calculator
```

So caching is safe.

## Dynamic tool

Same input may produce different output later.

Examples:

```text
search_documents
weather
current_time
latest_news
stock_price
```

These should usually execute again.

So caching policy should be tool-specific.

---

# 16. Operator Precedence Problem

We tested:

```text
5*3 + 2*4 + 5*3
```

Initially the agent did:

```text
5*3 = 15
```

then incorrectly jumped to:

```text
15 + 8
```

even though:

```text
2*4 = 8
```

had never been calculated by the tool.

This showed that the model was doing hidden arithmetic.

---

# 17. No Hidden Arithmetic Rule

We added a strict rule:

> Every intermediate arithmetic result must come from the calculator tool.

A number can only be used if:

```text
1. it appeared literally in the original user request

OR

2. it appeared as a result in Previous tool operations
```

So after:

```text
5*3 = 15
```

this is invalid:

```text
add(15, 8)
```

because `8` has not yet been produced by the calculator.

The agent must first request:

```text
2*4
```

---

# 18. BODMAS / Operator Precedence

We explicitly added arithmetic precedence:

```text
1. Parentheses
2. Multiplication and division
3. Addition and subtraction
```

Operations with equal precedence are evaluated left to right.

For:

```text
5*3 + 2*4 + 5*3
```

the expected plan is:

```text
5*3 = 15

2*4 = 8

15+8 = 23

23+15 = 38
```

The final `5*3` does not need recalculation because:

```text
5*3 = 15
```

already exists in history.

---

# 19. Reusing Identical Subexpressions

We tested:

```text
(5*3) + (5*3)
```

The agent correctly performed:

```text
5*3 = 15
```

only once.

Then it requested:

```text
15 + 15
```

rather than calculating `5*3` again.

This is correct because the previously calculated result can be reused.

Conceptually:

```text
(5*3) + (5*3)

   ↓

15 + 15

   ↓

30
```

This is similar to:

```text
memoization
```

or:

```text
common subexpression reuse
```

---

# 20. Why the Agent Repeated the Same Tool Call Forever

We encountered a case where the LLM repeatedly returned:

```text
add(15, 8)
```

for multiple iterations.

The reason was:

```text
LLM requested duplicate call
        ↓
Python reused previous result
        ↓
history did not change
        ↓
next prompt was effectively identical
        ↓
temperature = 0
        ↓
LLM returned same request
```

So we had:

```text
same input prompt
→ same LLM output
→ same input prompt
→ same LLM output
```

until:

```text
max_iterations
```

was reached.

---

# 21. Tool Feedback

To avoid that loop, when a duplicate result is reused we can send explicit feedback.

Example:

```json
{
  "type": "tool_feedback",
  "tool": "calculator",
  "arguments": {
    "operation": "add",
    "a": 15,
    "b": 8
  },
  "result": 23,
  "message": "This exact calculation was already completed. Use this result and do not request the same calculation again."
}
```

Now the next prompt is different.

The model sees:

```text
this calculation already exists
result = 23
move forward
```

instead of receiving exactly the same state again.

---

# 22. Important Stopping Rule

The model must determine whether the original task is complete.

After every tool result, it should ask:

```text
Have all required operations in the original request been completed?
```

If yes:

```json
{
  "type": "final_answer",
  "answer": 38
}
```

It should NOT request another tool call.

---

# 23. Final Arithmetic Test

We tested:

```text
5*3 + 2*4 + 5*3
```

The final correct flow was:

```text
Iteration 1

multiply(5,3)
→ 15


Iteration 2

multiply(2,4)
→ 8


Iteration 3

add(15,8)
→ 23


Iteration 4

add(23,15)
→ 38


Iteration 5

final_answer
→ 38
```

This demonstrates:

```text
operator precedence
+
tool execution
+
history
+
result reuse
+
multi-step planning
+
stop condition
```

---

# 24. Prompt Engineering Became Important

As the calculation examples became more complex, we added rules such as:

```text
Do not perform hidden arithmetic.

Do not invent intermediate values.

Follow operator precedence.

Check history before every tool call.

Do not repeat solved operations.

Use previous tool results.

Return final_answer when the task is complete.
```

This improved the behavior of our small local model significantly.

---

# 25. Small Model Limitation

We are using:

```text
qwen2.5:3b-instruct
```

A 3B model can follow tool instructions, but complex planning may require more explicit prompts and examples.

This is why few-shot examples helped.

Example:

```text
5*3 + 2*4 + 5*3
```

was included directly in the prompt to demonstrate the expected reasoning pattern.

---

# 26. Prompt Caching in the Agent Loop

During repeated agent iterations, Ollama returned:

```text
prompt_eval_count
prompt_eval_cached_count
```

Example:

```text
Iteration 1

prompt_eval_count = 666
prompt_eval_cached_count = 0
```

Later:

```text
Iteration 2

prompt_eval_count = 716
prompt_eval_cached_count = 657
```

and:

```text
Iteration 3

prompt_eval_count = 766
prompt_eval_cached_count = 707
```

The first request had no cached prefix.

Later prompts reused a large common prefix:

```text
agent instructions
+
user request
+
existing history
```

Only the newly added history required fresh evaluation.

Conceptually:

```text
prompt_eval_count
=
total prompt tokens

prompt_eval_cached_count
=
tokens whose previous computation could be reused
```

So approximately:

```text
fresh tokens
=
prompt_eval_count
-
prompt_eval_cached_count
```

This explains why later agent iterations can have lower prompt-processing latency.

---

# 27. Agent Loop vs RAG

RAG:

```text
Question
 ↓
automatic retrieval
 ↓
LLM
 ↓
answer
```

Agent:

```text
Question
 ↓
LLM decides what it needs
 ↓
tool
 ↓
result
 ↓
LLM decides again
 ↓
possibly another tool
 ↓
final answer
```

RAG is a fixed pipeline.

The agent loop is dynamic.

---

# 28. Agent + RAG

Our multi-tool agent combines both.

For a calculation:

```text
User
 ↓
Agent
 ↓
calculator
```

For a document question:

```text
User
 ↓
Agent
 ↓
search_documents
 ↓
semantic search
 ↓
RAG generation
```

So RAG becomes one capability available to the agent.

---

# 29. Final Architecture

```text
                         User
                          │
                          ▼
                         LLM
                    Agent decision
                          │
                ┌─────────┴─────────┐
                │                   │
                ▼                   ▼
          calculator         search_documents
                │                   │
                │             semantic search
                │                   │
                │               pgvector
                │                   │
                │             RAG generation
                │                   │
                └─────────┬─────────┘
                          ▼
                       Tool result
                          │
                          ▼
                     Python history
                          │
                          ▼
                         LLM
                          │
                    Need more tools?
                     /           \
                   yes            no
                    │              │
                    ▼              ▼
                  tool        final_answer
```

---

# 30. Key Lessons

**An agent loop allows an LLM to perform multiple actions before answering.**

**Python should own authoritative execution state.**

**The LLM should decide actions, not maintain trusted history.**

**Tool calls must be parsed and validated before execution.**

**Duplicate JSON keys should be rejected.**

**Calculator results can be cached because the calculator is deterministic.**

**Document search should execute fresh because the database may change.**

**Intermediate arithmetic results should come from tools, not hidden LLM calculations.**

**Operator precedence must be explicitly respected.**

**Identical solved subexpressions can reuse previous results.**

**The prompt must change after repeated tool behavior, otherwise deterministic generation may repeat forever.**

**A maximum iteration limit is always required.**

**RAG can be exposed as a tool inside an agent.**

---

# Step 10 Status

We have now implemented and understood:

```text
Basic agent loop ✅

Multiple tool calls ✅

Python-managed history ✅

Structured tool decisions ✅

Tool validation ✅

Duplicate JSON detection ✅

Maximum iteration guard ✅

Multiple tools ✅

Calculator tool ✅

Document-search tool ✅

RAG integration inside tool ✅

Grounded document answers ✅

Deterministic tool-result reuse ✅

Dynamic search refresh ✅

Operator precedence ✅

No hidden arithmetic ✅

Intermediate result provenance ✅

Repeated subexpression reuse ✅

Duplicate-call feedback ✅

Agent stop conditions ✅

Ollama prompt caching ✅
```

The next step is:

```text
Step 11 — MCP Server
```

where we move from:

```text
tools hardcoded inside our Python agent
```

to:

```text
tools exposed through a standard MCP server
```