from pathlib import Path
from dotenv import load_dotenv
import os, requests

ROOT = Path(__file__).resolve().parent
load_dotenv(dotenv_path=ROOT / ".env", override=True)

key = (os.getenv("HF_API_KEY") or "").strip()
print("Key loaded?", bool(key), "len:", len(key))

headers = {"Authorization": f"Bearer {key}"}
r = requests.get(
    "https://api-inference.huggingface.co/status/sshleifer/distilbart-cnn-12-6",
    headers=headers, timeout=30
)
print("Status:", r.status_code)
print("Body:", r.text[:200])
