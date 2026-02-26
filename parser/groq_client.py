# parser/groq_client.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

def ask_groq(prompt, model = "llama-3.3-70b-versatile"):
    """
    Call Groq's chat completions endpoint.
    Default model is llama-3.1-8b-instant (fast, supported).
    """
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set in .env")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1024
    }

    response = requests.post(BASE_URL, json=payload, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Groq API Error: {response.text}")

    return response.json()["choices"][0]["message"]["content"]
