from transformers import AutoTokenizer

MODEL_NAME = "BAAI/bge-small-en-v1.5"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
text = "Java is a programming language"

tokens = tokenizer.tokenize(text)
token_ids = tokenizer.encode(text)

print("Original text:")
print(text)

print("\nTokens:")
print(tokens)

print("\nToken IDs:")
print(token_ids)