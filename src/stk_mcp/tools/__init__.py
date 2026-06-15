"""STK MCP tool modules."""

# Import all tool modules to trigger @mcp_server.tool() registration
from stk_mcp.tools import (
    scenario,
    objects,
    orbit,
    access,
    cat,
    reports,
    animation,
    raw,
)

__all__ = [
    "scenario",
    "objects",
    "orbit",
    "access",
    "cat",
    "reports",
    "animation",
    "raw",
]
