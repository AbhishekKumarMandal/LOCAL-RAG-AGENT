import json
from urllib import request
from urllib.error import URLError, HTTPError

from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(
    "Qwen/Qwen2.5-3B-Instruct"
)

OLLAMA_URL = "http://localhost:11434/api/generate"

MODEL_NAME = "qwen2.5:3b-instruct"

def generate_text(
        prompt,
        temperature=0.2
        ):
    """
    Send a prompt to Ollama and return the generated response.

    Ollama is running locally on port 11434.
    """

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,

        # stream=False means:
        # wait for the complete response
        # and return it in one JSON object.
        "stream": False,

        # temperature:
        #         Lower value  -> more deterministic / focused
        #         Higher value -> more creative / varied
        "options": {
            "temperature": temperature
        }
    }

    request_body = json.dumps(payload).encode("utf-8")

    http_request = request.Request(
        OLLAMA_URL,
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with request.urlopen(http_request) as response:

            response_body = response.read()
            # print(f"\nresponse_body\n{response_body}\n")
            response_json = json.loads(response_body.decode("utf-8"))

        return response_json["response"]

    except HTTPError as error:
        raise RuntimeError(
            f"Ollama HTTP error: {error.code}"
        )

    except URLError as error:
        raise RuntimeError(
            "Could not connect to Ollama. "
            "Make sure Ollama is running."
        ) from error

if __name__ == "__main__":
    prompt = "Explain kafka in 2 simple sentences"
    answer = generate_text(prompt)
    print("prompt")
    print(prompt,"\n")
    print("answer")
    print(answer)

    print("\n\nDecoding response_body token present in context array")

    '''
    b'{"model":"qwen2.5:3b-instruct","created_at":"2026-09-26T01:55:33.883406Z","response":"Kafka is a high-throughput distributed streaming platform designed to handle high traffic, real-time data pipelines, and stream data processing.","done":true,"done_reason":"stop","context":[151644,8948,198,2610,525,1207,16948,11,3465,553,54364,14817,13,1446,525,264,10950,17847,13,151645,198,151644,872,198,840,20772,67852,304,220,17,4285,22870,151645,198,151644,77091,198,42,21883,374,264,1550,42747,628,4237,16842,5339,6188,311,3705,1550,9442,11,1931,7246,821,57673,11,323,4269,821,8692,13],"total_duration":2515257333,"load_duration":1820908750,"prompt_eval_count":37,"prompt_eval_cached_count":0,"prompt_eval_duration":129369000,"eval_count":27,"eval_duration":563433000}'
    '''

    context = [151644,8948,198,2610,525,1207,16948,11,3465,553,54364,14817,13,1446,525,264,10950,17847,13,151645,198,151644,872,198,840,20772,67852,304,220,17,4285,22870,151645,198,151644,77091,198,42,21883,374,264,1550,42747,628,4237,16842,5339,6188,311,3705,1550,9442,11,1931,7246,821,57673,11,323,4269,821,8692,13]
    
    tokens = tokenizer.convert_ids_to_tokens(context)

    for index, token in enumerate(tokens):
        print(index, token)

