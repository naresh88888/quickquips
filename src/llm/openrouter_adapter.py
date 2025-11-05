# src/llm/openrouter_adapter.py
import os, requests

OR_KEY   = os.getenv("OPENROUTER_API_KEY")
OR_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")

def summarize_openrouter(prompt: str, max_tokens: int = 160) -> str:
    """Send summarization prompt to OpenRouter model."""
    headers = {
        "Authorization": f"Bearer {OR_KEY}",
        "HTTP-Referer": "https://github.com/yourusername/insightpilot",  # optional
        "X-Title": "InsightPilot AI",
        "Content-Type": "application/json"
    }

    payload = {
        "model": OR_MODEL,
        "messages": [
            {"role": "system",
             "content": "You are an AI journalist. Summarize news clearly, factually, and concisely in about 120 words."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }

    r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                      headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"].strip()
