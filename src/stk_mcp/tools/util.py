"""stk_util — Reports, unit/date/coordinate conversion, animation time, and raw command passthrough."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from stk_mcp.app import mcp
from stk_mcp.tools._common import get_client
from stk_mcp.validation import CommandValidationError, validate_raw_command

# Unit names and abbreviations mapped to (STK dimension, canonical abbreviation).
# Values follow STK's unit reference; Units_Convert only accepts units valid for
# the chosen dimension. Unknown pairs fall back to the deprecated ConvertUnit.
_UNIT_TABLE: dict[str, tuple[str, str]] = {
    # Distance
    "m": ("Distance", "m"),
    "meter": ("Distance", "m"),
    "meters": ("Distance", "m"),
    "km": ("Distance", "km"),
    "kilometer": ("Distance", "km"),
    "kilometers": ("Distance", "km"),
    "ft": ("Distance", "ft"),
    "foot": ("Distance", "ft"),
    "feet": ("Distance", "ft"),
    "mi": ("Distance", "mi"),
    "mile": ("Distance", "mi"),
    "miles": ("Distance", "mi"),
    "nm": ("Distance", "nm"),
    "nmi": ("Distance", "nm"),
    "nauticalmile": ("Distance", "nm"),
    "nauticalmiles": ("Distance", "nm"),
    "au": ("Distance", "Au"),
    "astronomicalunit": ("Distance", "Au"),
    "re": ("Distance", "Re"),
    "earthradii": ("Distance", "Re"),
    "kft": ("Distance", "kft"),
    "kilofeet": ("Distance", "kft"),
    "fur": ("Distance", "fur"),
    "furlong": ("Distance", "fur"),
    "fm": ("Distance", "fm"),
    "fathom": ("Distance", "fm"),
    "leag": ("Distance", "leag"),
    "league": ("Distance", "leag"),
    # SmallDistance
    "in": ("SmallDistance", "in"),
    "inch": ("SmallDistance", "in"),
    "inches": ("SmallDistance", "in"),
    "cm": ("SmallDistance", "cm"),
    "centimeter": ("SmallDistance", "cm"),
    "centimeters": ("SmallDistance", "cm"),
    "mm": ("SmallDistance", "mm"),
    "millimeter": ("SmallDistance", "mm"),
    "millimeters": ("SmallDistance", "mm"),
    "um": ("SmallDistance", "um"),
    "micron": ("SmallDistance", "um"),
    "microns": ("SmallDistance", "um"),
    "nanom": ("SmallDistance", "nanom"),
    "nanometer": ("SmallDistance", "nanom"),
    # Time
    "sec": ("Time", "sec"),
    "second": ("Time", "sec"),
    "seconds": ("Time", "sec"),
    "s": ("Time", "sec"),
    "min": ("Time", "min"),
    "minute": ("Time", "min"),
    "minutes": ("Time", "min"),
    "hr": ("Time", "hr"),
    "hour": ("Time", "hr"),
    "hours": ("Time", "hr"),
    "day": ("Time", "day"),
    "days": ("Time", "day"),
    "cd": ("Time", "cd"),
    "centiday": ("Time", "cd"),
    "fn": ("Time", "FN"),
    "fortnight": ("Time", "FN"),
    "yr": ("Time", "yr"),
    "year": ("Time", "yr"),
    "years": ("Time", "yr"),
    # Angle
    "deg": ("Angle", "deg"),
    "degree": ("Angle", "deg"),
    "degrees": ("Angle", "deg"),
    "rad": ("Angle", "rad"),
    "radian": ("Angle", "rad"),
    "radians": ("Angle", "rad"),
    "arcsec": ("Angle", "arcSec"),
    "arcsecond": ("Angle", "arcSec"),
    "arcseconds": ("Angle", "arcSec"),
    "arcmin": ("Angle", "arcMin"),
    "arcminute": ("Angle", "arcMin"),
    "arcminutes": ("Angle", "arcMin"),
    "dms": ("Angle", "DMS"),
    "hms": ("Angle", "HMS"),
    "mrad": ("Angle", "mrad"),
    "milliradian": ("Angle", "mrad"),
    "urad": ("Angle", "urad"),
    "microradian": ("Angle", "urad"),
    "revs": ("Angle", "revs"),
    "revolution": ("Angle", "revs"),
    "semic": ("Angle", "semiC"),
    "mdeg": ("Angle", "mdeg"),
    "millidegree": ("Angle", "mdeg"),
    # Mass
    "kg": ("Mass", "kg"),
    "kilogram": ("Mass", "kg"),
    "kilograms": ("Mass", "kg"),
    "g": ("Mass", "g"),
    "gram": ("Mass", "g"),
    "grams": ("Mass", "g"),
    "mg": ("Mass", "mg"),
    "milligram": ("Mass", "mg"),
    "milligrams": ("Mass", "mg"),
    "lb": ("Mass", "lb"),
    "pound": ("Mass", "lb"),
    "pounds": ("Mass", "lb"),
    "slug": ("Mass", "slug"),
    "slugs": ("Mass", "slug"),
    # Temperature
    "k": ("Temperature", "K"),
    "kelvin": ("Temperature", "K"),
    "c": ("Temperature", "degC"),
    "celsius": ("Temperature", "degC"),
    "degc": ("Temperature", "degC"),
    "f": ("Temperature", "degF"),
    "fahrenheit": ("Temperature", "degF"),
    "degf": ("Temperature", "degF"),
    # Frequency
    "hz": ("Frequency", "Hz"),
    "hertz": ("Frequency", "Hz"),
    "khz": ("Frequency", "KHz"),
    "kilohertz": ("Frequency", "KHz"),
    "mhz": ("Frequency", "MHz"),
    "megahertz": ("Frequency", "MHz"),
    "ghz": ("Frequency", "GHz"),
    "gigahertz": ("Frequency", "GHz"),
    "thz": ("Frequency", "THz"),
    "terahertz": ("Frequency", "THz"),
    # DopplerVelocity
    "m/s": ("DopplerVelocity", "m/s"),
    "m/sec": ("DopplerVelocity", "m/s"),
    "fps": ("DopplerVelocity", "fps"),
    "ft/s": ("DopplerVelocity", "fps"),
    "kph": ("DopplerVelocity", "kph"),
    "km/h": ("DopplerVelocity", "kph"),
    "km/hr": ("DopplerVelocity", "kph"),
    "kts": ("DopplerVelocity", "kts"),
    "knot": ("DopplerVelocity", "kts"),
    "knots": ("DopplerVelocity", "kts"),
    "mph": ("DopplerVelocity", "mph"),
}


def _unit_conversion(from_unit: str, to_unit: str) -> tuple[str | None, str, str, str]:
    """Return (dimension, canonical from, canonical to, error message)."""
    source = _UNIT_TABLE.get(from_unit.strip().lower())
    target = _UNIT_TABLE.get(to_unit.strip().lower())
    if source is None or target is None:
        return None, from_unit, to_unit, ""
    if source[0] != target[0]:
        return (
            None,
            from_unit,
            to_unit,
            (
                f"Units '{from_unit}' and '{to_unit}' belong to different "
                f"dimensions ({source[0]}, {target[0]})"
            ),
        )
    return source[0], source[1], target[1], ""


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
    client = get_client(ctx)

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
            return f"Report '{style}' for {object_path} ({len(r['data'])} lines):\n" + "\n".join(
                r["data"]
            )
        elif r["ack"] == "ACK":
            return f"Report '{style}' for {object_path}: No data"
        return f"Failed to get report: {r}"

    # ── save_report ──────────────────────────────────────────
    elif action == "save_report":
        if not object_path or not style or not file_path:
            return "Parameters 'object_path', 'style', and 'file_path' are required"
        cmd = f'ReportCreate */{object_path} Type Save Style "{style}" File "{file_path}"'
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
            return "Date conversion:\n" + r["raw"]
        return f"Failed: {r}"

    # ── convert_unit ─────────────────────────────────────────
    elif action == "convert_unit":
        if not from_unit or not to_unit:
            return "Parameters 'from_unit' and 'to_unit' are required"
        dimension, source_unit, target_unit, error = _unit_conversion(from_unit, to_unit)
        if error:
            return error
        if dimension:
            cmd = f'Units_Convert * Unit {dimension} "{source_unit}" "{target_unit}" "{value}"'
        else:
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
        try:
            command = validate_raw_command(command)
        except CommandValidationError as exc:
            return f"Invalid input: {exc}"
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
