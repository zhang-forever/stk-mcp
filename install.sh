#!/usr/bin/env bash
#
# One-click installer for the STK MCP Server (Linux/macOS).
#
# Installs the package via uv (preferred) or pip, prepares .env, and
# verifies tool registration. COM support is Windows-only and is skipped
# here; the Connect TCP interface works cross-platform.
#
# Usage: ./install.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

step() { printf '\033[36m==> %s\033[0m\n' "$1"; }
ok()   { printf '\033[32m  OK  %s\033[0m\n' "$1"; }
warn() { printf '\033[33m  !!  %s\033[0m\n' "$1"; }

step "STK MCP Server installer"
echo "Repo: $REPO_ROOT"
echo

# --- Detect installer backend (prefer uv) --------------------------------
if command -v uv >/dev/null 2>&1; then
    ok "uv detected — using isolated environment"
    step "Installing stk-mcp (Connect TCP, cross-platform)"
    uv sync --extra dev
    ok "Dependencies installed into .venv"
    PY_EXE=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    warn "uv not found. Falling back to pip."
    ok "Python detected: $(python3 --version)"
    step "Installing stk-mcp via pip"
    python3 -m pip install -e ".[dev]"
    ok "Package installed"
    PY_EXE="python3"
else
    echo "ERROR: neither uv nor python3 found on PATH." >&2
    echo "Install uv (https://docs.astral.sh/uv/) or Python 3.10+." >&2
    exit 1
fi

# --- Prepare .env --------------------------------------------------------
if [ ! -f .env ]; then
    cp .env.example .env
    ok "Created .env from template"
else
    warn ".env already exists — left untouched"
fi

# --- Smoke test: import and tool registration ----------------------------
step "Verifying tool registration (no STK required)"
"$PY_EXE" -c "import stk_mcp.tools; from stk_mcp.app import mcp; import asyncio; tools = asyncio.run(mcp.list_tools()); print('  Registered ' + str(len(tools)) + ' tools: ' + ', '.join(t.name for t in tools))"
ok "Server imports cleanly"

# --- Print client config -------------------------------------------------
step "Next steps"
cat <<EOF

1. Enable Connect on the machine running STK (Windows):
     Edit -> Preferences -> Connect -> Enable Connect Server (port 5001)

2. Register with your MCP client. For a remote STK host set STK_HOST:

     claude mcp add stk --scope user \\
       --env STK_HOST=<stk-machine-ip> --env STK_PORT=5001 \\
       -- uvx --python 3.11 --from "$REPO_ROOT" stk-mcp

3. Start your MCP client. Done.
EOF

ok "Installation complete"
