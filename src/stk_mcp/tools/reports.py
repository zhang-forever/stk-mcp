"""Report tools: get reports via Connect socket or save to file."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from stk_mcp.app import mcp


def _get_client(ctx: Context):
    state = ctx.request_context.lifespan_context
    return state.client


@mcp.tool()
async def stk_get_report(
    ctx: Context,
    object_path: str,
    style: str,
    time_period: str = "",
    time_step: float = 0,
    access_object: str = "",
    all_lines: bool = False,
) -> str:
    """Get report data from an STK object via Connect socket.

    Args:
        object_path: Object path, e.g. "Satellite/Sat1" or "Facility/Fac1"
        style: Report style name, e.g. "LLA State", "AER", "Lighting Times",
               "Cartesian Position", "Classical Orbit", "VehPos"
        time_period: Time period string. Empty for scenario interval.
        time_step: Time step in seconds (0 for default)
        access_object: Access object path for access-based reports,
                       e.g. "Facility/Fac1"
        all_lines: Include all headers, spaces, tabs, blank lines
    """
    client = _get_client(ctx)

    cmd = f'Report_RM */{object_path} Style "{style}"'

    if time_period:
        cmd += f' TimePeriod "{time_period}"'
    elif access_object:
        cmd += " TimePeriod UseAccessTimes"

    if time_step > 0:
        cmd += f" TimeStep {time_step}"

    if access_object:
        cmd += f" AccessObject */{access_object}"

    if all_lines:
        cmd += " AllLines On"

    result = await client.send_command(cmd)
    if result["ack"] == "ACK" and result["data"]:
        return (
            f"Report '{style}' for {object_path} ({len(result['data'])} lines):\n"
            + "\n".join(result["data"])
        )
    elif result["ack"] == "ACK":
        return f"Report '{style}' for {object_path}: No data"
    return f"Failed to get report: {result}"


@mcp.tool()
async def stk_save_report(
    ctx: Context,
    object_path: str,
    style: str,
    file_path: str,
    time_period: str = "",
    time_step: float = 0,
    access_object: str = "",
) -> str:
    """Generate and save a report to a file.

    Args:
        object_path: Object path, e.g. "Satellite/Sat1"
        style: Report style name
        file_path: Output file path
        time_period: Time period string. Empty for scenario interval.
        time_step: Time step in seconds
        access_object: Access object path for access-based reports
    """
    client = _get_client(ctx)

    cmd = (
        f'ReportCreate */{object_path} Type Save Style "{style}" '
        f'File "{file_path}"'
    )

    if time_period:
        cmd += f' TimePeriod "{time_period}"'
    elif access_object:
        cmd += " TimePeriod UseAccessTimes"

    if time_step > 0:
        cmd += f" TimeStep {time_step}"

    if access_object:
        cmd += f" AccessObject */{access_object}"

    result = await client.send_command(cmd)
    if result["ack"] == "ACK":
        return f"Report '{style}' saved to: {file_path}"
    return f"Failed to save report: {result}"


@mcp.tool()
async def stk_list_report_styles(ctx: Context, object_path: str) -> str:
    """List available report styles for an object.

    Args:
        object_path: Object path, e.g. "Satellite/Sat1"
    """
    client = _get_client(ctx)
    result = await client.send_command(
        f'ReportStyle */{object_path}'
    )
    if result["ack"] == "ACK" and result["data"]:
        return (
            f"Available report styles for {object_path}:\n"
            + "\n".join(result["data"])
        )
    elif result["ack"] == "ACK":
        return (
            "Common report styles for satellites:\n"
            "  LLA State, Cartesian Position, Classical Orbit, "
            "Keplerian Elements, AER, Lighting Times, VehPos"
        )
    return f"Failed to list report styles: {result}"
