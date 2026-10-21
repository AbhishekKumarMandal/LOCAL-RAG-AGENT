import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import mcp.types as types

from step_8_1_ollama_basics import generate_text


PYTHON_PATH = (
    "/Users/abhishekkumarmandal/Documents/python/"
    "local-rag-agent/venv/bin/python"
)

SERVER_SCRIPT = "scripts/step_11_1_mcp_server.py"


# ---------------------------------------------------------
# MCP tool descriptions
# ---------------------------------------------------------

def build_tool_description(tools):
    """
    Convert MCP-discovered tools into text that can be
    supplied to the LLM.
    """

    tool_descriptions = []

    for tool in tools:
        tool_descriptions.append({
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema
        })

    return json.dumps(
        tool_descriptions,
        indent=2
    )


# ---------------------------------------------------------
# Agent prompt
# ---------------------------------------------------------

def build_agent_prompt(
    user_message,
    tools,
    history
):
    return (
        "You are an assistant that can use tools.\n\n"

        "Available tools were discovered from an MCP server.\n\n"

        f"Tools:\n{build_tool_description(tools)}\n\n"

        # -------------------------------------------------
        # General rules
        # -------------------------------------------------

        "GENERAL RULES:\n"

        "1. Respond ONLY with valid JSON.\n"

        "2. Do not output markdown or explanations outside JSON.\n"

        "3. Perform only ONE tool call at a time.\n"

        "4. Before making a tool call, inspect both the original user request "
        "and Previous tool operations.\n"

        "5. Use previous tool results whenever relevant.\n"

        "6. Do not invent tool results.\n"

        "7. If enough information is available to answer the user, "
        "return final_answer.\n"

        "8. Never repeat an identical calculator_tool call when its existing "
        "result can be reused.\n\n"

        # -------------------------------------------------
        # Calculator rules
        # -------------------------------------------------

        "CALCULATOR RULES:\n"

        "9. calculator_tool supports only add, subtract, multiply, and divide.\n"

        "10. Calculator arguments 'a' and 'b' MUST always be literal numbers.\n"

        "11. NEVER put a mathematical expression inside 'a' or 'b'.\n"

        "INVALID calculator argument:\n"
        '"a": "5 * 3"\n\n'

        "INVALID calculator argument:\n"
        '"a": 5 * 3\n\n'

        "VALID calculator arguments:\n"
        '"a": 5,\n'
        '"b": 3\n\n'

        "12. Perform only ONE arithmetic operation per calculator_tool call.\n"

        "13. NEVER perform arithmetic yourself. Every intermediate numeric "
        "result must come from calculator_tool.\n"

        "14. A number may be passed to calculator_tool only if it either:\n"
        "- appears literally in the original user request, OR\n"
        "- appears as a result of a successfully executed calculator_tool call "
        "in Previous tool operations.\n"

        "15. Follow mathematical operator precedence:\n"
        "- parentheses first\n"
        "- multiplication and division next\n"
        "- addition and subtraction last\n"
        "- operations with the same precedence are evaluated left to right\n"

        "16. Before each calculator call:\n"
        "- inspect the original mathematical expression\n"
        "- inspect Previous tool operations\n"
        "- determine which subexpressions are already solved\n"
        "- determine the CURRENT expression after replacing solved "
        "subexpressions with their results\n"
        "- choose the next UNSOLVED operation according to operator precedence\n"
        "- call calculator_tool only for that operation\n"

        "17. Do not skip an unresolved multiplication or division and move "
        "to addition or subtraction.\n"

        "18. If the exact calculator operation has already been completed, "
        "reuse its previous result instead of calling the calculator again.\n"

        "19. Once all operations in the original expression are complete, "
        "return final_answer immediately.\n"

        "20. After every successful calculator_tool call, conceptually replace "
        "ONLY the subexpression that was just calculated with its returned result.\n"

        "21. Determine the next operation from this updated expression.\n"

        "22. Do not use an earlier intermediate result merely because it has "
        "the same numeric value as another number in the expression.\n"

        "23. A previously calculated intermediate value that has already been "
        "consumed by another operation must not be treated as the current result "
        "of the whole expression.\n\n"

        # -------------------------------------------------
        # Document search rules
        # -------------------------------------------------

        "DOCUMENT SEARCH RULES:\n"

        "24. For questions that should be answered from the local documents, "
        "use search_documents_tool.\n"

        "25. When search_documents_tool returns an 'answer' field, use that "
        "grounded answer.\n"

        "26. Do not copy unrelated information from raw search results.\n"

        "27. If search_documents_tool returns found=false, use its supplied "
        "answer indicating that the documents do not contain enough information.\n\n"

        # -------------------------------------------------
        # Feedback
        # -------------------------------------------------

        "FEEDBACK RULES:\n"

        "28. Previous tool operations may contain a tool_feedback entry.\n"

        "29. tool_feedback means your previous response or tool call was invalid "
        "and was NOT executed.\n"

        "30. When tool_feedback is present, correct the problem described in it.\n"

        "31. Do NOT repeat the same invalid response.\n"

        "32. Continue solving the original user request after correcting it.\n\n"

        # -------------------------------------------------
        # Output formats
        # -------------------------------------------------

        "TOOL CALL FORMAT:\n"

        "{\n"
        '  "type": "tool_call",\n'
        '  "tool": "tool_name",\n'
        '  "arguments": {}\n'
        "}\n\n"

        "FINAL ANSWER FORMAT:\n"

        "{\n"
        '  "type": "final_answer",\n'
        '  "answer": "final response"\n'
        "}\n\n"

        "TOOL FEEDBACK FORMAT:\n"

        "{\n"
        '  "tool_feedback": "description of what was wrong with the previous response"\n'
        "}\n\n"

        # -------------------------------------------------
        # Calculator example 1
        # -------------------------------------------------

        "CALCULATOR EXAMPLE 1:\n"

        "User request:\n"
        "What is 5*3 + 2*4 + 5*3?\n\n"

        "Previous tool operations:\n"
        "[]\n\n"

        "Correct first response:\n"

        "{\n"
        '  "type": "tool_call",\n'
        '  "tool": "calculator_tool",\n'
        '  "arguments": {\n'
        '    "operation": "multiply",\n'
        '    "a": 5,\n'
        '    "b": 3\n'
        "  }\n"
        "}\n\n"

        "After calculator_tool returns 15, the next unresolved multiplication "
        "is 2*4.\n"

        "Correct next response:\n"

        "{\n"
        '  "type": "tool_call",\n'
        '  "tool": "calculator_tool",\n'
        '  "arguments": {\n'
        '    "operation": "multiply",\n'
        '    "a": 2,\n'
        '    "b": 4\n'
        "  }\n"
        "}\n\n"

        "After calculator_tool returns 8, multiplication operations are resolved.\n"

        "Correct next response:\n"

        "{\n"
        '  "type": "tool_call",\n'
        '  "tool": "calculator_tool",\n'
        '  "arguments": {\n'
        '    "operation": "add",\n'
        '    "a": 15,\n'
        '    "b": 8\n'
        "  }\n"
        "}\n\n"

        "After calculator_tool returns 23, reuse the existing result 15 "
        "for the repeated 5*3 subexpression.\n"

        "Correct next response:\n"

        "{\n"
        '  "type": "tool_call",\n'
        '  "tool": "calculator_tool",\n'
        '  "arguments": {\n'
        '    "operation": "add",\n'
        '    "a": 23,\n'
        '    "b": 15\n'
        "  }\n"
        "}\n\n"

        "After calculator_tool returns 38:\n"

        "{\n"
        '  "type": "final_answer",\n'
        '  "answer": 38\n'
        "}\n\n"

        # -------------------------------------------------
        # Calculator example 2 - parentheses/state
        # -------------------------------------------------

        "CALCULATOR EXAMPLE 2:\n"

        "Original expression:\n"
        "(2 + 3) * 5 + 4\n\n"

        "First operation:\n"
        "add(2, 3) -> 5\n\n"

        "Updated expression:\n"
        "5 * 5 + 4\n\n"

        "Next operation:\n"
        "multiply(5, 5) -> 25\n\n"

        "Updated expression:\n"
        "25 + 4\n\n"

        "The next operation MUST be add(25, 4).\n"

        "Do NOT use add(5, 4), because the intermediate result 5 from "
        "(2 + 3) has already been consumed by the multiplication that "
        "produced 25.\n\n"

        "After add(25, 4) returns 29, return:\n"

        "{\n"
        '  "type": "final_answer",\n'
        '  "answer": 29\n'
        "}\n\n"

        "NEVER pass the complete mathematical expression as calculator "
        "argument 'a' or 'b'.\n\n"

        # -------------------------------------------------
        # Current task
        # -------------------------------------------------

        f"Original user request:\n{user_message}\n\n"

        "Previous tool operations:\n"
        f"{json.dumps(history, indent=2)}\n\n"

        "Response:"
    )


# ---------------------------------------------------------
# JSON parsing
# ---------------------------------------------------------

def reject_duplicate_keys(pairs):
    """
    Reject duplicate JSON keys.

    Normal json.loads() silently keeps the last duplicate key,
    which can hide malformed LLM output.
    """

    result = {}

    for key, value in pairs:

        if key in result:
            raise ValueError(
                f"Duplicate JSON key: {key}"
            )

        result[key] = value

    return result


def parse_llm_response(response):
    """
    Parse model output as JSON.
    """

    try:
        return json.loads(
            response,
            object_pairs_hook=reject_duplicate_keys
        )

    except (
        json.JSONDecodeError,
        ValueError
    ) as error:

        raise ValueError(
            f"LLM returned invalid JSON:\n{response}"
        ) from error


# ---------------------------------------------------------
# MCP result helper
# ---------------------------------------------------------

def get_text_from_tool_result(result):
    """
    Extract TextContent from an MCP tool result.
    """

    texts = []

    for content in result.content:

        if isinstance(
            content,
            types.TextContent
        ):
            texts.append(content.text)

    if not texts:
        return None

    if len(texts) == 1:
        return texts[0]

    return "\n".join(texts)


# ---------------------------------------------------------
# Calculator helpers
# ---------------------------------------------------------

def find_existing_calculation(
    history,
    operation,
    a,
    b
):
    """
    Check whether an identical deterministic calculator
    operation has already been executed.
    """

    for item in history:

        if item.get("tool") != "calculator_tool":
            continue

        arguments = item.get(
            "arguments",
            {}
        )

        if (
            arguments.get("operation") == operation
            and arguments.get("a") == a
            and arguments.get("b") == b
            and "result" in item
        ):
            return item["result"]

    return None


def get_calculator_results(history):
    """
    Return all results produced by calculator_tool.
    """

    results = []

    for item in history:

        if (
            item.get("tool") == "calculator_tool"
            and "result" in item
        ):
            results.append(
                item["result"]
            )

    return results


# ---------------------------------------------------------
# Agent loop
# ---------------------------------------------------------

async def run_agent(
    session,
    tools,
    user_message,
    max_iterations=12
):
    history = []

    available_tool_names = {
        tool.name
        for tool in tools
    }

    for iteration in range(max_iterations):

        print(
            f"\n--- Agent iteration {iteration + 1} ---"
        )

        prompt = build_agent_prompt(
            user_message,
            tools,
            history
        )

        llm_response = generate_text(
            prompt,
            temperature=0.0
        )

        print("\nLLM response:")
        print(llm_response)

        # -------------------------------------------------
        # Parse LLM JSON
        # -------------------------------------------------

        try:
            agent_response = parse_llm_response(
                llm_response
            )

        except ValueError as error:

            history.append({
                "tool_feedback": (
                    "Your previous response was invalid JSON and was NOT executed. "
                    "Return only valid JSON matching one of the required formats. "
                    f"Error: {str(error)}"
                )
            })

            continue


        if not isinstance(agent_response, dict):

            history.append({
                "tool_feedback": (
                    "Your response must be a JSON object."
                )
            })

            continue


        response_type = agent_response.get(
            "type"
        )


        # =================================================
        # Final answer
        # =================================================

        if response_type == "final_answer":

            answer = agent_response.get(
                "answer"
            )

            calculator_results = (
                get_calculator_results(history)
            )

            # If calculator_tool was used, the final numeric
            # answer must have been produced by the calculator.
            if calculator_results:

                if (
                    isinstance(answer, bool)
                    or not isinstance(
                        answer,
                        (int, float)
                    )
                ):

                    history.append({
                        "tool_feedback": (
                            "The task used calculator_tool, so the final answer "
                            "must be the numeric result of a successfully executed "
                            "calculator_tool call. Do not calculate the result yourself."
                        )
                    })

                    continue


                if not any(
                    float(answer) == float(result)
                    for result in calculator_results
                    if isinstance(
                        result,
                        (int, float)
                    )
                ):

                    history.append({
                        "tool_feedback": (
                            f"Invalid final answer: {answer}. "
                            "This value was never produced by calculator_tool. "
                            "Do not perform arithmetic yourself. "
                            "Continue solving the original expression using "
                            "calculator_tool."
                        )
                    })

                    continue

            return answer


        # =================================================
        # Tool call
        # =================================================

        if response_type == "tool_call":

            tool_name = agent_response.get(
                "tool"
            )

            arguments = agent_response.get(
                "arguments"
            )


            # ---------------------------------------------
            # Validate tool
            # ---------------------------------------------

            if tool_name not in available_tool_names:

                history.append({
                    "tool_feedback": (
                        f"Unknown tool: {tool_name}. "
                        "Select one of the MCP-discovered tools."
                    )
                })

                continue


            if not isinstance(
                arguments,
                dict
            ):

                history.append({
                    "tool_feedback": (
                        "Tool arguments must be a JSON object."
                    )
                })

                continue


            # ---------------------------------------------
            # Calculator validation
            # ---------------------------------------------

            if tool_name == "calculator_tool":

                operation = arguments.get(
                    "operation"
                )

                a = arguments.get("a")
                b = arguments.get("b")

                valid_operations = {
                    "add",
                    "subtract",
                    "multiply",
                    "divide"
                }


                if operation not in valid_operations:

                    history.append({
                        "tool_feedback": (
                            f"Invalid calculator operation: {operation}. "
                            "Use only add, subtract, multiply, or divide."
                        )
                    })

                    continue


                if (
                    isinstance(a, bool)
                    or not isinstance(
                        a,
                        (int, float)
                    )
                ):

                    history.append({
                        "tool_feedback": (
                            "calculator_tool argument 'a' must be a literal "
                            "number. Do not pass a mathematical expression."
                        )
                    })

                    continue


                if (
                    isinstance(b, bool)
                    or not isinstance(
                        b,
                        (int, float)
                    )
                ):

                    history.append({
                        "tool_feedback": (
                            "calculator_tool argument 'b' must be a literal "
                            "number. Do not pass a mathematical expression."
                        )
                    })

                    continue


                # -----------------------------------------
                # Repeated deterministic calculation
                # -----------------------------------------

                existing_result = (
                    find_existing_calculation(
                        history,
                        operation,
                        a,
                        b
                    )
                )

                if existing_result is not None:

                    history.append({
                        "tool_feedback": (
                            f"The calculation "
                            f"{operation}({a}, {b}) has already been executed "
                            f"and returned {existing_result}. "
                            "Reuse that existing result and move to the next "
                            "unresolved operation."
                        )
                    })

                    continue


            # ---------------------------------------------
            # Execute MCP tool
            # ---------------------------------------------

            print(
                f"\nCalling MCP tool: {tool_name}"
            )

            result = await session.call_tool(
                tool_name,
                arguments=arguments
            )


            if result.is_error:

                history.append({
                    "tool_feedback": (
                        f"MCP tool {tool_name} returned an error. "
                        "Correct the request before trying again."
                    )
                })

                continue


            tool_result = (
                get_text_from_tool_result(
                    result
                )
            )

            print("\nTool result:")
            print(tool_result)


            # ---------------------------------------------
            # Parse tool result when it is JSON
            # ---------------------------------------------

            try:
                parsed_tool_result = (
                    json.loads(tool_result)
                )

            except (
                json.JSONDecodeError,
                TypeError
            ):
                parsed_tool_result = (
                    tool_result
                )


            # ---------------------------------------------
            # search_documents_tool already returns a
            # grounded answer, so no second LLM call needed
            # ---------------------------------------------

            if (
                tool_name
                == "search_documents_tool"
                and isinstance(
                    parsed_tool_result,
                    dict
                )
                and "answer"
                in parsed_tool_result
            ):
                return parsed_tool_result[
                    "answer"
                ]


            # ---------------------------------------------
            # Store successful tool operation
            # ---------------------------------------------

            history.append({
                "tool": tool_name,
                "arguments": arguments,
                "result": parsed_tool_result
            })

            continue


        # =================================================
        # Unknown response structure
        # =================================================

        history.append({
            "tool_feedback": (
                "Response must have type='tool_call' or "
                "type='final_answer'."
            )
        })


    raise RuntimeError(
        f"Agent exceeded maximum iterations: "
        f"{max_iterations}"
    )


# ---------------------------------------------------------
# MCP client
# ---------------------------------------------------------

async def run():

    server_params = StdioServerParameters(
        command=PYTHON_PATH,
        args=[SERVER_SCRIPT]
    )

    async with stdio_client(
        server_params
    ) as (
        read_stream,
        write_stream
    ):

        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            await session.initialize()

            print(
                "\nConnected to MCP server."
            )


            # ---------------------------------------------
            # Discover MCP tools
            # ---------------------------------------------

            tools_response = (
                await session.list_tools()
            )

            tools = tools_response.tools

            print(
                "\nDiscovered MCP tools:"
            )

            for tool in tools:
                print(
                    f"- {tool.name}"
                )


            # ---------------------------------------------
            # User request
            # ---------------------------------------------

            user_message = (
                "what is 2 + 3 * 5 + 4?"
            )


            final_answer = await run_agent(
                session,
                tools,
                user_message
            )


            print(
                "\nFinal answer:"
            )

            print(
                final_answer
            )


if __name__ == "__main__":
    asyncio.run(run())