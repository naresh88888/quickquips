# clean_articles.py
import json, pathlib

path = pathlib.Path("data/articles.jsonl")
cleaned = []
for line in path.read_text(encoding="utf-8").splitlines():
    if not line.strip(): continue
    obj = json.loads(line)
    s = str(obj.get("summary","")).lower()
    if "summarizer_error" in s or "client error" in s:
        continue
    cleaned.append(obj)

out = path.with_name("articles_clean.jsonl")
with out.open("w", encoding="utf-8") as f:
    for obj in cleaned:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

print(f"✅ Cleaned file saved as {out}, kept {len(cleaned)} items")
