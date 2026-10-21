import json

from step_08_1_ollama_basics import generate_text
from step_09_1_tools_basics import calculator
from step_06_1_semantic_search import semantic_search
from step_07_1_build_rag_prompt import build_rag_prompt


AGENT_INSTRUCTIONS = """
You are an assistant that can use tools.

Available tools:

1. calculator

Purpose:
Perform basic arithmetic.

Arguments:
operation: one of add, subtract, multiply, divide
a: literal number
b: literal number


2. search_documents

Purpose:
Search the local document knowledge base.

Arguments:
question: question to search for


GENERAL RULES

1. Respond ONLY with valid JSON.

2. Do not output markdown.

3. Do not output explanations outside JSON.

4. Perform only ONE tool call at a time.

5. Before making any tool call, inspect:
   - the original user request
   - Previous tool operations

6. Use previous tool results whenever they are relevant.

7. Do not invent tool results.

8. Do not use prior knowledge when a tool result should be used.

9. If enough information is already available to answer the user,
   return final_answer.

10. Never keep requesting tools after the original user request
    has already been fully solved.


CALCULATOR RULES

11. The calculator supports only:

    add
    subtract
    multiply
    divide

12. a and b must always be literal numeric values.

13. Never put mathematical expressions inside a or b.

INVALID:

{
  "type": "tool_call",
  "tool": "calculator",
  "arguments": {
    "operation": "add",
    "a": 5 * 3,
    "b": 8
  }
}

VALID:

{
  "type": "tool_call",
  "tool": "calculator",
  "arguments": {
    "operation": "multiply",
    "a": 5,
    "b": 3
  }
}


14. NEVER perform arithmetic calculations by yourself.

Every intermediate numeric result must come from the calculator tool.

15. A number may be used as a calculator argument only if:

    - the number appears literally in the original user request

    OR

    - the number appears as a result in Previous tool operations

16. Never invent an intermediate number.

For example, if the user asks:

5*3 + 2*4

and Previous tool operations contains only:

5*3 = 15

you MUST NOT request:

add(15, 8)

because 8 has not yet been produced by the calculator.

You must first request:

multiply(2, 4)


17. Follow mathematical operator precedence.

Evaluate in this order:

    1. Parentheses
    2. Multiplication and division
    3. Addition and subtraction

For operations with the same precedence,
evaluate from left to right.


18. Before every calculator call:

    a. Read the original expression.

    b. Read Previous tool operations.

    c. Determine which required subexpressions
       have already been solved.

    d. Determine the next UNSOLVED operation
       according to operator precedence.

    e. Request only that operation.


19. Never skip an unresolved multiplication or division
    and move directly to addition or subtraction.


20. If the exact calculator operation you want to perform
    already exists in Previous tool operations,
    use its existing result.

Do NOT request the same operation again.


21. If Previous tool operations contains a tool_feedback entry
    saying a calculation has already been completed,
    use the supplied result and move to the next unresolved operation.

Do NOT request that calculation again.


22. After every calculator result,
    compare the completed operations with the original user request.

If all required operations are complete,
return final_answer on the next response.


23. If the latest result completes the user's mathematical expression,
    MUST return final_answer.

Do not make another calculator request.


SEARCH DOCUMENT RULES

24. For document questions, use search_documents.

25. search_documents may be executed again because the database
    may have changed and fresh search results may be different.

26. When search_documents returns an "answer" field,
    use that grounded answer for the user's response.

27. Do not copy unrelated information from raw search results.

28. Answer only what the user asked.

29. If search_documents returns:

{
  "found": false
}

return the supplied answer indicating that there is
not enough information in the provided documents.


CALCULATOR REQUEST FORMAT

{
  "type": "tool_call",
  "tool": "calculator",
  "arguments": {
    "operation": "multiply",
    "a": 17,
    "b": 23
  }
}


DOCUMENT SEARCH REQUEST FORMAT

{
  "type": "tool_call",
  "tool": "search_documents",
  "arguments": {
    "question": "How do Kafka consumer groups work?"
  }
}


FINAL ANSWER FORMAT

{
  "type": "final_answer",
  "answer": "final response"
}


EXAMPLE 1

User request:

Multiply 17 by 23 plus 9

Previous tool operations:

[]

Correct response:

{
  "type": "tool_call",
  "tool": "calculator",
  "arguments": {
    "operation": "multiply",
    "a": 17,
    "b": 23
  }
}


After Previous tool operations becomes:

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

Correct response:

{
  "type": "tool_call",
  "tool": "calculator",
  "arguments": {
    "operation": "add",
    "a": 391,
    "b": 9
  }
}


After Previous tool operations becomes:

[
  {
    "tool": "calculator",
    "arguments": {
      "operation": "multiply",
      "a": 17,
      "b": 23
    },
    "result": 391
  },
  {
    "tool": "calculator",
    "arguments": {
      "operation": "add",
      "a": 391,
      "b": 9
    },
    "result": 400
  }
]

Correct response:

{
  "type": "final_answer",
  "answer": 400
}


EXAMPLE 2

User request:

What is (5 * 3) + (5 * 3)?

Previous tool operations:

[]

Correct response:

{
  "type": "tool_call",
  "tool": "calculator",
  "arguments": {
    "operation": "multiply",
    "a": 5,
    "b": 3
  }
}


After Previous tool operations contains:

[
  {
    "tool": "calculator",
    "arguments": {
      "operation": "multiply",
      "a": 5,
      "b": 3
    },
    "result": 15
  }
]

The same subexpression appears twice.

The existing result 15 may be reused.

Correct next response:

{
  "type": "tool_call",
  "tool": "calculator",
  "arguments": {
    "operation": "add",
    "a": 15,
    "b": 15
  }
}


After Previous tool operations contains:

[
  {
    "tool": "calculator",
    "arguments": {
      "operation": "multiply",
      "a": 5,
      "b": 3
    },
    "result": 15
  },
  {
    "tool": "calculator",
    "arguments": {
      "operation": "add",
      "a": 15,
      "b": 15
    },
    "result": 30
  }
]

All required operations are complete.

Correct response:

{
  "type": "final_answer",
  "answer": 30
}


EXAMPLE 3

User request:

What is 5*3 + 2*4 + 5*3?

Previous tool operations:

[]

Because multiplication must happen before addition,
first request:

{
  "type": "tool_call",
  "tool": "calculator",
  "arguments": {
    "operation": "multiply",
    "a": 5,
    "b": 3
  }
}


After receiving:

5*3 = 15

Previous tool operations contains:

[
  {
    "tool": "calculator",
    "arguments": {
      "operation": "multiply",
      "a": 5,
      "b": 3
    },
    "result": 15
  }
]

The next unresolved multiplication is:

2*4

Correct response:

{
  "type": "tool_call",
  "tool": "calculator",
  "arguments": {
    "operation": "multiply",
    "a": 2,
    "b": 4
  }
}


Do NOT respond with:

{
  "type": "tool_call",
  "tool": "calculator",
  "arguments": {
    "operation": "add",
    "a": 15,
    "b": 8
  }
}

at this stage because 8 has not yet been produced
by the calculator tool.


After Previous tool operations contains:

[
  {
    "tool": "calculator",
    "arguments": {
      "operation": "multiply",
      "a": 5,
      "b": 3
    },
    "result": 15
  },
  {
    "tool": "calculator",
    "arguments": {
      "operation": "multiply",
      "a": 2,
      "b": 4
    },
    "result": 8
  }
]

Now multiplication operations are resolved.

Correct next response:

{
  "type": "tool_call",
  "tool": "calculator",
  "arguments": {
    "operation": "add",
    "a": 15,
    "b": 8
  }
}


After result:

15 + 8 = 23

Previous tool operations contains 23.

The final 5*3 subexpression has already been solved previously
and its existing result is 15.

Do NOT calculate 5*3 again.

Correct next response:

{
  "type": "tool_call",
  "tool": "calculator",
  "arguments": {
    "operation": "add",
    "a": 23,
    "b": 15
  }
}


After result:

23 + 15 = 38

all operations are complete.

Correct response:

{
  "type": "final_answer",
  "answer": 38
}


EXAMPLE 4

User request:

How do Kafka consumer groups work?

Previous tool operations:

[]

Correct response:

{
  "type": "tool_call",
  "tool": "search_documents",
  "arguments": {
    "question": "How do Kafka consumer groups work?"
  }
}


If search_documents returns:

{
  "found": true,
  "answer": "Kafka consumer groups allow multiple consumers to share the work of processing topic partitions."
}

then enough information is available.

Correct response:

{
  "type": "final_answer",
  "answer": "Kafka consumer groups allow multiple consumers to share the work of processing topic partitions."
}


IMPORTANT:

Strictly follow these rules.

Do not perform hidden arithmetic.

Do not invent intermediate numbers.

Do not skip unresolved higher-precedence operations.

Do not repeat completed calculations.

Use Previous tool operations as the source of truth
for all calculator results.

When the original request is fully solved,
return final_answer immediately.
"""


def call_agent(user_message, history):
    """
    Ask the LLM what action should be taken next.
    """

    prompt = (
        AGENT_INSTRUCTIONS
        + "\n\nUser request:\n"
        + user_message
        + "\n\nPrevious tool operations:\n"
        + json.dumps(history, indent=2)
        + "\n\nResponse:"
    )

    return generate_text(
        prompt,
        temperature=0.0
    )


def reject_duplicate_keys(pairs):
    """
    Reject JSON with duplicate keys.

    Example:
    {
        "a": 10,
        "a": 20
    }
    """

    result = {}

    for key, value in pairs:
        if key in result:
            raise ValueError(
                f"Duplicate JSON key: {key}"
            )

        result[key] = value

    return result


def parse_agent_response(response):
    """
    Convert JSON text returned by the LLM
    into a Python dictionary.
    """

    try:
        return json.loads(
            response,
            object_pairs_hook=reject_duplicate_keys
        )

    except json.JSONDecodeError as error:
        raise ValueError(
            f"LLM returned invalid JSON:\n{response}"
        ) from error


def validate_tool_request(tool_request):
    """
    Validate tool name and arguments before execution.
    """

    tool_name = tool_request.get("tool")
    arguments = tool_request.get("arguments")

    if tool_name not in {
        "calculator",
        "search_documents"
    }:
        raise ValueError(
            f"Unknown tool: {tool_name}"
        )

    if not isinstance(arguments, dict):
        raise ValueError(
            "Tool arguments must be a JSON object"
        )

    if tool_name == "calculator":

        operation = arguments.get("operation")
        a = arguments.get("a")
        b = arguments.get("b")

        allowed_operations = {
            "add",
            "subtract",
            "multiply",
            "divide"
        }

        if operation not in allowed_operations:
            raise ValueError(
                f"Invalid calculator operation: {operation}"
            )

        if not isinstance(a, (int, float)):
            raise ValueError(
                "'a' must be a number"
            )

        if not isinstance(b, (int, float)):
            raise ValueError(
                "'b' must be a number"
            )

    if tool_name == "search_documents":

        question = arguments.get("question")

        if not isinstance(question, str):
            raise ValueError(
                "'question' must be a string"
            )

        if not question.strip():
            raise ValueError(
                "'question' cannot be empty"
            )


def generate_grounded_answer(question, matches):
    """
    Reuse the strict RAG prompt from Step 7.
    """

    prompt = build_rag_prompt(
        question,
        matches
    )

    return generate_text(
        prompt,
        temperature=0.0
    )


def search_documents(question):
    """
    Always perform a fresh semantic search.

    This tool is intentionally NOT cached because
    the database may change between calls.

    Flow:
        semantic search
        -> latest matching chunks
        -> strict RAG prompt
        -> grounded answer
    """

    matches = semantic_search(
        question,
        top_k=3,
        min_similarity=0.65
    )

    if not matches:
        return {
            "found": False,
            "answer": (
                "I don't have enough information "
                "in the provided documents."
            ),
            "results": []
        }

    results = []

    for match in matches:
        results.append({
            "document_name": match["document_name"],
            "chunk_index": match["chunk_index"],
            "content": match["content"],
            "similarity": match["cosine_similarity"]
        })

    grounded_answer = generate_grounded_answer(
        question,
        matches
    )

    return {
        "found": True,
        "answer": grounded_answer,
        "results": results
    }


def execute_tool(tool_request):
    """
    Execute a validated tool request.
    """

    tool_name = tool_request["tool"]
    arguments = tool_request["arguments"]

    if tool_name == "calculator":
        return calculator(
            operation=arguments["operation"],
            a=arguments["a"],
            b=arguments["b"]
        )

    if tool_name == "search_documents":
        return search_documents(
            arguments["question"]
        )

    raise ValueError(
        f"Unknown tool: {tool_name}"
    )


def find_previous_calculator_call(tool_request, history):
    """
    Reuse previous results ONLY for calculator.

    Calculator is deterministic:
        same operation + same arguments
        -> same result

    search_documents is NOT checked here because
    document search results may change over time.
    """

    if tool_request["tool"] != "calculator":
        return None

    for item in history:

        if (
            item["tool"] == "calculator"
            and
            item["arguments"] == tool_request["arguments"]
        ):
            return item

    return None


def get_tool_result(tool_request, history):
    """
    Calculator:
        reuse previous result if exact same call
        already happened.

    search_documents:
        always execute again to get fresh results.

    Returns:
        tool_result,
        reused_previous_result
    """

    if tool_request["tool"] == "calculator":

        previous_call = find_previous_calculator_call(
            tool_request,
            history
        )

        if previous_call is not None:

            print(
                "\nSame calculator call "
                "was already executed."
            )

            print(
                "Reusing previous calculator result."
            )

            return (
                previous_call["result"],
                True
            )

    # search_documents always reaches here
    # and performs a fresh search.
    tool_result = execute_tool(
        tool_request
    )

    return (
        tool_result,
        False
    )


def run_agent(user_message, max_iterations=10):
    """
    Multi-tool agent loop.

    Flow:

    1. Ask LLM what to do next.
    2. Parse JSON response.
    3. If final_answer -> return answer.
    4. If tool_call -> validate request.
    5. Calculator:
           reuse previous identical result if available.
       Search documents:
           always execute fresh.
    6. Store operation and result in Python history.
    7. Ask the LLM again.
    """

    history = []

    for iteration in range(max_iterations):

        print(
            f"\n--- Agent iteration {iteration + 1} ---"
        )

        llm_response = call_agent(
            user_message,
            history
        )

        print("\nLLM response:")
        print(llm_response)

        agent_response = parse_agent_response(
            llm_response
        )

        response_type = agent_response.get(
            "type"
        )

        # ---------------------------------
        # Final answer
        # ---------------------------------

        if response_type == "final_answer":

            if "answer" not in agent_response:
                raise ValueError(
                    "Final answer response "
                    "is missing 'answer'"
                )

            return agent_response["answer"]

        # ---------------------------------
        # Tool call
        # ---------------------------------

        if response_type == "tool_call":

            validate_tool_request(
                agent_response
            )

            tool_result, reused = get_tool_result(
                agent_response,
                history
            )

            if reused:

                history.append({
                    "type": "tool_feedback",
                    "tool": agent_response["tool"],
                    "arguments": agent_response["arguments"],
                    "result": tool_result,
                    "message": (
                        "This exact tool call was already completed. "
                        "Use this existing result and do not request "
                        "the same calculation again."
                    )
                })

            else:

                history.append({
                    "type": "tool_result",
                    "tool": agent_response["tool"],
                    "arguments": agent_response["arguments"],
                    "result": tool_result
                })

            print("\nTool result:")
            print(
                json.dumps(
                    tool_result,
                    indent=2,
                    default=str
                )
            )

            continue

        raise ValueError(
            f"Unknown response type: {response_type}"
        )

    raise RuntimeError(
        f"Agent exceeded maximum iterations: "
        f"{max_iterations}"
    )


if __name__ == "__main__":

    user_message = (
        "what is 5*3+2*4+5*3 ?"
    )

    final_answer = run_agent(
        user_message
    )

    print("\nFinal answer:")
    print(final_answer)