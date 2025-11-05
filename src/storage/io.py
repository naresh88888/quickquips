import json
from pathlib import Path
from typing import Iterable, Dict

DATA_DIR = Path("data")
ARTICLES_PATH = DATA_DIR / "articles.jsonl"

def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def append_jsonl(records: Iterable[Dict], path: Path = ARTICLES_PATH):
    ensure_dirs()
    with path.open("a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def read_jsonl(path: Path = ARTICLES_PATH):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
