import os
from typing import Dict

PROVIDER = os.getenv("LLM_PROVIDER", "openrouter").lower()

HEALTH_GUIDE = "Summarize for a general audience. Cover key findings, who/what, evidence level, risks, and timeline.\n\n"
TECH_GUIDE   = "Summarize clearly. Cover what's new, why it matters, who is affected, numbers, and timeline.\n\n"

def summarize_item(item: Dict) -> Dict:
    text  = (item.get("cleaned_text") or "").strip()
    title = item.get("title", "")
    theme = item.get("theme", "tech")
    if not text:
        return {**item, "summary": ""}

    guide  = HEALTH_GUIDE if theme == "health" else TECH_GUIDE
    prompt = f"{guide}TITLE: {title}\n\nARTICLE:\n{text[:6000]}"

    try:
        if PROVIDER == "openrouter":
            from src.llm.openrouter_adapter import summarize_openrouter
            summary = summarize_openrouter(prompt)
        else:
            summary = "(no provider configured)"
    except Exception as e:
        summary = f"(summarizer_error: {e})"

    return {**item, "summary": summary}
