#!/usr/bin/env python3
"""Call OpenAI (ChatGPT). Used by the cross-platform-router skill as the general/catch-all engine.

Usage:
    python3 call_openai.py "your prompt here"
    python3 call_openai.py --model gpt-4o "your prompt"
    echo "long prompt" | python3 call_openai.py -

Reads OPENAI_API_KEY from the environment. Zero external dependencies (stdlib only).
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_MODEL = "gpt-4o"  # override with --model (e.g. gpt-4o-mini for cheap, or a newer model)
API_URL = "https://api.openai.com/v1/chat/completions"


def call_openai(prompt: str, model: str, api_key: str) -> str:
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        raise SystemExit(f"[OpenAI HTTP {e.code}] {detail}")
    except urllib.error.URLError as e:
        raise SystemExit(f"[OpenAI network error] {e.reason}")

    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return json.dumps(body, indent=2)


def main() -> None:
    p = argparse.ArgumentParser(description="Call OpenAI ChatGPT.")
    p.add_argument("prompt", help="Prompt text, or '-' to read from stdin")
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"Default: {DEFAULT_MODEL}")
    args = p.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("[config] OPENAI_API_KEY not set. Add it to ~/.zshrc.")

    prompt = sys.stdin.read() if args.prompt == "-" else args.prompt
    if not prompt.strip():
        raise SystemExit("[input] Empty prompt.")

    print(call_openai(prompt, args.model, api_key))


if __name__ == "__main__":
    main()
