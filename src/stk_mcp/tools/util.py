"""stk_util — Reports, unit/date/coordinate conversion, animation time, and raw command passthrough."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from stk_mcp.app import mcp


def _get_client(ctx: Context):
    return ctx.request_context.lifespan_context.client


@mcp.tool()
async def stk_util(
    ctx: Context,
    action: str,
    # Report params
    object_path: str = "",
    style: str = "",
    file_path: str = "",
    time_period: str = "",
    time_step: float = 0.0,
    access_object: str = "",
    all_lines: bool = False,
    # Convert params
    from_unit: str = "",
    to_unit: str = "",
    value: float = 0.0,
    from_coord: str = "",
    to_coord: str = "",
    coord_values: str = "",
    date_string: str = "",
    date_format: str = "",
    # Raw command
    command: str = "",
    # Animate
    animate_action: str = "",
) -> str:
    """Reports, conversions, animation time, and raw STK commands.

    Actions:
        report              — Get report data. Params: object_path, style, time_period, time_step, access_object, all_lines
        save_report         — Save report to file. Params: object_path, style, file_path, time_period, time_step, access_object
        list_report_styles  — List available report styles. Params: object_path
        convert_coord       — Convert coordinates. Params: from_coord, to_coord, coord_values (comma-separated)
        convert_date        — Convert date format. Params: date_string, date_format
        convert_unit        — Convert units. Params: from_unit, to_unit, value
        get_animation_time  — Get current animation time (no params needed)
        send_command        — Send raw STK Connect command. Params: command
    """
    client = _get_client(ctx)

    # ── report ───────────────────────────────────────────────
    if action == "report":
        if not object_path or not style:
            return "Parameters 'object_path' and 'style' are required"
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
        r = await client.send_command(cmd)
        if r["ack"] == "ACK" and r["data"]:
            return f"Report '{style}' for {object_path} ({len(r['data'])} lines):\n" + "\n".join(r["data"])
        elif r["ack"] == "ACK":
            return f"Report '{style}' for {object_path}: No data"
        return f"Failed to get report: {r}"

    # ── save_report ──────────────────────────────────────────
    elif action == "save_report":
        if not object_path or not style or not file_path:
            return "Parameters 'object_path', 'style', and 'file_path' are required"
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
        r = await client.send_command(cmd)
        if r["ack"] == "ACK":
            return f"Report '{style}' saved to: {file_path}"
        return f"Failed to save report: {r}"

    # ── list_report_styles ───────────────────────────────────
    elif action == "list_report_styles":
        if not object_path:
            return "Parameter 'object_path' is required"
        r = await client.send_command(f"ReportStyle */{object_path}")
        if r["ack"] == "ACK" and r["data"]:
            return f"Report styles for {object_path}:\n" + "\n".join(r["data"])
        elif r["ack"] == "ACK":
            return (
                "Common report styles for satellites:\n"
                "  LLA State, Cartesian Position, Classical Orbit, "
                "Keplerian Elements, AER, Lighting Times, VehPos"
            )
        return f"Failed: {r}"

    # ── convert_coord ────────────────────────────────────────
    elif action == "convert_coord":
        if not from_coord or not to_coord or not coord_values:
            return "Parameters 'from_coord', 'to_coord', 'coord_values' are required"
        cmd = f"ConvertCoord {from_coord} {to_coord} {coord_values}"
        r = await client.send_command(cmd)
        if r["ack"] == "ACK" and r["data"]:
            return f"Coordinate conversion ({from_coord} → {to_coord}):\n" + r["raw"]
        return f"Failed: {r}"

    # ── convert_date ─────────────────────────────────────────
    elif action == "convert_date":
        if not date_string:
            return "Parameter 'date_string' is required"
        cmd = f'ConvertDate "{date_string}"'
        if date_format:
            cmd += f" Format {date_format}"
        r = await client.send_command(cmd)
        if r["ack"] == "ACK" and r["data"]:
            return f"Date conversion:\n" + r["raw"]
        return f"Failed: {r}"

    # ── convert_unit ─────────────────────────────────────────
    elif action == "convert_unit":
        if not from_unit or not to_unit:
            return "Parameters 'from_unit', 'to_unit', and 'value' are required"
        cmd = f"ConvertUnit {from_unit} {to_unit} {value}"
        r = await client.send_command(cmd)
        if r["ack"] == "ACK" and r["data"]:
            return f"Unit conversion: {value} {from_unit} = {r['raw']} {to_unit}"
        return f"Failed: {r}"

    # ── get_animation_time ───────────────────────────────────
    elif action == "get_animation_time":
        r = await client.send_command("GetAnimTime *")
        if r["ack"] == "ACK" and r["data"]:
            return f"Animation time: {r['raw']}"
        return f"Failed: {r}"

    # ── send_command ─────────────────────────────────────────
    elif action == "send_command":
        if not command:
            return "Parameter 'command' is required"
        r = await client.send_command(command)
        output = [f"Command: {command}", f"ACK: {r['ack']}"]
        if r["data"]:
            output.append(f"Data ({len(r['data'])} lines):")
            output.append("\n".join(r["data"]))
        elif r["raw"]:
            output.append(f"Response: {r['raw']}")
        return "\n".join(output)

    else:
        return (
            f"Unknown action '{action}'. Valid actions: "
            "report, save_report, list_report_styles, convert_coord, "
            "convert_date, convert_unit, get_animation_time, send_command"
        )
