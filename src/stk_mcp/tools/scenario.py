"""Scenario management tools: create, load, save, unload."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from stk_mcp.app import mcp


def _get_client(ctx: Context):
    state = ctx.request_context.lifespan_context
    return state.client


@mcp.tool()
async def stk_connect(ctx: Context, host: str = "localhost", port: int = 5001) -> str:
    """Connect to STK Connect port. Call this first if STK wasn't running at server start.

    Args:
        host: STK host address (default: localhost)
        port: STK Connect port (default: 5001)
    """
    state = ctx.request_context.lifespan_context
    client = state.client
    if client.connected:
        return f"Already connected to STK at {state.host}:{state.port}"
    client.host = host
    client.port = port
    await client.connect()
    state.host = host
    state.port = port
    return f"Connected to STK at {host}:{port}"


@mcp.tool()
async def stk_disconnect(ctx: Context) -> str:
    """Disconnect from STK Connect."""
    client = _get_client(ctx)
    if not client.connected:
        return "Not connected"
    await client.disconnect()
    return "Disconnected from STK"


@mcp.tool()
async def stk_status(ctx: Context) -> str:
    """Check STK connection status and current scenario info."""
    client = _get_client(ctx)
    if not client.connected:
        return "Not connected to STK"

    lines = ["Connected to STK"]

    # Get version
    try:
        result = await client.send_command("GetSTKVersion")
        if result["ack"] == "ACK" and result["data"]:
            lines.append(f"Version: {result['raw']}")
    except Exception as e:
        lines.append(f"Version check failed: {e}")

    # Check scenario
    try:
        result = await client.send_command("CheckScenario")
        if result["ack"] == "ACK" and result["data"]:
            lines.append(f"Scenario: {result['raw']}")
        else:
            lines.append("Scenario: None loaded")
    except Exception as e:
        lines.append(f"Scenario check failed: {e}")

    return "\n".join(lines)


@mcp.tool()
async def stk_new_scenario(
    ctx: Context,
    name: str,
    start_time: str = "",
    stop_time: str = "",
) -> str:
    """Create a new STK scenario.

    Args:
        name: Scenario name (no spaces recommended)
        start_time: Start time, e.g. "1 Jan 2025 00:00:00.00" or "Today" (default: today)
        stop_time: Stop time, e.g. "+24hr" or specific date (default: +24hr)
    """
    client = _get_client(ctx)

    # Create scenario
    result = await client.send_command(f"New / Scenario {name}")
    if result["ack"] != "ACK":
        return f"Failed to create scenario: {result}"

    # Set time period if specified
    if start_time and stop_time:
        tp_result = await client.send_command(
            f'SetTimePeriod * "{start_time}" "{stop_time}"'
        )
        if tp_result["ack"] != "ACK":
            return f"Scenario created but time period failed: {tp_result}"

    # Reset animation
    await client.send_command("Animate * Reset")

    return f"Scenario '{name}' created" + (
        f" [{start_time} to {stop_time}]" if start_time and stop_time else ""
    )


@mcp.tool()
async def stk_load_scenario(ctx: Context, file_path: str) -> str:
    """Load an existing STK scenario file (.sc).

    Args:
        file_path: Full path to the .sc scenario file
    """
    client = _get_client(ctx)
    result = await client.send_command(f'Load / Scenario "{file_path}"')
    if result["ack"] == "ACK":
        return f"Scenario loaded from: {file_path}"
    return f"Failed to load scenario: {result}"


@mcp.tool()
async def stk_save_scenario(ctx: Context, save_path: str = "") -> str:
    """Save the current STK scenario.

    Args:
        save_path: Directory path to save in. If empty, saves to current location.
    """
    client = _get_client(ctx)
    cmd = 'Save / *'
    if save_path:
        cmd += f' "{save_path}"'
    result = await client.send_command(cmd)
    if result["ack"] == "ACK":
        return f"Scenario saved" + (f" to {save_path}" if save_path else "")
    return f"Failed to save scenario: {result}"


@mcp.tool()
async def stk_unload_scenario(ctx: Context) -> str:
    """Unload (close) the current scenario."""
    client = _get_client(ctx)
    result = await client.send_command("Unload / *")
    if result["ack"] == "ACK":
        return "Scenario unloaded"
    return f"Failed to unload scenario: {result}"


@mcp.tool()
async def stk_set_time_period(
    ctx: Context,
    start_time: str,
    stop_time: str,
) -> str:
    """Set the scenario analytical time period.

    Args:
        start_time: Start time, e.g. "1 Jan 2025 00:00:00.00" or "Today"
        stop_time: Stop time, e.g. "+24hr" or "2 Jan 2025 00:00:00.00"
    """
    client = _get_client(ctx)
    result = await client.send_command(
        f'SetTimePeriod * "{start_time}" "{stop_time}"'
    )
    if result["ack"] == "ACK":
        return f"Time period set: {start_time} to {stop_time}"
    return f"Failed to set time period: {result}"
