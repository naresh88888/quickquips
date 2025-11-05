import yaml
from pathlib import Path

def load_sources(path: str = "src/ingest/rss_sources.yaml"):
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return data  # dict with keys "health", "tech"
