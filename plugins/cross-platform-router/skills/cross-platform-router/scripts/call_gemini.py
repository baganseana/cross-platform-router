#!/usr/bin/env python3
"""Call Google Gemini. Used by the cross-platform-router skill for research tasks.

Usage:
    python3 call_gemini.py "your prompt here"
    python3 call_gemini.py --model gemini-2.5-pro "your prompt"
    echo "long prompt" | python3 call_gemini.py -

Reads GEMINI_API_KEY from the environment. Zero external dependencies (stdlib only).
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

from _memory import wrap_with_memory

DEFAULT_MODEL = "gemini-2.5-flash"  # free-tier friendly. Use --model gemini-2.5-pro w/ billing.
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def call_gemini(prompt: str, model: str, api_key: str) -> str:
    url = f"{API_BASE}/{model}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        raise SystemExit(f"[Gemini HTTP {e.code}] {detail}")
    except urllib.error.URLError as e:
        raise SystemExit(f"[Gemini network error] {e.reason}")

    try:
        return body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        # Surface blocks/safety/errors verbatim so the router can react.
        return json.dumps(body, indent=2)


def main() -> None:
    p = argparse.ArgumentParser(description="Call Google Gemini.")
    p.add_argument("prompt", help="Prompt text, or '-' to read from stdin")
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"Default: {DEFAULT_MODEL}")
    p.add_argument("--no-memory", action="store_true", help="Don't inject shared memory")
    args = p.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("[config] GEMINI_API_KEY not set. Add it to ~/.zshrc.")

    prompt = sys.stdin.read() if args.prompt == "-" else args.prompt
    if not prompt.strip():
        raise SystemExit("[input] Empty prompt.")

    prompt = wrap_with_memory(prompt, enabled=not args.no_memory)
    print(call_gemini(prompt, args.model, api_key))


if __name__ == "__main__":
    main()
