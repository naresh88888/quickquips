# check_counts.py
import json, collections, pathlib
p = pathlib.Path("data/articles.jsonl")
counts = collections.Counter()
n=0
for line in p.read_text(encoding="utf-8").splitlines():
    if not line.strip(): continue
    try:
        obj = json.loads(line)
        counts[str(obj.get("theme","unknown")).lower()] += 1
        n+=1
    except: pass

print("Total rows:", n)
for k,v in counts.most_common():
    print(f"{k}: {v}")
