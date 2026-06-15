"""
STK MCP Server entry point.

Imports mcp from app.py, registers all tools, and starts the server.
"""

from __future__ import annotations

from stk_mcp.app import mcp

# Import all tool modules to trigger @mcp.tool() registration
import stk_mcp.tools  # noqa: E402, F401


def main():
    """Entry point for the stk-mcp CLI command."""
    mcp.run()


if __name__ == "__main__":
    main()
