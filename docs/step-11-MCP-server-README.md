# Step 11 - MCP Server

## Goal

In this step, we expose our existing tools through an MCP server.

The tools we expose are:

- `calculator_tool`
- `search_documents_tool`

This allows an MCP client to discover and invoke them without directly importing the Python functions.

---

## What is MCP?

MCP stands for:

```text
Model Context Protocol
```

MCP is a protocol that standardizes how an AI application can interact with external capabilities such as:

```text
Tools
Resources
Prompts
```

In our project, we mainly use:

```text
Tools
```

Examples:

```text
calculator_tool
search_documents_tool
```

---

## Why use MCP?

Before MCP, our agent directly imported Python functions.

Example:

```python
from step_9_1_tools_basics import calculator

result = calculator(
    operation="multiply",
    a=5,
    b=3
)
```

This creates direct coupling between:

```text
Agent code
and
Tool implementation
```

With MCP:

```text
Agent / MCP Client
        ↓
      MCP
        ↓
   MCP Server
        ↓
      Tools
```

The client does not need to directly import the underlying tool implementation.

It discovers the tools from the server.

---

# MCP Server

The MCP server is responsible for exposing capabilities to MCP clients.

In our project:

```text
step_11_1_mcp_server.py
```

acts as the MCP server.

Conceptually:

```text
MCP Client
    ↓
MCP request
    ↓
MCP Server
    ↓
calculator_tool
or
search_documents_tool
```

---

## Creating the MCP server

We create the server using:

```python
from mcp.server import MCPServer

mcp = MCPServer(
    "Local RAG Agent MCP Server"
)
```

`MCPServer` is the server class.

```python
mcp
```

is our server instance.

The variable name does not have to be `mcp`.

For example, this would also work:

```python
server = MCPServer(
    "Local RAG Agent MCP Server"
)
```

and then:

```python
@server.tool()
```

Python is case-sensitive:

```text
MCPServer
```

and:

```text
mcp
```

are completely different things.

---

# Exposing a Tool

A normal Python function can be exposed as an MCP tool using:

```python
@mcp.tool()
```

Example:

```python
@mcp.tool()
def calculator_tool(
    operation: str,
    a: float,
    b: float
) -> float:

    return calculator(
        operation=operation,
        a=a,
        b=b
    )
```

The decorator:

```python
@mcp.tool()
```

registers the function with the MCP server.

The MCP client can then discover it.

---

## Why function type hints matter

Consider:

```python
def calculator_tool(
    operation: str,
    a: float,
    b: float
) -> float:
```

MCP can use this function definition to understand the tool arguments.

For example:

```text
operation → string
a         → number
b         → number
```

This information becomes part of the tool's input schema.

The client can discover that schema using MCP.

---

# Search Documents Tool

Our second MCP tool exposes the local RAG system.

Conceptually:

```text
search_documents_tool
        ↓
semantic search
        ↓
retrieve matching chunks
        ↓
build RAG prompt
        ↓
Ollama / Qwen
        ↓
grounded answer
```

Example result:

```json
{
  "found": true,
  "answer": "Kafka consumer groups allow multiple consumers to share the work of processing topic partitions.",
  "results": [
    {
      "document_name": "backend_notes.md",
      "chunk_index": 1,
      "similarity": 0.7675
    }
  ]
}
```

The important fields are:

```text
found
```

Whether relevant information was found.

```text
answer
```

The final grounded answer.

```text
results
```

Raw retrieved chunks and metadata.

---

# MCP vs Tool Logic

The MCP server does not replace the actual business logic.

For example:

```text
calculator()
```

still performs the arithmetic.

MCP only exposes that capability through a standard protocol.

Similarly:

```text
semantic_search()
build_rag_prompt()
generate_text()
```

still perform the RAG work.

MCP provides a standard interface around them.

---

# JSON-RPC

MCP messages use JSON-RPC.

JSON itself is only a data format.

For example:

```json
{
  "name": "calculator_tool",
  "a": 5,
  "b": 3
}
```

is valid JSON.

But JSON alone does not define:

```text
Which operation is being requested?
How should responses be matched to requests?
How are errors represented?
How are notifications represented?
```

JSON-RPC provides those communication rules.

---

## Example JSON-RPC request

Conceptually, an MCP tool call may look like:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "calculator_tool",
    "arguments": {
      "operation": "multiply",
      "a": 5,
      "b": 3
    }
  }
}
```

Important fields:

```text
jsonrpc
```

Protocol version.

```text
id
```

Request identifier.

Used to match a response with its request.

```text
method
```

The operation to execute.

Example:

```text
tools/call
```

```text
params
```

Arguments required by the operation.

---

## Example JSON-RPC response

Conceptually:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "value": 15
  }
}
```

The same:

```text
id = 1
```

allows the client to know which request produced the response.

---

# JSON vs JSON-RPC

JSON:

```text
Data format
```

JSON-RPC:

```text
Communication protocol using JSON
```

A useful mental model:

```text
JSON
= syntax

JSON-RPC
= request/response rules
```

Without JSON-RPC, we could create our own custom JSON protocol.

But then we would have to define:

```text
request IDs
method names
success format
error format
notifications
request-response matching
```

JSON-RPC already standardizes those concepts.

---

# MCP, JSON-RPC and Transport

These are different layers.

```text
MCP
    ↓
defines capabilities and methods

JSON-RPC
    ↓
defines the request/response message structure

Transport
    ↓
moves those messages between client and server
```

For example:

```text
MCP
→ tools/call

JSON-RPC
→ method, id, params, result

stdio
→ carries the JSON-RPC messages
```

---

# Transport

Transport means:

```text
How the MCP client and MCP server communicate.
```

In our project, we use:

```text
stdio
```

which means:

```text
standard input / standard output
```

---

## stdio communication

With stdio:

```text
MCP Client
     ↓
starts MCP server process
     ↓
stdin / stdout
     ↓
JSON-RPC messages
```

The client starts the server as a subprocess.

The client sends messages to the server's:

```text
stdin
```

and receives messages from:

```text
stdout
```

---

## Why stdio is useful

stdio is convenient for local tools because:

```text
No HTTP server is required
No port is required
No REST endpoint is required
```

The client can directly launch the MCP server.

---

# Is stdio stateful?

The stdio connection is long-lived while the MCP client and server are connected.

For example:

```text
Client connects
    ↓
Server process starts
    ↓
tools/list
    ↓
tools/call
    ↓
tools/call
    ↓
tools/call
    ↓
Client disconnects
    ↓
Server process ends
```

The same server process can handle many MCP requests.

However:

```text
MCP does NOT automatically preserve LLM conversation context.
```

---

# Where is Context Stored?

There are different kinds of state.

## 1. Transport state

The stdio connection remains open.

```text
Client ↔ Server
```

---

## 2. MCP session state

The client and server have completed the MCP initialization handshake.

---

## 3. Application / Agent state

This includes:

```text
User messages
Previous tool calls
Previous tool results
Conversation history
Intermediate calculations
Agent workflow state
```

This state is normally managed by the:

```text
MCP client / agent
```

not automatically by the MCP server.

---

## Example

User asks:

```text
5*3 + 2*4
```

The MCP server may receive:

```text
multiply(5,3)
```

and return:

```text
15
```

Later it may receive:

```text
multiply(2,4)
```

and return:

```text
8
```

The MCP server does not automatically know that these two calls belong to the same mathematical expression.

The agent/client maintains:

```text
Original request:
5*3 + 2*4

History:
5*3 = 15
2*4 = 8
```

The agent can then decide to call:

```text
add(15,8)
```

---

# MCP Server Should Usually Be a Tool Provider

For our project, we keep responsibilities separated:

```text
MCP Server
= exposes tools

MCP Client / Agent
= maintains workflow and context

Tool
= performs actual work
```

This makes the architecture easier to reason about.

---

# MCP Inspector

MCP Inspector is a debugging and testing UI for MCP servers.

A useful analogy is:

```text
Postman
for
MCP
```

It lets us:

```text
Connect to an MCP server
Discover tools
Inspect tool schemas
Call tools manually
Inspect responses
```

---

## Why use MCP Inspector?

Before writing our own MCP client, we can verify that the server works correctly.

For example:

```text
calculator_tool
```

can be tested manually.

Input:

```text
operation = multiply
a = 5
b = 3
```

Result:

```text
15
```

---

# Inspector and stdio

When using stdio, the Inspector can start the MCP server process.

Example configuration:

```text
Transport:
stdio

Command:
/path/to/venv/bin/python

Arguments:
scripts/step_11_1_mcp_server.py
```

The server does not need to be started separately.

Inspector starts it when connecting.

---

# Why use the full Python path?

Instead of:

```text
python
```

we used the full virtual-environment interpreter path:

```text
/Users/.../local-rag-agent/venv/bin/python
```

This ensures the MCP server uses the correct environment even if the terminal does not currently have the virtual environment activated.

That environment contains our required packages such as:

```text
mcp
transformers
torch
psycopg
```

---

# MCP Inspector and Node.js

MCP Inspector itself is a Node.js application.

Our MCP server is written in Python.

That is completely fine because MCP is language-independent.

For example:

```text
Node.js MCP Inspector
        ↓
       MCP
        ↓
Python MCP Server
```

The two programs communicate using the MCP protocol.

---

# `mcp[cli]`

We installed:

```text
mcp[cli]
```

The syntax:

```text
package[extra]
```

means:

```text
install the base package
+
install optional dependencies for that extra
```

For example:

```text
psycopg[binary]
```

means:

```text
psycopg
+
binary/precompiled implementation
```

Similarly:

```text
mcp[cli]
```

installs the MCP package plus its CLI-related dependencies.

---

# Running the MCP Server

The server can contain:

```python
if __name__ == "__main__":
    mcp.run()
```

This allows the script to run as an MCP server.

Example:

```bash
python scripts/step_11_1_mcp_server.py
```

In stdio mode, normally an MCP client starts this process for us.

---

# Tools Discovered by Our Server

Our server currently exposes:

```text
calculator_tool
search_documents_tool
```

Inspector successfully discovered both tools.

That confirmed that:

```text
Python functions
    ↓
@mcp.tool()
    ↓
MCP Server
    ↓
MCP tool discovery
```

is working.

---

# Search Tool Test

We tested:

```text
How do Kafka consumer groups work?
```

The semantic search returned a matching chunk.

The raw chunk also included PostgreSQL text because both sections existed inside the same stored chunk.

We later improved the MCP search tool so that it also runs the retrieved context through our RAG answer-generation step.

This gave a focused answer:

```text
Kafka consumer groups allow multiple consumers to share the work of processing topic partitions.
```

while still allowing raw retrieval results to be returned for debugging.

---

# Architecture After Step 11

Before MCP:

```text
Agent
   ↓
Python function
```

After Step 11:

```text
             MCP Server

      ┌─────────────────────┐
      │                     │
      │ calculator_tool     │
      │                     │
      │ search_documents    │
      │                     │
      └─────────────────────┘
                ▲
                │
               MCP
                │
                ▼
             Client
```

At this point, the server works.

The next step is to build our own MCP client instead of using Inspector manually.

---

# Step 11 Summary

In this step we learned:

```text
MCP
= standard protocol for exposing AI capabilities

MCP Server
= exposes tools/resources/prompts

@mcp.tool()
= registers a Python function as an MCP tool

JSON-RPC
= structured request/response communication format

stdio
= transport used to carry MCP messages locally

MCP Inspector
= debugging/testing UI for MCP servers

MCP session
!=
LLM conversation history

Agent/client
= normally owns workflow and conversation state
```

The most important architectural idea is:

```text
MCP does not perform the business logic.

MCP standardizes how the client discovers and calls that logic.
```

Our next step is:

```text
Step 12
MCP Client + MCP Agent
```