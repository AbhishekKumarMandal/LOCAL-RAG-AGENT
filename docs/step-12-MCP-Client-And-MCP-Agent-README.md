# Step 12 - MCP Client and MCP Agent

## Goal

In this step, we build our own MCP client and connect it to the MCP server created in Step 11.

We then extend the client into an agent that can:

- discover MCP tools
- call MCP tools
- receive MCP tool results
- maintain tool history
- use an LLM to decide which MCP tool to call next
- return a final answer

Our MCP server exposes:

```text
calculator_tool
search_documents_tool
```

---

# MCP Client

An MCP client connects to an MCP server and interacts with the capabilities exposed by that server.

Conceptually:

```text
MCP Client
    ↓
MCP
    ↓
MCP Server
    ↓
Tools
```

The client does not directly import the tool implementation.

Instead, it communicates with the MCP server.

---

# Client and Server in Our Project

Our server:

```text
scripts/step_11_1_mcp_server.py
```

Our client scripts:

```text
scripts/step_12_1_mcp_client.py
scripts/step_12_2_call_mcp_tool.py
scripts/step_12_3_call_search_tool.py
scripts/step_12_4_mcp_agent.py
```

---

# Step 12.1 - Connect to MCP Server

We first created a simple MCP client that connects to the server and discovers available tools.

Important imports:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
```

---

# `StdioServerParameters`

`StdioServerParameters` tells the MCP client how to start the server process.

Example:

```python
server_params = StdioServerParameters(
    command=PYTHON_PATH,
    args=[SERVER_SCRIPT]
)
```

Where:

```text
command
```

is the Python executable.

Example:

```text
/Users/.../local-rag-agent/venv/bin/python
```

and:

```text
args
```

contains the server script:

```text
scripts/step_11_1_mcp_server.py
```

---

# Why Use the Full Python Path?

We used the Python executable inside the project's virtual environment.

Example:

```text
/Users/.../local-rag-agent/venv/bin/python
```

instead of only:

```text
python
```

This ensures the MCP server starts using the correct Python environment even if the terminal is not currently inside the virtual environment.

---

# `stdio_client`

The MCP client uses:

```python
async with stdio_client(
    server_params
) as (read_stream, write_stream):
```

This does several things conceptually:

```text
start MCP server subprocess
        ↓
create stdin/stdout communication
        ↓
create read/write streams
```

These streams are then given to the MCP session.

---

# `ClientSession`

We create the MCP session using:

```python
async with ClientSession(
    read_stream,
    write_stream
) as session:
```

The session manages communication between the client and MCP server.

---

# MCP Initialization

Before using the server, the client performs the MCP initialization handshake:

```python
await session.initialize()
```

Conceptually:

```text
Client
   ↓
initialize
   ↓
Server
   ↓
capabilities / protocol information
```

After initialization, the client can discover and call tools.

---

# Discovering Tools

The client asks the MCP server for its tools:

```python
tools_response = await session.list_tools()
```

Then:

```python
tools = tools_response.tools
```

Our output was:

```text
Connected to MCP server.

Available tools:
- calculator_tool
- search_documents_tool
```

This proves that tool discovery works.

---

# Why Tool Discovery Matters

Without MCP, we might hardcode:

```python
AVAILABLE_TOOLS = [
    "calculator",
    "search_documents"
]
```

With MCP:

```text
Client
   ↓
tools/list
   ↓
MCP Server
   ↓
returns available tools
```

The client can dynamically discover:

- tool name
- description
- argument schema

This reduces coupling between the client and tool implementation.

---

# Step 12.2 - Calling `calculator_tool`

After discovering the tools, we called the calculator through MCP.

Example:

```python
result = await session.call_tool(
    "calculator_tool",
    arguments={
        "operation": "multiply",
        "a": 5,
        "b": 3
    }
)
```

Conceptually, the flow is:

```text
Python MCP Client
        ↓
session.call_tool(...)
        ↓
MCP JSON-RPC request
        ↓
stdio
        ↓
MCP Server
        ↓
calculator_tool
        ↓
calculator()
        ↓
15
```

---

# MCP Tool Result

The raw client result looked similar to:

```text
meta=None
content=[
    TextContent(
        type='text',
        text='15.0',
        ...
    )
]
structured_content={'result': 15.0}
is_error=False
result_type='complete'
```

The actual calculator produced:

```text
15.0
```

The surrounding structure was produced by the MCP SDK.

---

# MCP Result vs Tool Result

This distinction is important.

Tool logic returns:

```text
15.0
```

MCP wraps the result in an MCP-defined response structure:

```text
CallToolResult
    ↓
content
structured_content
is_error
metadata
```

So:

```text
calculator()
= business result

MCP
= communication wrapper around the result
```

---

# `TextContent`

A tool result may contain MCP content blocks.

For text-based results, we inspected:

```python
types.TextContent
```

Example:

```python
for content in result.content:

    if isinstance(
        content,
        types.TextContent
    ):
        print(content.text)
```

This produced:

```text
15.0
```

---

# Step 12.3 - Calling `search_documents_tool`

Next, we called our RAG-based search tool through MCP.

Example:

```python
result = await session.call_tool(
    "search_documents_tool",
    arguments={
        "question": "How do Kafka consumer groups work?"
    }
)
```

The result was:

```json
{
  "found": true,
  "answer": "Kafka consumer groups allow multiple consumers to share the work of processing topic partitions.",
  "results": [
    {
      "document_name": "backend_notes.md",
      "chunk_index": 1,
      "similarity": 0.767592924998927
    }
  ]
}
```

---

# Search Tool Flow

Conceptually:

```text
MCP Client
    ↓
search_documents_tool
    ↓
MCP Server
    ↓
semantic_search()
    ↓
retrieve document chunk
    ↓
build RAG prompt
    ↓
Ollama / Qwen
    ↓
grounded answer
```

The MCP client does not need to know how semantic search or RAG is implemented.

It only knows:

```text
tool name
arguments
result
```

---

# Step 12.4 - MCP Agent

After manually calling MCP tools, we created an agent.

The agent combines:

```text
LLM
+
MCP Client
+
Tool discovery
+
Tool execution
+
History
+
Python validation
```

---

# Agent Architecture

Our architecture is:

```text
                User
                  ↓
                 LLM
                  ↓
        chooses MCP tool call
                  ↓
             Python Agent
                  ↓
           validates request
                  ↓
             MCP Client
                  ↓
              stdio
                  ↓
             MCP Server
                  ↓
                Tool
                  ↓
              Result
                  ↓
             Python Agent
                  ↓
            stores history
                  ↓
                 LLM
```

---

# Dynamic Tool Discovery

Instead of hardcoding tool descriptions, the agent gets them from MCP:

```python
tools_response = await session.list_tools()
tools = tools_response.tools
```

We then pass information such as:

```text
name
description
input_schema
```

to the LLM.

This allows the model to know what tools exist.

---

# Building Tool Descriptions for the LLM

We convert MCP tool definitions into JSON-like text.

Example concept:

```python
{
    "name": "calculator_tool",
    "description": "...",
    "input_schema": {...}
}
```

The LLM can inspect this and decide which tool to use.

---

# Agent Response Types

The LLM is instructed to return only one of two main response types.

## Tool call

```json
{
  "type": "tool_call",
  "tool": "calculator_tool",
  "arguments": {
    "operation": "multiply",
    "a": 5,
    "b": 3
  }
}
```

## Final answer

```json
{
  "type": "final_answer",
  "answer": 15
}
```

Python parses the result and decides what to do next.

---

# Why Python Owns the Agent Loop

The LLM does not execute MCP tools directly.

It only generates a requested action.

Example:

```json
{
  "type": "tool_call",
  "tool": "calculator_tool",
  "arguments": {
    "operation": "multiply",
    "a": 5,
    "b": 3
  }
}
```

Python then performs:

```python
await session.call_tool(...)
```

So:

```text
LLM
= decides

Python
= orchestrates

MCP
= communicates

Tool
= executes
```

---

# Context and History

MCP does not automatically maintain the agent's reasoning history.

We maintain:

```python
history = []
```

Each successful tool operation is added to history.

Example:

```json
[
  {
    "tool": "calculator_tool",
    "arguments": {
      "operation": "multiply",
      "a": 5,
      "b": 3
    },
    "result": 15.0
  }
]
```

The history is sent back to the LLM on the next iteration.

---

# Why History Is Important

For a multi-step expression:

```text
5*3 + 2*4
```

the agent may perform:

```text
multiply(5,3)
→ 15

multiply(2,4)
→ 8

add(15,8)
→ 23
```

The MCP server itself does not automatically know that these calls are part of the same problem.

The client/agent tracks that context.

---

# `tool_feedback`

We added another history entry type:

```json
{
  "tool_feedback": "description of what was wrong"
}
```

This is generated by Python when the LLM produces an invalid request.

Example:

```json
{
  "tool_feedback": "calculator_tool argument 'a' must be a literal number."
}
```

The tool was NOT executed.

The next LLM iteration sees this feedback and gets a chance to correct itself.

---

# Why Use a Feedback Loop?

Small LLMs may generate invalid output.

For example:

```json
{
  "type": "tool_call",
  "tool": "calculator_tool",
  "arguments": {
    "operation": "add",
    "a": "5*3",
    "b": 8
  }
}
```

This is valid JSON but invalid calculator usage.

Python can detect the problem and provide feedback.

Flow:

```text
LLM
 ↓
invalid tool request
 ↓
Python validation
 ↓
tool_feedback
 ↓
LLM retries
```

---

# Malformed JSON

The LLM can also produce output such as:

```text
"a": 5*3
```

This is not valid JSON.

Therefore:

```python
json.loads(...)
```

fails before MCP is called.

We catch the parsing failure and add feedback instead of immediately executing anything.

---

# JSON Validation vs Tool Validation

These are two separate layers.

## Layer 1 - JSON validation

Checks whether the LLM response is valid JSON.

Example invalid output:

```text
"a": 5*3
```

Caught by:

```python
json.loads(...)
```

---

## Layer 2 - Tool argument validation

Valid JSON can still contain invalid tool arguments.

Example:

```json
{
  "a": "5*3"
}
```

This is valid JSON.

But `a` should be numeric.

Python checks:

```python
isinstance(a, (int, float))
```

before calling MCP.

---

# Duplicate JSON Keys

Normal Python behavior:

```python
json.loads(...)
```

silently accepts duplicate keys and keeps the last value.

Example:

```json
{
  "a": 5,
  "a": 10
}
```

may become:

```python
{
    "a": 10
}
```

This can hide malformed LLM output.

We added:

```python
object_pairs_hook=reject_duplicate_keys
```

to explicitly reject duplicate keys.

---

# Calculator Validation

Before calling:

```python
session.call_tool(...)
```

Python validates:

```text
operation
a
b
```

Example:

```python
valid_operations = {
    "add",
    "subtract",
    "multiply",
    "divide"
}
```

And:

```python
if not isinstance(a, (int, float)):
    ...
```

This prevents malformed calculator requests from reaching MCP.

---

# Why Validation Happens Before MCP

The intended flow is:

```text
LLM response
    ↓
JSON parsing
    ↓
Python validation
    ↓
MCP tool call
```

Invalid requests should never reach the MCP server.

---

# Duplicate Calculator Calls

The calculator is deterministic.

For example:

```text
multiply(5,3)
```

will always return:

```text
15
```

So if the exact calculation already exists in history, there is no reason to execute it again.

We check previous history before making the MCP call.

Conceptually:

```text
requested:
multiply(5,3)

history already contains:
multiply(5,3) → 15

therefore:
reuse 15
```

---

# Why Search Is Different

`search_documents_tool` is conceptually dynamic.

The underlying database or documents may change.

Therefore, unlike the calculator, we should not automatically assume every identical search can always be reused indefinitely.

Caching behavior should depend on the tool.

---

# Search Tool Short-Circuit

Our `search_documents_tool` already performs:

```text
semantic search
+
RAG answer generation
```

and returns:

```json
{
  "found": true,
  "answer": "...",
  "results": [...]
}
```

Because the tool already produces a final grounded answer, the outer agent does not need another LLM call.

Python can simply return:

```python
parsed_tool_result["answer"]
```

This avoids unnecessary repeated searches.

---

# Example - Unknown Document Answer

Question:

```text
What is the capital of France?
```

Our local documents did not contain the answer.

The tool returned:

```json
{
  "found": false,
  "answer": "I don't have enough information in the provided documents.",
  "results": []
}
```

The outer Python agent can immediately return the supplied answer.

There is no reason to repeatedly call the same document search.

---

# Agent Loop Safety

The agent loop has:

```python
max_iterations
```

Example:

```python
max_iterations=12
```

This prevents an infinite loop if the LLM repeatedly requests tools without completing the task.

Conceptually:

```text
for iteration in range(max_iterations):
    ...
```

If the agent still has not finished:

```python
raise RuntimeError(...)
```

---

# Final Answer Validation

A small LLM may invent a final arithmetic answer.

Example:

```text
tool results:
5
25
9

LLM final answer:
39
```

But:

```text
39
```

was never produced by the calculator.

We therefore validate numeric final answers when calculator_tool has been used.

Conceptually:

```text
final numeric answer
must appear in calculator results
```

Otherwise Python rejects it and sends tool feedback.

---

# Why This Validation Matters

The LLM should not secretly perform arithmetic after we explicitly require all arithmetic to go through the tool.

So:

```text
LLM:
decides which operation to perform

calculator_tool:
produces numeric results
```

The final numeric answer should therefore come from the calculator.

---

# Current Limitation - Mathematical Planning

The calculator MCP integration works, but the small Qwen model sometimes chooses the wrong next subexpression.

Example:

```text
2 + 3*5 + 4
```

Correct progression:

```text
3*5
→ 15

2+15
→ 17

17+4
→ 21
```

The model may instead choose a valid but logically incorrect next operation.

This is not an MCP problem.

It is an:

```text
LLM planning / state tracking problem
```

The generated JSON can be valid.

The calculator arguments can also be valid.

But the selected operation may still be mathematically wrong.

---

# Syntactic vs Semantic Errors

This distinction is important.

## Syntactic error

Example:

```text
"a": 5*3
```

Invalid JSON.

Easy for Python to detect.

---

## Schema / argument error

Example:

```json
{
  "a": "5*3"
}
```

Valid JSON, but wrong argument type.

Python validation can detect it.

---

## Semantic planning error

Example:

Original:

```text
(2 + 3) * 5 + 4
```

After:

```text
2 + 3 = 5
5 * 5 = 25
```

the correct next operation is:

```text
25 + 4
```

but the LLM may request:

```text
5 + 4
```

The request is valid JSON and uses valid numeric arguments, but it is logically wrong.

This is harder to detect without additional expression-state tracking.

---

# Prompt vs Python Responsibility

A useful design principle from this step:

```text
LLM
= flexible decisions and planning

Python
= deterministic validation and control flow
```

Do not rely on the LLM for things Python can reliably enforce.

Python should handle:

```text
JSON validation
tool-name validation
argument-type validation
duplicate deterministic calls
maximum iterations
known termination conditions
tool errors
final-answer validation
```

The LLM should mainly handle:

```text
Which tool should I use?
What arguments should I request?
What should I do next?
How should I formulate the final response?
```

---

# Why Not Put Everything in the Prompt?

A possible approach is to keep making the prompt larger and larger.

But with a small model:

```text
more rules
!=
guaranteed better behavior
```

A better design is often:

```text
clear prompt
+
strong Python orchestration
```

rather than:

```text
very large prompt
+
complete reliance on the model
```

---

# MCP Does Not Replace the Agent

MCP provides:

```text
tool discovery
tool schemas
tool invocation
standard communication
```

MCP does NOT automatically provide:

```text
reasoning
planning
conversation history
multi-step workflow
retry logic
validation logic
agent memory
```

Those responsibilities belong to the client/application.

---

# Architecture After Step 12

We now have:

```text
                    User
                      ↓
                     LLM
                      ↓
              Agent decision JSON
                      ↓
              Python validation
                      ↓
                  MCP Client
                      ↓
                    stdio
                      ↓
                  MCP Server
                 /          \
                /            \
   calculator_tool      search_documents_tool
          ↓                     ↓
     calculator              RAG system
          ↓                     ↓
        result                answer
                \            /
                 \          /
                  MCP Result
                      ↓
                Python history
                      ↓
                     LLM
```

---

# Evolution of the Project

Earlier:

```text
User
 ↓
Python
 ↓
calculator()
```

Then:

```text
User
 ↓
LLM
 ↓
Python tool dispatcher
 ↓
calculator()
```

Now:

```text
User
 ↓
LLM
 ↓
Python MCP Agent
 ↓
MCP Client
 ↓
MCP Server
 ↓
Tool
```

This separates:

```text
reasoning
communication
tool execution
```

into different layers.

---

# Step 12 Summary

In this step we learned:

```text
ClientSession
= MCP client session

StdioServerParameters
= tells the client how to start the MCP server

stdio_client
= starts/connects to the stdio MCP server

session.initialize()
= MCP handshake

session.list_tools()
= discover tools

session.call_tool()
= invoke an MCP tool

result.content
= MCP content blocks

TextContent
= text result returned through MCP
```

We also learned that:

```text
MCP does not maintain agent history automatically.
```

The client owns:

```text
conversation state
tool history
intermediate results
feedback
agent loop
```

And the most important architecture principle from this step is:

```text
LLM
= decision maker

Python
= orchestrator and validator

MCP
= standardized communication layer

MCP Server
= tool provider

Tool
= actual executor
```

---

# Current Project Status

Completed:

```text
Step 1   Embeddings
Step 2   Cosine Similarity
Step 3   PostgreSQL + pgvector
Step 4   Chunking
Step 5   Document Ingestion
Step 6   Semantic Search
Step 7   RAG
Step 8   Ollama
Step 9   Tools
Step 10  Agent Loop
Step 11  MCP Server
Step 12  MCP Client + MCP Agent
```

Next:

```text
Step 13 - GitHub and Project Cleanup
```

Before considering the project fully finished, we will later return to the remaining calculator-planning issue and improve the agent's handling of mathematical expression state.