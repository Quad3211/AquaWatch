# Using the Cursor agent on AquaWatch

The Cursor CLI agent can work on this repo from the terminal. It follows the same scope and honesty rules as any other agent: see [AGENTS.md](../AGENTS.md).

## One-time setup
1. Install the Cursor CLI (https://cursor.com/cli) and open a new terminal.
2. Create an API key in the Cursor dashboard (https://cursor.com/dashboard/api).
3. Copy `.env.example` to `.env` and paste the key in:
   ```
   CURSOR_API_KEY=your-key-here
   ```
   `.env` is gitignored, and the agent is blocked from reading it (`.cursorignore`, `.cursor/cli.json`). **Never commit the key or paste it into chat.** If it leaks, delete it in the dashboard and make a new one.

## Running it
PowerShell:
```powershell
.\scripts\cursor_agent.ps1 -p --mode ask "Explain how src/metrics.py scores alarm episodes"
.\scripts\cursor_agent.ps1 -p "Add a unit test for src/schema.py::find_gaps"
.\scripts\cursor_agent.ps1                 # interactive session
```
Git Bash or macOS/Linux:
```bash
scripts/cursor_agent.sh -p --mode ask "Explain how src/metrics.py scores alarm episodes"
```
The wrapper reads the key from `.env`, gives it to the agent for that run only, and never prints it. `-p` runs once without asking questions (headless). `--mode ask` answers questions without editing anything.

## What the agent may and may not do
Cursor loads these automatically:
- **`AGENTS.md`** and **`.cursor/rules/`** set the project's scope and honesty rules.
- **`.cursor/cli.json`** sets hard limits for the command-line agent, and deny always wins:
  - **Commands it may run:** tests, lint, the evaluation and training scripts, and `git status/diff/log`.
  - **Files it may edit:** `src/`, `tests/`, `scripts/`, `app.py`, `docs/`, `README.md` and the two data notes.
  - **Blocked:**
    - reading `.env`
    - editing config, dependencies, CI, `AGENTS.md`, `.cursor/`, generated data, models, the research reports and the pitch
    - git commit, push, reset, rebase and checkout
    - deleting files
    - installing packages
    - downloads and web fetches
- **`.cursor/permissions.json`** sets the same kind of limits for the agent inside the Cursor editor.

In headless mode (`-p`), any command not on the allowlist is refused unless you add `--force`. **Do not use `--force` on this repo.** Review what the agent changed with `git diff`, and commit it yourself.
