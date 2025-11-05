# src/ingest/fetch.py  (replace your function’s internals with this approach)
import time
import feedparser
import requests
from urllib.parse import urlparse
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

try:
    import trafilatura
except Exception:
    trafilatura = None

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/123.0 Safari/537.36")

def _download(url: str, timeout: int = 15) -> Optional[str]:
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
        if r.status_code == 200 and r.text:
            return r.text
    except Exception:
        pass
    return None

def _extract_text(url: str) -> str:
    # Try full-text via Trafilatura
    if trafilatura:
        html = _download(url)
        if html:
            txt = trafilatura.extract(html, include_comments=False, favor_recall=False)
            if txt and len(txt.strip()) > 300:  # require some substance
                return txt.strip()
    return ""

def _coerce_date(entry) -> Optional[str]:
    # Try multiple date fields → ISO string
    for key in ("published_parsed", "updated_parsed"):
        dt = getattr(entry, key, None) or entry.get(key)
        if dt:
            try:
                return datetime(*dt[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                pass
    for key in ("published", "updated"):
        raw = entry.get(key)
        if raw:
            try:
                # let pandas parse later if not strict ISO
                return str(raw)
            except Exception:
                pass
    return None

def collect_from_feeds(feed_urls: List[str], theme: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for feed_url in feed_urls:
        try:
            # Parse RSS with UA (feedparser uses urllib by default; set global UA)
            feedparser.USER_AGENT = UA
            fp = feedparser.parse(feed_url)
            if fp.bozo:
                # Sometimes downloading manually then parsing helps
                raw = _download(feed_url)
                if raw:
                    fp = feedparser.parse(raw)

            for entry in fp.entries[:30]:  # safety cap
                title = (entry.get("title") or "").strip()
                link = (entry.get("link") or "").strip()
                if not link or not title:
                    continue

                published = _coerce_date(entry)

                # Try full-text extraction, else fallback to summary/description
                fulltext = _extract_text(link)
                if not fulltext:
                    # fallback: use summary/description from RSS
                    fallback = (entry.get("summary") or entry.get("description") or "").strip()
                    # keep only if we have something decent
                    if len(fallback) < 120:
                        continue
                    cleaned_text = fallback
                else:
                    cleaned_text = fulltext

                items.append({
                    "theme": theme,
                    "title": title[:240],
                    "url": link,
                    "published": published,
                    "cleaned_text": cleaned_text
                })
            time.sleep(0.6)  # be polite between feeds
        except Exception as e:
            print(f"[WARN] feed failed: {feed_url} :: {e}")
            continue
    return items
