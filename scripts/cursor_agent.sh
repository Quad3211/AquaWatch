#!/usr/bin/env bash
# Run the Cursor CLI agent on this repo, using the API key from .env.
#
# Reads CURSOR_API_KEY (or cursor_api_key) from the repo's .env and passes it
# to the Cursor CLI for this run only; the key is never printed. The agent picks
# up AGENTS.md, .cursor/rules/ and the limits in .cursor/cli.json automatically.
#
#   scripts/cursor_agent.sh status
#   scripts/cursor_agent.sh -p "Explain how src/metrics.py scores alarm episodes" --mode ask
#   scripts/cursor_agent.sh            # interactive session
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="$root/.env"
if [[ ! -f "$env_file" ]]; then
  echo "No .env file at $env_file. Copy .env.example to .env and set CURSOR_API_KEY." >&2
  exit 1
fi

key="$(grep -E '^[[:space:]]*(CURSOR_API_KEY|cursor_api_key)[[:space:]]*=' "$env_file" | tail -n 1 \
  | sed -E 's/^[^=]*=[[:space:]]*//; s/[[:space:]]*$//; s/^["'\'']//; s/["'\'']$//' | tr -d '\r')"
if [[ -z "$key" ]]; then
  echo "CURSOR_API_KEY is missing or empty in .env." >&2
  exit 1
fi

if command -v agent >/dev/null 2>&1; then
  agent_cmd=agent
elif command -v cursor-agent >/dev/null 2>&1; then
  agent_cmd=cursor-agent
elif command -v cursor-agent.cmd >/dev/null 2>&1; then
  agent_cmd=cursor-agent.cmd
else
  echo "Cursor CLI not found. Install it from https://cursor.com/cli, then open a new terminal." >&2
  exit 1
fi

cd "$root"
CURSOR_API_KEY="$key" exec "$agent_cmd" "$@"
