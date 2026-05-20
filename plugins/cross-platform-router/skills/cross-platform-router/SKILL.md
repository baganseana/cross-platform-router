---
name: cross-platform-router
description: Routes a task to the best AI engine — Claude (stay), Gemini (research/synthesis), ChatGPT/OpenAI (general catch-all & second opinions), or Manus (autonomous multi-step tasks). Use when the user asks to "use the router", "channel ChatGPT/Gemini/Manus", asks "which AI should handle this", wants a second opinion from another model, asks for deep research, or asks for an autonomous multi-step task. Tries the real API first and falls back to drafting a paste-ready prompt.
---

# Cross-Platform Router

Pick the right AI engine for the task, run it (or draft a prompt to paste), and return the result. The user drives everything from inside Claude.

## Routing rules

| Route to | When the task is… | Engine |
|---|---|---|
| **Claude (stay)** | Coding, writing, editing, brainstorming, reasoning over the current conversation/files, anything already in flight | (no script — just answer) |
| **Gemini** | Deep research, multi-source synthesis, summarizing long documents, "look into / investigate / compare" questions | `call_gemini.py` |
| **ChatGPT (OpenAI)** | General catch-all, a different model's take, a second opinion, or when the user explicitly asks for ChatGPT | `call_openai.py` |
| **Manus** | Autonomous multi-step execution — "go do this," agentic web tasks, long task chains | `call_manus.py` |

**Default to staying in Claude** unless the task clearly matches Gemini, ChatGPT, or Manus, OR the user explicitly names a tool. When unsure between two, briefly state your pick and why in one line, then proceed.

## How to run each engine

Scripts live in this skill's `scripts/` folder and read their key from the environment. They have **zero dependencies** (Python stdlib only). Run with the Bash tool. The skill directory is referenced below as `$DIR` — resolve it to `${CLAUDE_PLUGIN_ROOT}/skills/cross-platform-router/scripts` when installed as a plugin, or `~/.claude/skills/cross-platform-router/scripts` when installed as a personal skill.

```bash
DIR="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude}/skills/cross-platform-router/scripts"
# (If CLAUDE_PLUGIN_ROOT is unset and this is a personal skill, use: DIR="$HOME/.claude/skills/cross-platform-router/scripts")

# Gemini (research) — defaults to gemini-2.5-flash (free tier)
python3 "$DIR/call_gemini.py" "PROMPT"
python3 "$DIR/call_gemini.py" --model gemini-2.5-pro "PROMPT"   # stronger; needs billing

# ChatGPT (catch-all / second opinion)
python3 "$DIR/call_openai.py" "PROMPT"

# Manus (autonomous tasks) — ASYNC: creates a task, polls, returns the result.
# Tasks can take minutes. Run via Bash with a generous timeout (e.g. 300000 ms).
python3 "$DIR/call_manus.py" "PROMPT"
python3 "$DIR/call_manus.py" --no-wait "PROMPT"   # create only, get task_url
python3 "$DIR/call_manus.py" --poll <task_id>      # resume polling later
python3 "$DIR/call_manus.py" --timeout 480 "PROMPT" # wait up to 8 min
# Profiles: manus-1.6 (default), manus-1.6-lite (fast/cheap), manus-1.6-max (best) via --profile
```

**Manus specifics:** It's autonomous and async. For long tasks, prefer `--no-wait` to grab the
`task_url` immediately and share it with the user, then `--poll <task_id>` to fetch the result.
If a task returns "[Manus paused — needs confirmation]", the agent hit an action needing approval
(e.g. sending email) — point the user to the task_url to confirm. Always give the Bash call a
timeout ≥ the script's `--timeout`.

For long prompts, pipe via stdin to avoid shell-quoting headaches:
```bash
python3 "$DIR/call_gemini.py" - <<'PROMPT'
multi-line
prompt here
PROMPT
```

## Execution mode: API first, draft-and-paste fallback

For any non-Claude route:

1. **Optimize the prompt** for the target engine (see below).
2. **Try the API.** Run the script.
3. **On success:** present the result inline. Lead with one line naming the engine, e.g. *"Gemini's answer:"*. Then add your own brief take if it helps.
4. **On failure** (missing key, Manus exit code **2** = not configured, or any HTTP error): **fall back to draft-and-paste.** Don't silently retry. Output: which engine, a copy-paste-ready prompt in a code block, where to paste it (aistudio.google.com / chatgpt.com / manus.im), and an offer to process the pasted-back output.

## Prompt optimization per engine

- **Gemini (research):** ask for structured output with sources/citations, a brief executive summary up top, and specify recency if relevant.
- **ChatGPT:** state role + goal + constraints + desired format concisely.
- **Manus:** give a clear objective, success criteria, constraints/credentials it may need, and the deliverable format. Be explicit about scope and stopping conditions.

## Required environment variables

This skill needs API keys in the environment (e.g. in `~/.zshrc`). Run `setup_keys.sh` (in the plugin root) once to set them, or add manually:

- `GEMINI_API_KEY` — Google AI Studio (aistudio.google.com/apikey). Free tier: use `gemini-2.5-flash` (default); `gemini-2.5-pro` needs billing.
- `OPENAI_API_KEY` — platform.openai.com/api-keys. Default model `gpt-4o`.
- `MANUS_API_KEY` — open.manus.ai (Settings → API). Async create+poll; default profile `manus-1.6`.

**These must be the current user's OWN keys.** This skill never ships with keys — it reads them only from the local environment. Each person who installs it supplies their own.

### First-run / missing-key behavior (IMPORTANT)

Before routing to an engine, assume the key may not be set yet. When a script returns `[config] ... not set` or `[not-configured]` (exit code 2), do NOT silently fall back. Instead, **stop and prompt the user to set up their own key**:

1. Tell them which key is missing and that it must be *their own* account's key (they cannot use anyone else's).
2. Offer to run the setup helper for them:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/skills/cross-platform-router}/setup_keys.sh"
   ```
   (or, if installed as a personal skill, the `setup_keys.sh` in the plugin root)
3. Point them to where to get the key: Gemini → aistudio.google.com/apikey · OpenAI → platform.openai.com/api-keys · Manus → open.manus.ai (Settings → API).
4. Only after they decline setup, offer the draft-and-paste fallback as a stopgap.

If a key is genuinely absent and the user doesn't want to add it, that engine falls back to draft-and-paste mode — the others still work.
