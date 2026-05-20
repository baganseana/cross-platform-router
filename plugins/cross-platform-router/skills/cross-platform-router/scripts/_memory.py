"""Shared-memory helper for the cross-platform-router scripts.

Loads the shared MEMORY.md and wraps a prompt so every engine (Gemini, ChatGPT,
Manus) receives the same context — making them all act "on the same page".

Resolution order for the memory file:
  1. $ROUTER_MEMORY_FILE if set
  2. ~/.claude/skills/cross-platform-router/MEMORY.md (personal skill)
  3. $CLAUDE_PLUGIN_ROOT/skills/cross-platform-router/MEMORY.md (plugin install)
"""
import os

_PREAMBLE_HEADER = (
    "[SHARED MEMORY — persistent context that Claude, Gemini, ChatGPT and Manus all share. "
    "Treat it as background truth. Apply it; do not repeat it back unless asked.]"
)
_PREAMBLE_FOOTER = "[END SHARED MEMORY]"


def _candidate_paths():
    env = os.environ.get("ROUTER_MEMORY_FILE")
    if env:
        yield env
    home = os.path.expanduser("~")
    yield os.path.join(home, ".claude", "skills", "cross-platform-router", "MEMORY.md")
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if plugin_root:
        yield os.path.join(plugin_root, "skills", "cross-platform-router", "MEMORY.md")
    # Sibling of this script (scripts/ -> ../MEMORY.md)
    yield os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "MEMORY.md")


def load_memory() -> str:
    """Return the memory text (comments stripped), or '' if none found/empty."""
    for path in _candidate_paths():
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read()
        except (OSError, TypeError):
            continue
        # Strip the leading HTML comment block if present.
        if "-->" in raw:
            raw = raw.split("-->", 1)[1]
        text = raw.strip()
        if text:
            return text
    return ""


def wrap_with_memory(prompt: str, enabled: bool = True) -> str:
    """Prepend shared memory to a prompt. No-op if disabled or memory is empty."""
    if not enabled:
        return prompt
    mem = load_memory()
    if not mem:
        return prompt
    return f"{_PREAMBLE_HEADER}\n{mem}\n{_PREAMBLE_FOOTER}\n\n{prompt}"
