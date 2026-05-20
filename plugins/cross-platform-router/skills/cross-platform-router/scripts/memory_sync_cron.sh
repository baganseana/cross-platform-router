#!/bin/zsh
# Daily local sync: pull the server's (tidied) shared memory into local MEMORY.md.
# Sources ~/.zshrc to get ROUTER_MCP_ADMIN_URL + keys — no secrets stored in this file.
# Install via crontab (see the bottom of this file) or run manually.

source "$HOME/.zshrc" 2>/dev/null
LOG="$HOME/.claude/skills/cross-platform-router/.sync.log"
echo "--- $(date) pull ---" >> "$LOG"
python3 "$HOME/.claude/skills/cross-platform-router/scripts/sync_memory.py" pull >> "$LOG" 2>&1

# To install a daily pull at 6am local time, run:
#   ( crontab -l 2>/dev/null; echo "0 6 * * * $HOME/.claude/skills/cross-platform-router/scripts/memory_sync_cron.sh" ) | crontab -
# To remove it later:  crontab -e   (delete the line)
