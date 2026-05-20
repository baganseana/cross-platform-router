# Cross-Platform Router (Claude Code plugin)

A Claude Code skill that routes each task to the best AI engine and runs it for you, returning the result inline:

| Task | Routed to |
|---|---|
| Deep research, multi-source synthesis, long docs | **Gemini** |
| General catch-all, a second opinion / different model's take | **ChatGPT (OpenAI)** |
| Autonomous multi-step "go do this" tasks | **Manus** |
| Everything else | **Claude** (stays put) |

It calls the real APIs (zero Python dependencies — stdlib only). If a key is missing or a call fails, it falls back to drafting a copy-paste-ready prompt for that tool's web app.

---

## Install

### Option A — as a plugin (recommended for teams)

1. Push this folder to a git repo (e.g. GitHub).
2. In Claude Code:
   ```
   /plugin marketplace add <your-git-repo-url>
   /plugin install cross-platform-router@cross-platform-router-marketplace
   ```
3. Set your API keys:
   ```
   bash "$(claude plugin path cross-platform-router)/setup_keys.sh"
   ```
   …or just run the `setup_keys.sh` from the installed plugin directory.

### Option B — as a personal skill (single machine)

```bash
cp -R plugins/cross-platform-router/skills/cross-platform-router ~/.claude/skills/
bash plugins/cross-platform-router/setup_keys.sh
```

---

## Get the API keys

| Engine | Where | Notes |
|---|---|---|
| **Gemini** | https://aistudio.google.com/apikey | Free tier covers `gemini-2.5-flash`. `gemini-2.5-pro` needs billing. |
| **OpenAI** | https://platform.openai.com/api-keys | Pay-as-you-go; add a few dollars of credit. Default model `gpt-4o`. |
| **Manus** | https://open.manus.ai (Settings → API) | Tasks run async; default profile `manus-1.6`. |

You don't need all three — any engine with a missing key just falls back to draft-and-paste; the others still run live.

Keys are stored only in your shell rc (`~/.zshrc`), never in this repo.

---

## Use it

Once installed, just talk naturally in Claude Code — the skill triggers on intent:

- *"Router: research the best email tools for creative agencies in 2026"* → Gemini
- *"Get ChatGPT's second opinion on this draft"* → ChatGPT
- *"Have Manus compile a list of 20 niche podcasts"* → Manus (returns a live task link + result)
- *"Research X with Gemini and also get ChatGPT's take"* → fans out and compares

## Scope

Skills run in **Claude Code** (CLI/desktop coding tool) — any project on a machine where they're installed. They do **not** run on claude.ai web or the mobile app (those can't reach local scripts/keys).
