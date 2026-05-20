#!/usr/bin/env bash
# Interactive, idempotent setup for the cross-platform-router skill.
# Adds GEMINI_API_KEY / OPENAI_API_KEY / MANUS_API_KEY to your shell rc file.
# Safe to re-run: it updates existing lines instead of duplicating them.
# No keys are stored in this repo — they live only in your shell rc.

set -euo pipefail

# Pick the right rc file for the current shell.
if [ -n "${ZSH_VERSION:-}" ] || [ "$(basename "${SHELL:-}")" = "zsh" ]; then
  RC="$HOME/.zshrc"
else
  RC="$HOME/.bashrc"
fi
touch "$RC"

set_key() {
  local name="$1" prompt="$2" current val
  current="$(grep -E "^export ${name}=" "$RC" | tail -1 | sed -E "s/^export ${name}=\"?([^\"]*)\"?$/\1/" || true)"
  if [ -n "$current" ]; then
    printf "  %s already set (%s…). Keep it? [Y/n] " "$name" "${current:0:6}"
    read -r keep
    [ "${keep:-Y}" = "n" ] || [ "${keep:-Y}" = "N" ] || return 0
  fi
  printf "  Enter %s (%s), or blank to skip: " "$name" "$prompt"
  read -r val
  [ -z "$val" ] && { echo "    skipped $name"; return 0; }
  # Remove any existing line, then append the new one.
  grep -v -E "^export ${name}=" "$RC" > "$RC.tmp" && mv "$RC.tmp" "$RC"
  printf 'export %s="%s"\n' "$name" "$val" >> "$RC"
  echo "    set $name"
}

echo "Cross-Platform Router — API key setup"
echo "Keys are written to: $RC"
echo
echo "Get keys here:"
echo "  Gemini : https://aistudio.google.com/apikey"
echo "  OpenAI : https://platform.openai.com/api-keys"
echo "  Manus  : https://open.manus.ai (Settings -> API)"
echo

grep -q "Cross-Platform Router API keys" "$RC" || printf '\n# --- Cross-Platform Router API keys ---\n' >> "$RC"
set_key GEMINI_API_KEY "starts with AIza..."
set_key OPENAI_API_KEY "starts with sk-proj..."
set_key MANUS_API_KEY  "starts with sk-..."

echo
echo "Done. Open a new terminal or run:  source $RC"
echo "Then ask Claude Code something like: \"router: research the best CRMs for agencies\""
