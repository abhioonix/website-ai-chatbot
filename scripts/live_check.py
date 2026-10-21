"""One-off live smoke test against the configured LLM provider.

Reads the API key from Intern_15_PJT/AAAAAapi.txt (never printed), lists the
models the key can see, picks a suitable chat model, and makes one real call.

Run:  python3 scripts/live_check.py
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

KEY_FILE = Path("/home/weirdvella/Intern_15_PJT/AAAAAapi.txt")
BASE = "https://api.groq.com/openai/v1"

# Preferred free-tier chat models, in order of preference.
PREFERRED = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
    "allam-2-7b",
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
]


def load_key() -> str:
    text = KEY_FILE.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"gsk_[A-Za-z0-9]{20,}", text)
    if not match:
        sys.exit("no gsk_ key found in " + str(KEY_FILE))
    return match.group(0)


def request(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {load_key()}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(errors="replace").strip()
        try:
            return exc.code, json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return exc.code, {"error": raw[:200] or f"HTTP {exc.code}"}


def main() -> None:
    status, data = request("GET", "/models")
    if status != 200:
        sys.exit(f"models request failed: HTTP {status} {data.get('error', '')}")
    available = {m["id"] for m in data.get("data", [])}
    print(f"models visible to key: {len(available)}")
    for mid in sorted(available):
        print(f"  - {mid}")

    chosen = next((m for m in PREFERRED if m in available), None)
    if chosen is None:
        chat_models = sorted(m for m in available if any(t in m for t in ("llama", "qwen", "oss", "kimi", "gemma")))
        chosen = chat_models[0] if chat_models else sorted(available)[0]
    print(f"using model: {chosen}")

    status, data = request(
        "POST",
        "/chat/completions",
        {
            "model": chosen,
            "messages": [
                {"role": "system", "content": "Reply in one short sentence."},
                {"role": "user", "content": "What is 2 + 2?"},
            ],
            "max_tokens": 64,
        },
    )
    if status != 200:
        sys.exit(f"chat failed: HTTP {status} {data.get('error', '')}")
    reply = data["choices"][0]["message"]["content"]
    print(f"reply: {reply.strip()[:200]}")
    print("LIVE TEST: OK")


if __name__ == "__main__":
    main()
