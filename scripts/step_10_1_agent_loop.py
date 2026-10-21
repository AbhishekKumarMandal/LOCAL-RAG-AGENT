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

the json you will send must have only 2 fields

1) first field: "current" this will be a json that will tell either of these

1.1) tool_call, which is a request to use calculator tool
example
"current": {
    "type": "tool_call",
    "tool": "calculator",
    "arguments": {
        "operation": "multiply",
        "a": 17,
        "b": 23
    }
}

by looking into arguments i will use the calculator tool and i will provide you answer of this operation.

1.2) final answer of given question
example
"current": {
    "type": "final_answer",
    "answer": 391
}

this will tell that you have found the final answer of the question

2) second field: "previous" this will be an array that contains list of mathematical operations you have asked to perfom previously. and each list will contain the result of that operation as well
example
"previous": [
    {
        "type": "tool_call",
        "tool": "calculator",
        "arguments": {
            "operation": "multiply",
            "a": 17,
            "b": 23
        },
        "result": 391
    }
]


If you already have enough information to answer the user,
respond with type "final_answer" inside current:

 {
 	"current": {
 		"type": "final_answer",
 		"answer": 391
 	},

 	"previous": [
 		list of previous calculator tool operations
 	]
 }

For multi-step calculations, perform ONLY ONE calculation at a time. And store the calulations with response in previous array.

After receiving the result of a tool call, decide whether:
- another tool call is required
- or you can provide the final answer

EXAMPLES
example 1: Multiply 17 with 23
notice here only as single mathematical operation is required i.e. multiplication
so here i will ask you this question and your first answer should be like this where in you are requesting to use calculator tool to perform multiplication
 {
 	"current": {
 		"type": "tool_call",
 		"tool": "calculator",
 		"arguments": {
 			"operation": "multiply",
 			"a": 17,
 			"b": 23
 		}
 	},
 	"previous": []
 }
here i will give you response and then you store whatever is there in current in previous array along with answer

since the question involved only one mathematical operation so after sending the answer to your question, you should provide me with the final reponse like this
{
 	"current": {
 		"type": "final_answer",
 		"answer": 391
 	},

 	"previous": [
 		{
 			"type": "tool_call",
	 		"tool": "calculator",
	 		"arguments": {
	 			"operation": "multiply",
	 			"a": 17,
	 			"b": 23
	 		},
	 		"result": 391
 		}
 	]
 }

by looking at the type as final answer i will understand that this is the final answer and after that i will stop responding to you as i got my final answer


example 2: Multiply 17 with 23 plus 9
notice there are 2 mathematical operations involved multiplication and addition
after i asked this question, you should response me with request to use calculator tool to perform multiplication operation
{
  "current": {
	  "type": "tool_call",
	  "tool": "calculator",
	  "arguments": {
	    "operation": "multiply",
	    "a": 17,
	    "b": 23
	  },
	  "previous": []
  }
}

notice previous array is empty since this is the first time you are asking to perform multiplication.

after i provided you with the answer of multiplication then you should store that in previous array 

now since i provided you the response of multiplication operation and you stored the result of that operation so now you should respond me with the request to use calculator tool to perform addition operation.
and in the addition operation, reponse from the last multiplication operation becomes the first argument of addition operation. the request should look something like this
{
	"current": {
		"type": "tool_call",
		"tool": "calculator",
		"arguments": {
			"operation": "add",
			"a": 391,
			"b": 7
		}
	},

	"previous": [
		{
			"type": "tool_call",
	  		"tool": "calculator",
	  		"arguments": {
	    		"operation": "multiply",
	    		"a": 17,
	    		"b": 23
	  		},
	  		"result": 391
		}
	]
}

notice that in previous section you have to send the previous requests that you made along with the response that i had gave you when you made the request
also in this request inside the arguments field present inside current object notice how answer of previous calculation response becomes one of the arguments for next calculator tool operation.
i will provide you the answer to the addition operation along with the previous requests you have sent to me so that you will have the context of what all mathematcal operations has been performed so far

now after sending you the response, you should response me back with the final response since both multiplication and addition operation has been performed.
this is how you will send me the final response
{
	"current": {
		"type": "final_answer",
		"answer": 400
	},

	"previous": [
		{
			"type": "tool_call",
	  		"tool": "calculator",
	  		"arguments": {
	    		"operation": "multiply",
	    		"a": 17,
	    		"b": 23
	  		},
	  		"result": 391
		},

		{
			"type": "tool_call",
			"tool": "calculator",
			"arguments": {
				"operation": "add",
				"a": 491,
				"b": 9
			},
			"result": 400
		}
	]

}

notice that in previous section you have to send the previous requests that you made along with the response that i had gave you when you made the request.
after looking as the type "final_answer" inside current. i will understand that you have provided me with the final response and after this i will not reponsd you back and thhat will mark the end of conversation


main thing to note that in both examples as you can see, you have to respond ONLY with valid JSON. so that i can parse it and can understand you response. 

example3: what is capital of france.
in this question you can see that this question does not contain any mathematical operations and since there is no mathematical operation involved so you can respond with a neutral answer like this
{
	"current": {
		"type": "final_answer",
		"answer": "this question does not require any mathematical operation"
	},
	"previous": []
}

example 4: sine30 + sine60
this question requires addition operation but the operands are not normal numbers but they are trignometric values so you can response like this
{
	"current": {
		"type": "final_answer",
		"answer": "operands must be a real number"
	},
	"previous": []
}
operands must be a valid real number to and operation must be one of add, substract, multiply and divide.

at end i will say to strictly follow the reules that i have provided above. no need to be creative at all and do not provide you own answers.
from what ever i have provided here you have to respond using that only.

in case you came across something which is not mentioned here, you can simply respond like this

{
	"current": {
		"type": "final_answer",
		"answer": "i don't know"
	},
	"previous": []
}

"""


def call_agent(conversation):
    prompt = (
        AGENT_INSTRUCTIONS
        + "\n\nConversation:\n"
        + conversation
        + "\n\nResponse:"
    )

    return generate_text(
        prompt,
        temperature=0.0
    )


def execute_tool(tool_request):
    tool_name = tool_request["tool"]

    if tool_name == "calculator":
        arguments = tool_request["arguments"]

        return calculator(
            operation=arguments["operation"],
            a=arguments["a"],
            b=arguments["b"]
        )

    raise ValueError(
        f"Unknown tool: {tool_name}"
    )


def run_agent(user_message, max_iterations=5):

    conversation = (
        f"User request:\n{user_message}"
    )

    iteration = 0
    while True:
        iteration += 1

        print(
            f"\n--- Agent iteration {iteration} ---"
        )

        llm_response = call_agent(
            conversation
        )

        print("\nLLM response:")
        print(llm_response)

        try:
            agent_response = json.loads(
                llm_response
            )

        except json.JSONDecodeError:
            raise ValueError(
                f"LLM returned invalid JSON:\n{llm_response}"
            )

        current_response = agent_response.get("current")
        previous_responses = agent_response.get("previous")

        response_type=current_response["type"]

        if response_type == "final_answer":

            return current_response["answer"]

        if response_type == "tool_call":

            tool_result = execute_tool(
                current_response
            )

            print("\nTool result:")
            print(tool_result)

            conversation += (
                "\n\nAssistant requested tool:\n"
                + json.dumps(current_response)
                + "\n\nTool result:\n"
                + str(tool_result)
                + "\n\nPrevious Requests made\n"
                + json.dumps(previous_responses)
            )

            continue

        raise ValueError(
            f"Unknown response type: {response_type}"
        )

    raise RuntimeError(
        "Agent exceeded maximum iterations"
    )


if __name__ == "__main__":

    user_message = (
        "Multiply 17 by 23 plus 9"
    )

    final_answer = run_agent(
        user_message
    )

    print("\nFinal answer:")
    print(final_answer)