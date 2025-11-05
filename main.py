# main.py — QuickQuips pipeline runner
# Collects articles per theme, summarizes via your summarizer, appends to data/articles.jsonl

from src.ingest.load_sources import load_sources
from src.ingest.fetch import collect_from_feeds
from src.summarize.summarizer import summarize_item
from src.storage.io import append_jsonl

import os
import json
import pathlib
from typing import List, Dict, Any, Optional

ROOT = pathlib.Path(__file__).resolve().parent
CONFIG_FEEDS = ROOT / "config" / "feeds.json"

def read_feeds_config() -> Dict[str, List[str]]:
    """
    Load feed URLs from config/feeds.json if present.
    Falls back to load_sources() if not.
    """
    if CONFIG_FEEDS.exists():
        try:
            return json.loads(CONFIG_FEEDS.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[WARN] Failed to parse {CONFIG_FEEDS}: {e}. Falling back to load_sources().")
    # fallback to legacy loader
    try:
        return load_sources()  # must return {theme: [urls]}
    except Exception as e:
        print(f"[ERROR] load_sources() failed: {e}")
        return {}

def dedupe_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate by (url, title) to avoid double work/appends."""
    seen = set()
    out = []
    for it in items:
        url = (it.get("url") or "").strip()
        title = (it.get("title") or "").strip()
        key = (url, title)
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out

def run_theme(theme: str, feed_urls: Optional[List[str]] = None, limit_sources: Optional[int] = None) -> int:
    """
    Run one theme end-to-end.
    - If feed_urls is None, tries to pull from config/load_sources().
    - limit_sources caps the number of feeds for this theme (useful while testing).
    Returns number of summarized items appended.
    """
    if feed_urls is None:
        all_map = read_feeds_config()
        feed_urls = all_map.get(theme, [])

    if limit_sources:
        feed_urls = feed_urls[:limit_sources]

    print(f"[{theme.upper()}] collecting from {len(feed_urls)} feeds...")
    if not feed_urls:
        print(f"[{theme.upper()}] no feeds configured. Skipping.")
        return 0

    items = collect_from_feeds(feed_urls, theme=theme)
    print(f"[{theme.upper()}] fetched & cleaned: {len(items)}")

    items = dedupe_items(items)
    print(f"[{theme.upper()}] after dedupe: {len(items)}")

    summarized = []
    for it in items:
        try:
            summarized.append(summarize_item(it))
        except Exception as e:
            # keep going even if one item fails
            title = (it.get("title") or "")[:80]
            print(f"[{theme.upper()}] summarize failed for: {title} :: {e}")

    if summarized:
        append_jsonl(summarized)
    print(f"[{theme.upper()}] stored {len(summarized)} items.\n")
    return len(summarized)

def main():
    # --- config knobs ---
    # THEMES: comma-separated list; if not set, run everything in feeds.json
    env_themes = os.getenv("THEMES", "").strip()
    # Limit feeds PER THEME during testing to control cost/time
    limit_sources = int(os.getenv("LIMIT_SOURCES", "2"))

    feeds_map = read_feeds_config()
    if not feeds_map:
        print("[ERROR] No feeds found. Create config/feeds.json or fix load_sources().")
        return

    if env_themes:
        themes = [t.strip().lower() for t in env_themes.split(",") if t.strip()]
        # keep only those present in config
        themes = [t for t in themes if t in feeds_map]
        if not themes:
            print("[WARN] THEMES env provided but none matched config. Running all themes.")
            themes = list(feeds_map.keys())
    else:
        themes = list(feeds_map.keys())

    print(f"[RUN] Themes: {themes}  |  LIMIT_SOURCES={limit_sources}")

    total = 0
    for theme in themes:
        total += run_theme(theme=theme, feed_urls=feeds_map.get(theme, []), limit_sources=limit_sources)

    print(f"[DONE] Appended summaries for {total} items. See data/articles.jsonl")

if __name__ == "__main__":
    main()
