#!/usr/bin/env python3
"""Sync the local shared MEMORY.md with the Cloudflare MCP server's memory store.

  push : local MEMORY.md  ->  server (overwrites server copy)
  pull : server           ->  local MEMORY.md (overwrites local copy)
  show : print the server's current memory

The server endpoint + secret come from $ROUTER_MCP_ADMIN_URL, e.g.
  https://cross-platform-router-mcp.<sub>.workers.dev/<SECRET>/admin/memory

Zero external dependencies (stdlib only).
"""
import argparse
import os
import sys
import urllib.error
import urllib.request

UA = "cross-platform-router-sync/1.0"


def memory_file() -> str:
    return os.environ.get(
        "ROUTER_MEMORY_FILE",
        os.path.expanduser("~/.claude/skills/cross-platform-router/MEMORY.md"),
    )


def admin_url() -> str:
    url = os.environ.get("ROUTER_MCP_ADMIN_URL")
    if not url:
        raise SystemExit(
            "[config] ROUTER_MCP_ADMIN_URL not set. Add to ~/.zshrc:\n"
            '  export ROUTER_MCP_ADMIN_URL="https://<worker>/<SECRET>/admin/memory"'
        )
    return url


def _req(method: str, data: bytes | None = None) -> str:
    req = urllib.request.Request(
        admin_url(),
        data=data,
        method=method,
        headers={"User-Agent": UA, "Content-Type": "text/markdown"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise SystemExit(f"[sync HTTP {e.code}] {e.read().decode('utf-8', 'replace')[:200]}")
    except urllib.error.URLError as e:
        raise SystemExit(f"[sync network error] {e.reason}")


def main() -> None:
    p = argparse.ArgumentParser(description="Sync shared memory with the MCP server.")
    p.add_argument("action", choices=["push", "pull", "show"])
    args = p.parse_args()

    if args.action == "push":
        with open(memory_file(), "rb") as f:
            body = f.read()
        _req("PUT", body)
        print(f"✓ pushed {len(body)} bytes from {memory_file()} -> server")
    elif args.action == "pull":
        text = _req("GET")
        with open(memory_file(), "w", encoding="utf-8") as f:
            f.write(text)
        print(f"✓ pulled {len(text)} bytes from server -> {memory_file()}")
    else:  # show
        sys.stdout.write(_req("GET"))


if __name__ == "__main__":
    main()
