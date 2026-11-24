<#
.SYNOPSIS
    Run the Cursor CLI agent on this repo, using the API key from .env.

.DESCRIPTION
    Reads CURSOR_API_KEY (or cursor_api_key) from the repo's .env file and
    passes it to the Cursor CLI for this run only. The key is never printed or
    written anywhere else. The agent picks up AGENTS.md, .cursor/rules/ and the
    command/file limits in .cursor/cli.json automatically.

.EXAMPLE
    .\scripts\cursor_agent.ps1 status
    .\scripts\cursor_agent.ps1 -p "Explain how src/metrics.py scores alarm episodes" --mode ask
    .\scripts\cursor_agent.ps1 -p "Add a unit test for src/schema.py::find_gaps"
    .\scripts\cursor_agent.ps1            # interactive session
#>
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root ".env"

if (-not (Test-Path $envFile)) {
    Write-Error "No .env file at $envFile. Copy .env.example to .env and set CURSOR_API_KEY."
}

$key = $null
foreach ($line in Get-Content $envFile) {
    if ($line -match '^\s*(CURSOR_API_KEY|cursor_api_key)\s*=\s*(.*)\s*$') {
        $key = $Matches[2].Trim().Trim('"').Trim("'")
    }
}
if (-not $key) {
    Write-Error "CURSOR_API_KEY is missing or empty in .env."
}

$agent = Get-Command agent -ErrorAction SilentlyContinue
if (-not $agent) { $agent = Get-Command cursor-agent -ErrorAction SilentlyContinue }
if (-not $agent) {
    Write-Error "Cursor CLI not found. Install it from https://cursor.com/cli, then open a new terminal."
}

$previous = $env:CURSOR_API_KEY
try {
    $env:CURSOR_API_KEY = $key   # only for this process and the agent it starts
    Push-Location $root
    & $agent.Source @args
    exit $LASTEXITCODE
}
finally {
    Pop-Location
    $env:CURSOR_API_KEY = $previous
}
