# src/llm/hf_adapter.py
import os, time, requests
from typing import List

HF_API_KEY   = os.getenv("HF_API_KEY")
HF_SUM_MODEL = os.getenv("HF_SUM_MODEL", "Falconsai/text_summarization")
HF_URL       = f"https://api-inference.huggingface.co/models/{HF_SUM_MODEL}"
HF_HEADERS   = {"Authorization": f"Bearer {HF_API_KEY}"}

# ---- simple chunker to handle long articles ----
def _chunk(text: str, max_chars: int = 2500) -> List[str]:
    text = text.strip()
    if len(text) <= max_chars:
        return [text]
    chunks, start = [], 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        # try to cut at sentence boundary
        cut = text.rfind(".", start, end)
        if cut == -1: cut = end
        chunks.append(text[start:cut].strip())
        start = cut + 1
    return chunks

def _hf_summarize_once(txt: str, max_new_tokens: int = 140, retries: int = 3) -> str:
    payload = {
        "inputs": txt,
        "parameters": {"max_new_tokens": max_new_tokens, "return_full_text": False}
    }
    backoff = 2
    for _ in range(retries):
        r = requests.post(HF_URL, headers=HF_HEADERS, json=payload, timeout=60)
        # cold start / loading state returns 503 with "loading" — wait and retry
        if r.status_code in (503, 524):
            time.sleep(backoff); backoff *= 2; continue
        r.raise_for_status()
        data = r.json()
        # HF summarization returns [{"summary_text": "..."}]
        if isinstance(data, list) and data and "summary_text" in data[0]:
            return data[0]["summary_text"].strip()
        # some models return plain string
        if isinstance(data, str):
            return data.strip()
        # unexpected shape
        return str(data)
    return "(summary unavailable: HF endpoint busy)"

def summarize_long_text(text: str) -> str:
    """Map-reduce style: summarize chunks, then summarize the combined."""
    chunks = _chunk(text, max_chars=2500)
    partials = [_hf_summarize_once(c, max_new_tokens=120) for c in chunks[:6]]  # cap chunks
    combined = "\n".join(partials)
    final = _hf_summarize_once(combined, max_new_tokens=140)
    return final
