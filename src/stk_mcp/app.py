"""
FastMCP instance definition.

This module ONLY creates the MCP server instance.
It does NOT import tools — that happens in server.py.
Tool modules import `mcp` from here (not from server.py)
to avoid circular imports.
"""

from __future__ import annotations

import logging
import os
import sys

from mcp.server.fastmcp import FastMCP

from stk_mcp.logic.stk_state import create_stk_lifespan

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)

# Server configuration from environment
logger = logging.getLogger("stk_mcp.app")


def _env_int(name: str, default: int) -> int:
    """Read a positive integer environment variable, falling back with a warning."""
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning("Invalid %s=%r; using %d", name, raw, default)
        return default
    if not 1 <= value <= 65535:
        logger.warning("%s=%d is out of range; using %d", name, value, default)
        return default
    return value


STK_HOST = os.environ.get("STK_HOST", "localhost").strip() or "localhost"
STK_PORT = _env_int("STK_PORT", 5001)

# Create the MCP server with lifespan for STK connection lifecycle
mcp = FastMCP(
    "STK Control",
    lifespan=create_stk_lifespan(host=STK_HOST, port=STK_PORT),
)
