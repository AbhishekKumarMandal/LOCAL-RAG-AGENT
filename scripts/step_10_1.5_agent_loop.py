import json

from step_08_1_ollama_basics import generate_text
from step_09_1_tools_basics import calculator


AGENT_INSTRUCTIONS = """
You are an assistant that can use tools.

Available tool:

Tool name: calculator

Arguments:
operation: one of add, subtract, multiply, divide
a: literal number
b: literal number

Rules:

1. Respond ONLY with valid JSON.
2. Do not output markdown.
3. Do not output explanations outside JSON.
4. a and b must always be literal numbers.
5. Never put mathematical expressions inside a or b.
6. Perform only ONE calculator operation at a time.
7. Use the previous tool operation history to decide the next step.
8. Do not repeat a calculation that is already present in the previous tool operations.
9. If the user's request does not require the calculator, return a final answer saying that the request does not require a mathematical operation.
10. If the request requires unsupported operations or invalid operands, return a final answer explaining that the request cannot be handled.
11. Do not invent tool results. Tool results are provided by the Python application.

If another calculator operation is required, respond in this format:

{
  "type": "tool_call",
  "tool": "calculator",
  "arguments": {
    "operation": "multiply",
    "a": 17,
    "b": 23
  }
}

If all required calculations are complete, respond in this format:

{
  "type": "final_answer",
  "answer": 400
}

Example:

User request:
Multiply 17 by 23 plus 9

Previous tool operations:
[]

Response:

{
  "type": "tool_call",
  "tool": "calculator",
  "arguments": {
    "operation": "multiply",
    "a": 17,
    "b": 23
  }
}

After Python executes the tool:

Previous tool operations:

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

The next response should be:

{
  "type": "tool_call",
  "tool": "calculator",
  "arguments": {
    "operation": "add",
    "a": 391,
    "b": 9
  }
}

After Python executes the second tool:

Previous tool operations:

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

Now respond:

{
  "type": "final_answer",
  "answer": 400
}
"""


def call_agent(user_message, history):
    """
    Ask the LLM what it should do next.

    The LLM receives:
    - original user request
    - previous tool operations
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
    json.loads() normally accepts duplicate keys and keeps
    the last value.

    Example:
        {"b": 17, "b": 44}

    This function rejects such JSON instead.
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
    Convert the JSON-formatted LLM response into
    a Python dictionary.
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
    Validate the tool request before executing it.
    """

    tool_name = tool_request.get("tool")

    if tool_name != "calculator":
        raise ValueError(
            f"Unsupported tool: {tool_name}"
        )

    arguments = tool_request.get("arguments")

    if not isinstance(arguments, dict):
        raise ValueError(
            "Tool arguments must be a JSON object"
        )

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
            f"Unsupported operation: {operation}"
        )

    if not isinstance(a, (int, float)):
        raise ValueError(
            f"'a' must be a number. Received: {a}"
        )

    if not isinstance(b, (int, float)):
        raise ValueError(
            f"'b' must be a number. Received: {b}"
        )


def execute_tool(tool_request):
    """
    Execute the validated calculator tool request.
    """

    arguments = tool_request["arguments"]

    return calculator(
        operation=arguments["operation"],
        a=arguments["a"],
        b=arguments["b"]
    )


def run_agent(user_message, max_iterations=10):
    """
    Agent loop:

    1. Ask LLM what to do.
    2. Parse response.
    3. If final answer -> return.
    4. If tool call -> validate.
    5. Execute tool.
    6. Store result in Python-controlled history.
    7. Ask LLM again.
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

        if response_type == "final_answer":

            if "answer" not in agent_response:
                raise ValueError(
                    "Final answer response is missing 'answer'"
                )

            return agent_response["answer"]

        if response_type == "tool_call":

            validate_tool_request(
                agent_response
            )

            tool_result = execute_tool(
                agent_response
            )

            print("\nTool result:")
            print(tool_result)

            history.append({
                "tool": agent_response["tool"],
                "arguments": agent_response["arguments"],
                "result": tool_result
            })

            continue

        raise ValueError(
            f"Unknown response type: {response_type}"
        )

    raise RuntimeError(
        f"Agent exceeded maximum iterations: {max_iterations}"
    )


if __name__ == "__main__":

    user_message = (
        "Multiply 17 by 23"
    )

    final_answer = run_agent(
        user_message
    )

    print("\nFinal answer:")
    print(final_answer)