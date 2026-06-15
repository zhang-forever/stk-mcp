"""stk_analysis — Access, coverage, chain, communications, sensor, visibility, radar analysis."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from stk_mcp.app import mcp


def _get_client(ctx: Context):
    return ctx.request_context.lifespan_context.client


@mcp.tool()
async def stk_analysis(
    ctx: Context,
    action: str,
    # Common params
    from_object: str = "",
    to_object: str = "",
    object_path: str = "",
    time_period: str = "",
    max_step_size: float = 0.0,
    # Chain params
    chain_name: str = "",
    # Coverage params
    coverage_name: str = "",
    # Sensor params
    sensor_path: str = "",
    # Comm params
    comm_system: str = "",
    query_type: str = "",
) -> str:
    """Visibility, coverage, chain, communication, sensor, and radar analysis.

    Actions:
        access          — Compute access between two objects. Params: from_object, to_object, time_period, max_step_size
        all_access      — Access from one object to all others. Params: from_object
        aer             — Azimuth/Elevation/Range data. Params: from_object, to_object, time_period, max_step_size
        chain_access    — Communication chain access analysis. Params: chain_name
        chain_intervals — Chain access time intervals. Params: chain_name
        coverage        — Coverage analysis. Params: coverage_name (CoverageDefinition name)
        comm_link       — Communication system query. Params: comm_system, query_type
        sensor_fov      — Sensor field of view analysis. Params: sensor_path (e.g. "Satellite/Sat1/Sensor/Sensor1")
        visibility      — Lighting/visibility conditions. Params: from_object, to_object
        radar           — Radar analysis query. Params: object_path
    """
    client = _get_client(ctx)

    # ── access ───────────────────────────────────────────────
    if action == "access":
        if not from_object or not to_object:
            return "Parameters 'from_object' and 'to_object' are required"
        cmd = f"Access */{from_object} */{to_object}"
        if time_period:
            cmd += f' TimePeriod "{time_period}"'
        else:
            cmd += " TimePeriod UseScenarioInterval"
        if max_step_size > 0:
            cmd += f" MaxStepSize {max_step_size}"
        r = await client.send_command(cmd)
        if r["ack"] == "ACK" and r["data"]:
            return f"Access {from_object} → {to_object}:\n" + "\n".join(r["data"])
        elif r["ack"] == "ACK":
            return f"No access intervals between {from_object} and {to_object}"
        return f"Failed: {r}"

    # ── all_access ───────────────────────────────────────────
    elif action == "all_access":
        if not from_object:
            return "Parameter 'from_object' is required"
        r = await client.send_command(f"AllAccess */{from_object}")
        if r["ack"] == "ACK" and r["data"]:
            return f"All access from {from_object}:\n" + "\n".join(r["data"])
        elif r["ack"] == "ACK":
            return f"No access intervals from {from_object}"
        return f"Failed: {r}"

    # ── aer ──────────────────────────────────────────────────
    elif action == "aer":
        if not from_object or not to_object:
            return "Parameters 'from_object' and 'to_object' are required"
        cmd = f"AER */{from_object} */{to_object}"
        if time_period:
            cmd += f' TimePeriod "{time_period}"'
        if max_step_size > 0:
            cmd += f" MaxStepSize {max_step_size}"
        r = await client.send_command(cmd)
        if r["ack"] == "ACK" and r["data"]:
            return f"AER {from_object} → {to_object}:\n" + "\n".join(r["data"])
        elif r["ack"] == "ACK":
            return "No AER data available"
        return f"Failed: {r}"

    # ── chain_access ─────────────────────────────────────────
    elif action == "chain_access":
        if not chain_name:
            return "Parameter 'chain_name' is required"
        r = await client.send_command(f"ChainAllAccess */Chain/{chain_name}")
        if r["ack"] == "ACK" and r["data"]:
            return f"Chain access for '{chain_name}':\n" + "\n".join(r["data"])
        elif r["ack"] == "ACK":
            return f"No chain access data for '{chain_name}'"
        return f"Failed: {r}"

    # ── chain_intervals ──────────────────────────────────────
    elif action == "chain_intervals":
        if not chain_name:
            return "Parameter 'chain_name' is required"
        r = await client.send_command(f"ChainGetIntervals */Chain/{chain_name}")
        if r["ack"] == "ACK" and r["data"]:
            return f"Chain intervals for '{chain_name}':\n" + "\n".join(r["data"])
        elif r["ack"] == "ACK":
            return f"No interval data for chain '{chain_name}'"
        return f"Failed: {r}"

    # ── coverage ─────────────────────────────────────────────
    elif action == "coverage":
        if not coverage_name:
            return "Parameter 'coverage_name' is required"
        r = await client.send_command(f"Cov_RM */CoverageDefinition/{coverage_name}")
        if r["ack"] == "ACK" and r["data"]:
            return f"Coverage for '{coverage_name}':\n" + "\n".join(r["data"])
        elif r["ack"] == "ACK":
            return f"No coverage data for '{coverage_name}'"
        return f"Failed: {r}"

    # ── comm_link ────────────────────────────────────────────
    elif action == "comm_link":
        if comm_system:
            cmd = f"CommSystem_RM */CommSystem/{comm_system}"
            if query_type:
                cmd += f" {query_type}"
            r = await client.send_command(cmd)
            if r["ack"] == "ACK" and r["data"]:
                return f"CommSystem '{comm_system}':\n" + "\n".join(r["data"])
            elif r["ack"] == "ACK":
                return f"No data for CommSystem '{comm_system}'"
            return f"Failed: {r}"
        # General comm query
        r = await client.send_command("CommQuery")
        if r["ack"] == "ACK" and r["data"]:
            return "CommQuery:\n" + "\n".join(r["data"])
        return f"Failed: {r}"

    # ── sensor_fov ───────────────────────────────────────────
    elif action == "sensor_fov":
        if not sensor_path:
            return "Parameter 'sensor_path' is required (e.g. 'Satellite/Sat1/Sensor/Sensor1')"
        r = await client.send_command(f"FieldOfView_RM */{sensor_path}")
        if r["ack"] == "ACK" and r["data"]:
            return f"Field of view for '{sensor_path}':\n" + "\n".join(r["data"])
        elif r["ack"] == "ACK":
            return f"No FOV data for '{sensor_path}'"
        return f"Failed: {r}"

    # ── visibility ───────────────────────────────────────────
    elif action == "visibility":
        if not from_object or not to_object:
            return "Parameters 'from_object' and 'to_object' are required"
        r = await client.send_command(
            f"Visibility_RM */{from_object} */{to_object}"
        )
        if r["ack"] == "ACK" and r["data"]:
            return f"Visibility {from_object} → {to_object}:\n" + "\n".join(r["data"])
        elif r["ack"] == "ACK":
            return "No visibility data"
        return f"Failed: {r}"

    # ── radar ────────────────────────────────────────────────
    elif action == "radar":
        if not object_path:
            return "Parameter 'object_path' is required"
        r = await client.send_command(f"Radar_RM */{object_path}")
        if r["ack"] == "ACK" and r["data"]:
            return f"Radar data for '{object_path}':\n" + "\n".join(r["data"])
        elif r["ack"] == "ACK":
            return f"No radar data for '{object_path}'"
        return f"Failed: {r}"

    else:
        return (
            f"Unknown action '{action}'. Valid actions: "
            "access, all_access, aer, chain_access, chain_intervals, "
            "coverage, comm_link, sensor_fov, visibility, radar"
        )
