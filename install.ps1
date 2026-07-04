<#
.SYNOPSIS
    One-click installer for the STK MCP Server on Windows.

.DESCRIPTION
    Verifies prerequisites, installs the package with COM support via uv
    (or pip as a fallback), prepares the .env file, and prints the client
    configuration snippet to register the server with an MCP client.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File install.ps1
#>

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "  !!  $msg" -ForegroundColor Yellow }

Write-Step "STK MCP Server installer"
Write-Host "Repo: $RepoRoot`n"

# --- Detect installer backend (prefer uv) --------------------------------
$UvAvailable = $null -ne (Get-Command uv -ErrorAction SilentlyContinue)

if ($UvAvailable) {
    Write-Ok "uv detected — using isolated environment"
    Write-Step "Installing stk-mcp with COM support"
    uv sync --extra com --extra dev
    Write-Ok "Dependencies installed into .venv"
} else {
    Write-Warn "uv not found. Falling back to pip."
    $PyVersion = (python --version 2>&1)
    if ($LASTEXITCODE -ne 0) {
        throw "Neither uv nor python found on PATH. Install uv (https://docs.astral.sh/uv/) or Python 3.10+."
    }
    Write-Ok "Python detected: $PyVersion"
    Write-Step "Installing stk-mcp with COM support via pip"
    python -m pip install -e ".[com,dev]"
    Write-Ok "Package installed"
}

# --- Prepare .env --------------------------------------------------------
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Ok "Created .env from template"
} else {
    Write-Warn ".env already exists — left untouched"
}

# --- Smoke test: import and tool registration ----------------------------
Write-Step "Verifying tool registration (no STK required)"
$PyExe = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
& $PyExe -c "import stk_mcp.tools; from stk_mcp.app import mcp; import asyncio; tools = asyncio.run(mcp.list_tools()); print(f'  Registered {len(tools)} tools: ' + ', '.join(t.name for t in tools))"
if ($LASTEXITCODE -ne 0) { throw "Tool registration check failed." }
Write-Ok "Server imports cleanly"

# --- Print client config -------------------------------------------------
Write-Step "Next steps"
Write-Host @"

1. Enable Connect in STK:
     Edit -> Preferences -> Connect -> Enable Connect Server (port 5001)

2. Register with your MCP client. For Claude Code (recommended):

     claude mcp add stk --scope user ``
       --env STK_HOST=localhost --env STK_PORT=5001 ``
       -- uvx --python 3.11 --from "$RepoRoot" stk-mcp

   Or add this to your client's mcpServers config:

     {
       "mcpServers": {
         "stk": {
           "command": "uvx",
           "args": ["--python", "3.11", "--from", "$($RepoRoot -replace '\\','/')", "stk-mcp"],
           "env": { "STK_HOST": "localhost", "STK_PORT": "5001" }
         }
       }
     }

3. Start STK, then launch your MCP client. Done.
"@ -ForegroundColor White

Write-Ok "Installation complete"
