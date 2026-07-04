"""Enable `python -m stk_mcp` as an entry point.

Mirrors the `stk-mcp` console script so the server can be launched
without a PATH-installed entry point (useful for MCP host configs
that invoke the module directly).
"""

from __future__ import annotations

from stk_mcp.server import main

if __name__ == "__main__":
    main()
