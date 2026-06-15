"""Access and AER analysis tools."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from stk_mcp.app import mcp


def _get_client(ctx: Context):
    state = ctx.request_context.lifespan_context
    return state.client


@mcp.tool()
async def stk_compute_access(
    ctx: Context,
    from_object: str,
    to_object: str,
    time_period: str = "",
    max_step_size: float = 0,
) -> str:
    """Compute access intervals between two objects.

    Args:
        from_object: Source object path, e.g. "Satellite/Sat1" or "Facility/Fac1"
        to_object: Target object path, e.g. "Facility/Fac1" or "Satellite/Sat2"
        time_period: Optional time period, e.g. "1 Jan 2025 00:00:00" "2 Jan 2025 00:00:00".
                     Leave empty to use scenario interval.
        max_step_size: Maximum step size in seconds (0 for default)
    """
    client = _get_client(ctx)

    cmd = f"Access */{from_object} */{to_object}"
    if time_period:
        cmd += f' TimePeriod "{time_period}"'
    else:
        cmd += " TimePeriod UseScenarioInterval"

    if max_step_size > 0:
        cmd += f" MaxStepSize {max_step_size}"

    result = await client.send_command(cmd)
    if result["ack"] == "ACK" and result["data"]:
        return (
            f"Access intervals for {from_object} -> {to_object}:\n"
            + "\n".join(result["data"])
        )
    elif result["ack"] == "ACK":
        return f"No access intervals found between {from_object} and {to_object}"
    return f"Failed to compute access: {result}"


@mcp.tool()
async def stk_all_access(
    ctx: Context,
    from_object: str,
) -> str:
    """Compute access from one object to all other objects in the scenario.

    Args:
        from_object: Source object path, e.g. "Satellite/Sat1"
    """
    client = _get_client(ctx)
    result = await client.send_command(f"AllAccess */{from_object}")
    if result["ack"] == "ACK" and result["data"]:
        return (
            f"All access intervals from {from_object}:\n"
            + "\n".join(result["data"])
        )
    elif result["ack"] == "ACK":
        return f"No access intervals from {from_object}"
    return f"Failed to compute all access: {result}"


@mcp.tool()
async def stk_get_aer(
    ctx: Context,
    from_object: str,
    to_object: str,
    time_period: str = "",
    max_step_size: float = 0,
) -> str:
    """Get Azimuth, Elevation, Range (AER) data between two objects.

    Args:
        from_object: Source object path, e.g. "Facility/Fac1" or "Satellite/Sat1"
        to_object: Target object path, e.g. "Satellite/Sat1"
        time_period: Optional time period string
        max_step_size: Maximum step size in seconds
    """
    client = _get_client(ctx)

    cmd = f"AER */{from_object} */{to_object}"
    if time_period:
        cmd += f' TimePeriod "{time_period}"'
    if max_step_size > 0:
        cmd += f" MaxStepSize {max_step_size}"

    result = await client.send_command(cmd)
    if result["ack"] == "ACK" and result["data"]:
        return (
            f"AER data for {from_object} -> {to_object}:\n"
            + "\n".join(result["data"])
        )
    elif result["ack"] == "ACK":
        return f"No AER data available"
    return f"Failed to get AER data: {result}"
