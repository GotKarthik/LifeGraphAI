import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
try:
    models = client.models.list()
    for m in models:
        print(m.id)
except Exception as e:
    print("Error:", e)
