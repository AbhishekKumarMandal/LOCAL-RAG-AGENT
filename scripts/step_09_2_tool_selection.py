import json

from step_08_1_ollama_basics import generate_text
from step_09_1_tools_basics import calculator


TOOL_DESCRIPTION = """
You have access to one tool.

Tool name: calculator

Arguments:
operation: one of add, subtract, multiply, divide
a: a literal number
b: a literal number

Rules:

1. Output ONLY one JSON object.
2. Do not output markdown.
3. Do not output explanations.
4. a and b MUST be JSON numbers.
5. a and b MUST NOT contain expressions.
6. Never write values like:
   17 * 23
   5 + 9
   100 / 4

7. If the user request requires multiple calculations,
   choose ONLY the first calculation that must be performed.

Example:

User:
Multiply 17 by 23 plus 9

Correct response:

{
  "tool": "calculator",
  "arguments": {
    "operation": "multiply",
    "a": 17,
    "b": 23
  }
}

Do NOT try to solve the second calculation yet.

If no calculation is required, respond:

{
  "tool": null,
  "answer": "your answer"
}

Response:
"""


def ask_llm_for_tool(user_message):
    prompt = (
        TOOL_DESCRIPTION
        + "\n\n"
        + f"User request:\n{user_message}\n\n"
        + "Response:"
    )

    response = generate_text(
        prompt,
        temperature=0.0
    )

    return response


def parse_tool_response(response):
    """
    Convert the LLM JSON string into a Python dictionary.
    """

    return json.loads(response)


def execute_tool(tool_request):

    tool_name = tool_request.get("tool")

    if tool_name == "calculator":

        arguments = tool_request["arguments"]

        return calculator(
            operation=arguments["operation"],
            a=arguments["a"],
            b=arguments["b"]
        )

    return None


def generate_final_answer(
    user_message,
    tool_result
):
    prompt = (
        "You are a helpful assistant.\n\n"
        f"User request:\n{user_message}\n\n"
        f"Tool result:\n{tool_result}\n\n"
        "Use the tool result to answer the user's request.\n"
        "Do not recalculate the answer yourself.\n\n"
        "Final answer:"
    )

    return generate_text(
        prompt,
        temperature=0.0
    )


if __name__ == "__main__":

    user_message = "multiply -17 with -0"

    # Step 1: Ask LLM whether a tool is needed
    llm_response = ask_llm_for_tool(
        user_message
    )

    print("\nRaw LLM response:")
    print(llm_response)
    '''
    above line prints this response in case of success
    {
        "tool": "calculator",
        "arguments": {
            "operation": "multiply",
            "a": 17,
            "b": 23
        }
    }

    in case of failure, it prints response like this
    {
        "tool": null,
        "answer": "your normal answer"
    }
    '''

    # Step 2: Convert JSON string to Python dictionary
    tool_request = json.loads(llm_response)

    # Step 3: Check whether LLM selected a tool
    if tool_request.get("tool") is None:

        final_answer = tool_request.get(
            "answer"
        )

    else:

        # Step 4: Execute selected tool
        tool_result = execute_tool(
            tool_request
        )

        print("\nTool result:")
        print(tool_result)

        # Step 5: Send tool result back to LLM
        final_answer = generate_final_answer(
            user_message,
            tool_result
        )

    print("\nFinal answer:")
    print(final_answer)