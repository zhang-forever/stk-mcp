"""Raw Connect command passthrough — escape hatch for any STK command."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from stk_mcp.app import mcp


def _get_client(ctx: Context):
    state = ctx.request_context.lifespan_context
    return state.client


@mcp.tool()
async def stk_send_command(ctx: Context, command: str) -> str:
    """Send a raw STK Connect command. Use this for any command not covered by other tools.

    The Connect protocol has 1100+ commands. This tool lets you send any of them directly.

    Common examples:
        - "New / */Satellite MySat"
        - "SetState */Satellite/MySat TLE \\"line1\\" \\"line2\\""
        - "GetTimePeriod *"
        - "Position */Satellite/MySat"
        - "VO * WindowState 3D On"

    Args:
        command: The raw STK Connect command string (without trailing newline)
    """
    client = _get_client(ctx)
    result = await client.send_command(command)

    output_parts = [f"Command: {command}", f"ACK: {result['ack']}"]

    if result["data"]:
        output_parts.append(f"Data ({len(result['data'])} lines):")
        output_parts.append("\n".join(result["data"]))
    elif result["raw"]:
        output_parts.append(f"Response: {result['raw']}")

    return "\n".join(output_parts)
