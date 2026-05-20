#!/usr/bin/env python3
"""Call Manus for autonomous multi-step tasks. Used by the cross-platform-router skill.

Manus runs tasks ASYNCHRONOUSLY: we create a task, then poll task.listMessages until the
agent stops. API contract verified against https://open.manus.ai/docs/v2 (May 2026).

  Create:  POST https://api.manus.ai/v2/task.create   header x-manus-api-key
           body {"message": {"content": "..."}, "agent_profile": "..."}
           -> {"ok", "task_id", "task_url", ...}
  Poll:    GET  https://api.manus.ai/v2/task.listMessages?task_id=...&order=asc&limit=100
           -> {"messages": [TaskEvent...]}   done when status_update.agent_status == "stopped"

Usage:
    python3 call_manus.py "your task"                 # create + wait for result
    python3 call_manus.py --no-wait "your task"       # create, print task_id+url, exit
    python3 call_manus.py --poll <task_id>            # resume polling an existing task
    echo "long task" | python3 call_manus.py -
    python3 call_manus.py --timeout 480 "your task"   # wait up to 8 min (default 240s)

Reads MANUS_API_KEY from the environment. Zero external dependencies (stdlib only).
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

API_BASE = "https://api.manus.ai/v2"
DEFAULT_PROFILE = "manus-1.6"  # also: manus-1.6-lite (cheap/fast), manus-1.6-max (best)


def _request(method: str, path: str, api_key: str, body: dict | None = None, timeout: int = 60) -> dict:
    url = f"{API_BASE}/{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"x-manus-api-key": api_key}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        raise SystemExit(f"[Manus HTTP {e.code}] {detail}")
    except urllib.error.URLError as e:
        raise SystemExit(f"[Manus network error] {e.reason}")


def create_task(prompt: str, profile: str, api_key: str) -> dict:
    body = {"message": {"content": prompt}, "agent_profile": profile}
    return _request("POST", "task.create", api_key, body)


def poll_task(task_id: str, api_key: str, timeout: int, interval: int) -> str:
    """Poll until the agent stops/errors/waits or we time out. Returns assistant output text."""
    deadline = time.time() + timeout
    while True:
        resp = _request(
            "GET",
            f"task.listMessages?task_id={task_id}&order=asc&limit=100&verbose=false",
            api_key,
        )
        events = resp.get("messages", [])
        assistant_parts, latest_status, error_text, waiting_desc = [], None, None, None
        for ev in events:
            t = ev.get("type")
            if t == "assistant_message":
                c = (ev.get("assistant_message") or {}).get("content")
                if c:
                    assistant_parts.append(c)
            elif t == "error_message":
                error_text = (ev.get("error_message") or {}).get("content") or "unknown error"
            elif t == "status_update":
                su = ev.get("status_update") or {}
                latest_status = su.get("agent_status")
                if latest_status == "waiting":
                    waiting_desc = (su.get("status_detail") or {}).get(
                        "waiting_description", "agent needs confirmation"
                    )

        if latest_status == "stopped":
            return "\n\n".join(assistant_parts) if assistant_parts else "[Manus finished with no text output]"
        if latest_status == "error" or error_text:
            raise SystemExit(f"[Manus task error] {error_text or 'agent entered error state'}")
        if latest_status == "waiting":
            return (
                f"[Manus paused — needs confirmation] {waiting_desc}\n"
                f"Open the task to confirm/continue."
            )
        if time.time() >= deadline:
            return (
                "[Manus still running — polling timed out]\n"
                f"Resume with: python3 {sys.argv[0]} --poll {task_id}"
            )
        time.sleep(interval)


def main() -> None:
    p = argparse.ArgumentParser(description="Call Manus (async autonomous tasks).")
    p.add_argument("prompt", nargs="?", help="Task text, or '-' for stdin. Omit when using --poll.")
    p.add_argument("--no-wait", action="store_true", help="Create task and exit without polling")
    p.add_argument("--poll", metavar="TASK_ID", help="Resume polling an existing task")
    p.add_argument("--timeout", type=int, default=240, help="Max seconds to poll (default 240)")
    p.add_argument("--interval", type=int, default=5, help="Poll interval seconds (default 5)")
    p.add_argument("--profile", default=DEFAULT_PROFILE, help=f"agent_profile (default {DEFAULT_PROFILE})")
    args = p.parse_args()

    api_key = os.environ.get("MANUS_API_KEY")
    if not api_key:
        sys.stderr.write("[not-configured] MANUS_API_KEY not set. Use draft-and-paste fallback.\n")
        raise SystemExit(2)

    # Resume-poll mode.
    if args.poll:
        print(poll_task(args.poll, api_key, args.timeout, args.interval))
        return

    if not args.prompt:
        raise SystemExit("[input] Provide a task prompt, or use --poll <task_id>.")
    prompt = sys.stdin.read() if args.prompt == "-" else args.prompt
    if not prompt.strip():
        raise SystemExit("[input] Empty prompt.")

    created = create_task(prompt, args.profile, api_key)
    task_id = created.get("task_id", "")
    task_url = created.get("task_url", "")
    sys.stderr.write(f"[Manus] task created: {task_id}\n[Manus] watch live: {task_url}\n")

    if args.no_wait:
        print(json.dumps({"task_id": task_id, "task_url": task_url}, indent=2))
        return

    result = poll_task(task_id, api_key, args.timeout, args.interval)
    print(result)
    if task_url:
        sys.stderr.write(f"\n[Manus] full task: {task_url}\n")


if __name__ == "__main__":
    main()
