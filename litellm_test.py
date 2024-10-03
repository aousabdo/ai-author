
from litellm import completion
import os

## set ENV variables
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

os.environ["COHERE_API_KEY"] = os.getenv("COHERE_API_KEY")
messages = [{ "content": "Hello, how are you?","role": "user"}]

# openai call
response = completion(model="gpt-4o-mini", messages=messages)

# anthropic call
# response = completion(model="command-nightly", messages=messages)
print(response)