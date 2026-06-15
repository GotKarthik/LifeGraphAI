import os
from openai import OpenAI
from core.config import settings

client = OpenAI(api_key=settings.GEMINI_API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
models = client.models.list()
for m in models.data:
    if "flash" in m.id.lower():
        print(m.id)
