"""Shared context helpers and checked Connect command dispatch."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from stk_mcp.connect_client import StkConnectClient, StkResult


class StkCommandError(RuntimeError):
    """A Connect command was rejected or returned an unexpected response."""


def get_client(ctx: Context) -> StkConnectClient:
    """Return the Connect client from the MCP lifespan context."""
    return ctx.request_context.lifespan_context.client


def get_state(ctx: Context) -> Any:
    """Return the full STK state from the MCP lifespan context."""
    return ctx.request_context.lifespan_context


async def send_checked(client: StkConnectClient, command: str) -> StkResult:
    """Send a command and raise when STK does not answer with ACK."""
    result = await client.send_command(command)
    if result["ack"] != "ACK":
        raise StkCommandError(f"STK rejected '{command}': {result}")
    return result
