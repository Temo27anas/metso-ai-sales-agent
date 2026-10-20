import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
response = client.responses.create(model="gpt-4o-mini", input="Hello")
print(response.output_text)
