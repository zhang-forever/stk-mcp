"""STK MCP tool modules — 6 domain tools."""

# Import all tool modules to trigger @mcp.tool() registration
from stk_mcp.tools import (
    scenario,
    objects,
    orbit,
    cat,
    analysis,
    util,
)

__all__ = [
    "scenario",
    "objects",
    "orbit",
    "cat",
    "analysis",
    "util",
]
