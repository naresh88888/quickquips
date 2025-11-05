# app.py — QuickQuips (Filters Always Visible)
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="QuickQuips — Smart AI News Feed", page_icon="⚡", layout="wide")

# ---------- LOAD DATA ----------
DATA_PATH = Path(__file__).resolve().parent / "data" / "articles.jsonl"
# st.write("🔎 Loading from:", str(DATA_PATH))  # debug

if not DATA_PATH.exists():
    st.error("Couldn't find data/articles.jsonl — run main.py first.")
    st.stop()

rows = []
with DATA_PATH.open("r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception as e:
            st.warning(f"Skipped a malformed line: {e}")

df = pd.DataFrame(rows)
if df.empty:
    st.warning("The JSONL loaded but no rows found.")
    st.stop()

# Ensure expected columns exist
if "theme" not in df.columns:
    # try to map from other field names if your pipeline used something else
    if "category" in df.columns:
        df["theme"] = df["category"]
    else:
        df["theme"] = "unknown"

if "title" not in df.columns:
    df["title"] = ""
if "summary" not in df.columns:
    df["summary"] = df.get("cleaned_text", "")
if "url" not in df.columns:
    df["url"] = ""
if "published" not in df.columns:
    df["published"] = None

df["published"] = pd.to_datetime(df["published"], errors="coerce")
df["theme"] = df["theme"].astype(str).str.strip()
# st.write("✅ Rows loaded:", len(df))  # debug
# st.write("✅ Unique themes in data:", sorted(df["theme"].str.lower().unique().tolist()))  # debug

st.title("⚡ QuickQuips — Smart AI News Feed")
st.caption("Built by Naresh · Read less, know more.")

# ---------- FILTERS (SIDEBAR) ----------
st.sidebar.header("Filters")
all_themes = ["health","tech","sports","finance","immigration","politics","weather"]

themes_in_df = sorted(set(all_themes) & set(df["theme"].str.lower()))
if not themes_in_df:
    # If none of the preferred themes are present, fall back to what's in the file
    themes_in_df = sorted(df["theme"].str.lower().unique().tolist())

selected_themes = st.sidebar.multiselect(
    "Theme",
    options=sorted(set(all_themes) | set(themes_in_df)),  # union for safety
    default=themes_in_df
)

search = st.sidebar.text_input("Search (title or summary)")
date_filter_on = st.sidebar.checkbox("Filter by date range", value=False)
if date_filter_on and df["published"].notna().any():
    min_d, max_d = df["published"].min(), df["published"].max()
    date_range = st.sidebar.date_input("Published date range", [min_d, max_d])
else:
    date_range = None

# ---------- APPLY FILTERS ----------
view = df.copy()

if selected_themes:
    view = view[view["theme"].str.lower().isin([t.lower() for t in selected_themes])]

if search:
    s = search.lower()
    view = view[
        view["title"].astype(str).str.lower().str.contains(s, na=False) |
        view["summary"].astype(str).str.lower().str.contains(s, na=False)
    ]

if date_filter_on and date_range and len(date_range) == 2 and df["published"].notna().any():
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    view = view[(view["published"].isna()) | ((view["published"] >= start) & (view["published"] <= end))]

# ---------- RENDER FEED ----------
view = view.sort_values(by="published", ascending=False, na_position="last")
st.markdown(f"### Showing {len(view)} article(s)")

ICONS = {
    "health": "💊", "tech": "💻", "sports": "⚽", "finance": "💹",
    "immigration": "🛂", "politics": "🏛️", "weather": "🌦️"
}

for _, row in view.iterrows():
    theme = str(row.get("theme", "unknown"))
    icon = ICONS.get(theme.lower(), "🗞️")
    title = str(row.get("title", "Untitled")).strip() or "Untitled"

    st.markdown(f"### {icon} {title}")

    if pd.notnull(row.get("published")):
        try:
            st.caption(f"🗓️ {row['published'].strftime('%d %b %Y')} | 🏷️ {theme.title()}")
        except Exception:
            st.caption(f"🏷️ {theme.title()}")

    # NEW badge (today)
    today = datetime.today().date()
    if pd.notnull(row.get("published")) and row["published"].date() == today:
        st.markdown(
            "<span style='background:#22d3ee22;color:#22d3ee;"
            "padding:2px 8px;border-radius:8px;font-size:12px;'>NEW</span>",
            unsafe_allow_html=True
        )

    summary = str(row.get("summary", "")).strip()
    st.write(summary if summary else "_No summary available._")

    url = str(row.get("url", "")).strip()
    if url:
        st.markdown(f"[🔗 Read Full Article]({url})")
    st.divider()
