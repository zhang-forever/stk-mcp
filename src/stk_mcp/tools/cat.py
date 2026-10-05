"""stk_conjunction — Conjunction Assessment (CAT + Advanced CAT) for collision warning."""

from __future__ import annotations

import math
from functools import wraps
from uuid import uuid4

from mcp.server.fastmcp import Context

from stk_mcp.app import mcp
from stk_mcp.tools.orbit import _propagate_satellite_result


def _get_client(ctx: Context):
    return ctx.request_context.lifespan_context.client


class _ConjunctionFailure(Exception):
    """A failed prerequisite must never become an empty/successful assessment."""


def _report_failures(function):
    @wraps(function)
    async def checked(*args, **kwargs):
        try:
            return await function(*args, **kwargs)
        except _ConjunctionFailure as error:
            return f"Conjunction operation failed: {error}. Earlier changes may remain; no rollback was attempted."
    return checked


async def _send_checked(client, command):
    try:
        result = await client.send_command(command)
    except Exception as error:
        raise _ConjunctionFailure(f"{command}: {error}") from error
    if result.get("ack") != "ACK":
        raise _ConjunctionFailure(f"STK rejected {command}: {result}")
    return result


async def _object_exists(client, path):
    # DoesObjExist requires the application scope and returns ASCII 0 or 1.
    # https://help.agi.com/stk/Subsystems/connectCmds/Content/cmd_DoesObjExist.htm
    result = await _send_checked(client, f"DoesObjExist / {path}")
    data = result.get("data")
    if data == ["1"]:
        return True
    if data == ["0"]:
        return False
    raise _ConjunctionFailure(f"Invalid DoesObjExist response for {path}: {data!r}")


async def _distances(client, **values):
    """Convert API kilometers to current Connect units without changing them."""
    for name, value in values.items():
        if not math.isfinite(value) or value < 0:
            raise _ConjunctionFailure(f"{name} must be finite and nonnegative")
    converted = {name: 0.0 for name, value in values.items() if value == 0}
    values = {name: value for name, value in values.items() if value != 0}
    if not values:
        return converted
    # Official Units_Get output is a semicolon-delimited dimension/unit list.
    # https://help.agi.com/stk/Subsystems/connectCmds/Content/cmd_Units_Get.htm
    result = await _send_checked(client, "Units_Get * Connect")
    units = []
    for entry in " ".join(result.get("data") or []).split(";"):
        parts = entry.strip().split(maxsplit=1)
        if len(parts) == 2 and parts[0] == "Distance":
            units.append(parts[1])
    if len(units) != 1 or any(c in units[0] for c in '\r\n"'):
        raise _ConjunctionFailure("Unable to determine Connect distance units")
    for name, value in values.items():
        # STK performs the conversion, including non-metric user units.
        # https://help.agi.com/stk/Subsystems/connectCmds/Content/cmd_Units_Convert.htm
        result = await _send_checked(
            client, f'Units_Convert * Unit Distance km "{units[0]}" {value}'
        )
        try:
            data = result.get("data") or []
            number = float(data[0]) if len(data) == 1 else math.nan
        except (TypeError, ValueError):
            number = math.nan
        if not math.isfinite(number) or number < 0 or (value > 0 and number == 0):
            raise _ConjunctionFailure(f"Invalid distance conversion for {name}: {data!r}")
        converted[name] = number
    return converted


@mcp.tool()
@_report_failures
async def stk_conjunction(
    ctx: Context,
    action: str,
    # General
    satellite_name: str = "",
    object_path: str = "",
    acat_name: str = "AdvCAT",
    # CAT params
    range_threshold: float = 50.0,
    database_path: str = "",
    filter_apogee_perigee: float = 0.0,
    filter_orbit_path: float = 0.0,
    add_threats: bool = False,
    max_threats: int = 100,
    # ACAT params
    start_time: str = "",
    stop_time: str = "",
    threshold: float = 0.0,
    sample_step_size: float = 0.0,
    # Secondary add
    secondary_path: str = "",
    # Prefilters
    out_of_date: str = "",
    apogee_perigee: float = 0.0,
    orbit_path: float = 0.0,
    time_filter: str = "",
    # Threat volume
    dimension_type: str = "Fixed",
    tangential_km: float = 20.0,
    cross_track_km: float = 10.0,
    normal_km: float = 5.0,
    hard_body_radius_m: float = 0.0,
    # Events / Probability
    sort_by: str = "",
    primary_name: str = "",
    secondary_name: str = "",
    tca_time: str = "",
    method: str = "Alfano",
    # Assess (end-to-end)
    primary_satellite: str = "",
    secondary_satellite: str = "",
    tle_primary_line1: str = "",
    tle_primary_line2: str = "",
    tle_secondary_line1: str = "",
    tle_secondary_line2: str = "",
    threshold_km: float = 5.0,
) -> str:
    """Conjunction Assessment — close approach screening and collision probability.

    Numeric distances are kilometers, converted to current Connect units.
    String prefilter values use Connect units or On/Off. A nonzero single
    sample_step_size is unsupported: STK requires both maximum and minimum.
    assess creates a fresh AdvCAT object per call and reports its name.
    Failed prerequisites stop the operation; earlier changes are not rolled back.

    Actions:
        cat_setup              — Configure basic CAT. Params: satellite_name, range_threshold, database_path, filter_apogee_perigee, filter_orbit_path, add_threats, max_threats
        cat_compute            — Run basic CAT. Params: satellite_name, range_threshold
        acat_setup             — Configure Advanced CAT. Params: acat_name, start_time, stop_time, threshold, sample_step_size
        acat_add_primary      — Add primary (protected) object. Params: object_path, acat_name
        acat_add_secondary    — Add secondary (threat) object. Params: object_path or database_path, acat_name
        acat_set_prefilters   — Set pre-computation filters. Params: acat_name, out_of_date, apogee_perigee, orbit_path, time_filter
        acat_set_threat_volume — Unsupported; returns guidance without changing STK. Params: acat_name, dimension_type, tangential_km, cross_track_km, normal_km, hard_body_radius_m
        acat_compute           — Run Advanced CAT. Params: acat_name
        acat_events            — Get conjunction events. Params: acat_name, sort_by
        acat_probability       — Compute Pc for a pair. Params: acat_name, primary_name, secondary_name, tca_time, method
        assess                 — End-to-end conjunction assessment. Params: primary_satellite, secondary_satellite, tle_*_line1/2, start_time, stop_time, threshold_km
    """
    client = _get_client(ctx)
    if action in {"acat_setup", "assess"} and bool(start_time) != bool(stop_time):
        return "Parameters 'start_time' and 'stop_time' must be supplied together"
    if action == "acat_setup" and sample_step_size != 0:
        return (
            "Unsupported sample_step_size: STK requires both maximum and minimum "
            "SampleStepSize values. No settings were changed; use send_command "
            "with both values in Connect time units."
        )
    if action == "assess":
        if bool(tle_primary_line1) != bool(tle_primary_line2):
            return "Both primary TLE lines must be supplied together"
        if bool(tle_secondary_line1) != bool(tle_secondary_line2):
            return "Both secondary TLE lines must be supplied together"

    # ── cat_setup ────────────────────────────────────────────
    if action == "cat_setup":
        if not satellite_name:
            return "Parameter 'satellite_name' is required"
        if range_threshold <= 0:
            return "Parameter 'range_threshold' must be positive"
        distances = await _distances(
            client, range_threshold=range_threshold,
            filter_apogee_perigee=filter_apogee_perigee,
            filter_orbit_path=filter_orbit_path,
        )
        results = []
        await _send_checked(
            client,
            f"CAT */Satellite/{satellite_name} Range {distances['range_threshold']}"
        )
        results.append(f"Range threshold: {range_threshold} km")

        if database_path:
            await _send_checked(
                client,
                f'CAT */Satellite/{satellite_name} Database "{database_path}"'
            )
            results.append(f"Database: {database_path}")

        if filter_apogee_perigee > 0:
            await _send_checked(
                client,
                f"CAT */Satellite/{satellite_name} Filter ApogeePerigee {distances['filter_apogee_perigee']}"
            )
            results.append(f"Apogee/Perigee filter: {filter_apogee_perigee} km")

        if filter_orbit_path > 0:
            await _send_checked(
                client,
                f"CAT */Satellite/{satellite_name} Filter OrbitPath {distances['filter_orbit_path']}"
            )
            results.append(f"Orbit path filter: {filter_orbit_path} km")

        if add_threats:
            await _send_checked(
                client,
                f"CAT */Satellite/{satellite_name} AddThreats On {max_threats}"
            )
            results.append(f"Add threats: On (max {max_threats})")

        return "CAT configured:\n" + "\n".join(results)

    # ── cat_compute ──────────────────────────────────────────
    elif action == "cat_compute":
        if not satellite_name:
            return "Parameter 'satellite_name' is required"
        if range_threshold <= 0:
            return "Parameter 'range_threshold' must be positive"
        distances = await _distances(client, range_threshold=range_threshold)
        r = await client.send_command(
            f"CAT_RM */Satellite/{satellite_name} Range {distances['range_threshold']}"
        )
        if r["ack"] == "ACK" and r["data"]:
            return (
                f"Close approaches for '{satellite_name}' (threshold: {range_threshold} km):\n"
                + "\n".join(r["data"])
            )
        elif r["ack"] == "ACK":
            return f"No close approaches found within {range_threshold} km"
        return f"Failed to compute: {r}"

    # ── acat_setup ───────────────────────────────────────────
    elif action == "acat_setup":
        distances = await _distances(client, threshold=threshold) if threshold != 0 else {}
        results = []
        # Create AdvCAT if not exists
        if not await _object_exists(client, f"*/AdvCAT/{acat_name}"):
            await _send_checked(client, f"New / */AdvCAT {acat_name}")
            results.append(f"AdvCAT '{acat_name}' created")

        if start_time and stop_time:
            await _send_checked(
                client,
                f'ACAT */AdvCAT/{acat_name} TimePeriod "{start_time}" "{stop_time}"'
            )
            results.append(f"Time period: {start_time} to {stop_time}")

        if threshold > 0:
            await _send_checked(
                client,
                f"ACAT */AdvCAT/{acat_name} Threshold {distances['threshold']}"
            )
            results.append(f"Threshold: {threshold} km")

        return "ACAT configured:\n" + "\n".join(results) if results else "ACAT setup complete"

    # ── acat_add_primary ─────────────────────────────────────
    elif action == "acat_add_primary":
        if not object_path:
            return "Parameter 'object_path' is required (e.g. 'Satellite/Sat1')"
        r = await client.send_command(
            f"ACAT */AdvCAT/{acat_name} Primary Add {object_path}"
        )
        if r["ack"] == "ACK":
            return f"Primary added: {object_path}"
        return f"Failed: {r}"

    # ── acat_add_secondary ───────────────────────────────────
    elif action == "acat_add_secondary":
        if secondary_path:
            r = await client.send_command(
                f"ACAT */AdvCAT/{acat_name} Secondary Add {secondary_path}"
            )
            if r["ack"] == "ACK":
                return f"Secondary added: {secondary_path}"
            return f"Failed: {r}"
        elif database_path:
            r = await client.send_command(
                f'ACAT */AdvCAT/{acat_name} Secondary AddDatabase "{database_path}"'
            )
            if r["ack"] == "ACK":
                return f"Secondaries loaded from: {database_path}"
            return f"Failed: {r}"
        return "Provide either 'secondary_path' (single object) or 'database_path' (bulk)"

    # ── acat_set_prefilters ──────────────────────────────────
    elif action == "acat_set_prefilters":
        distances = await _distances(
            client, apogee_perigee=apogee_perigee, orbit_path=orbit_path,
        )
        results = []
        if out_of_date:
            await _send_checked(
                client,
                f"ACAT */AdvCAT/{acat_name} PreFilters OutOfDate {out_of_date}"
            )
            results.append(f"OutOfDate: {out_of_date}")
        if apogee_perigee > 0:
            await _send_checked(
                client,
                f"ACAT */AdvCAT/{acat_name} PreFilters ApogeePerigee {distances['apogee_perigee']}"
            )
            results.append(f"ApogeePerigee: {apogee_perigee} km")
        if orbit_path > 0:
            await _send_checked(
                client,
                f"ACAT */AdvCAT/{acat_name} PreFilters OrbitPath {distances['orbit_path']}"
            )
            results.append(f"OrbitPath: {orbit_path} km")
        if time_filter:
            await _send_checked(
                client,
                f"ACAT */AdvCAT/{acat_name} PreFilters Time {time_filter}"
            )
            results.append(f"Time: {time_filter}")
        return "Prefilters:\n" + "\n".join(results) if results else "No filters changed"

    # ── acat_set_threat_volume ───────────────────────────────
    elif action == "acat_set_threat_volume":
        # Dimensions and hard-body radius are per-object ACAT Primary/Secondary
        # Add parameters. ScaleFactor does not apply these requested values.
        return (
            "Unsupported action: acat_set_threat_volume does not configure "
            "dimensions or hard-body radius; no STK settings were changed. "
            "Configure the intended primary/secondary object's threat volume "
            "in STK, or use send_command with the ACAT Primary/Secondary Add "
            "parameters appropriate to your STK version and Connect units. "
            "See https://help.agi.com/stk/Subsystems/connectCmds/Content/cmd_ACAT.htm"
        )

    # ── acat_compute ─────────────────────────────────────────
    elif action == "acat_compute":
        r = await client.send_command(f"ACAT */AdvCAT/{acat_name} Compute")
        if r["ack"] == "ACK":
            return f"Advanced CAT computation completed for '{acat_name}'"
        return f"ACAT computation failed: {r}"

    # ── acat_events ──────────────────────────────────────────
    elif action == "acat_events":
        cmd = f"ACATEvents_RM */AdvCAT/{acat_name}"
        if sort_by:
            cmd += f" Sort {sort_by}"
        r = await client.send_command(cmd)
        if r["ack"] == "ACK" and r["data"]:
            return (
                f"Conjunction events ({len(r['data'])} events):\n"
                + "\n".join(r["data"])
            )
        elif r["ack"] == "ACK":
            return "No conjunction events found"
        return f"Failed: {r}"

    # ── acat_probability ─────────────────────────────────────
    elif action == "acat_probability":
        if not primary_name or not secondary_name or not tca_time:
            return "Parameters 'primary_name', 'secondary_name', 'tca_time' are required"
        r = await client.send_command(
            f'ACATProbability_R */AdvCAT/{acat_name} '
            f"Primary {primary_name} Secondary {secondary_name} "
            f'TCA "{tca_time}" Method {method}'
        )
        if r["ack"] == "ACK" and r["data"]:
            return (
                f"Pc ({primary_name} vs {secondary_name}):\n"
                + "\n".join(r["data"])
            )
        elif r["ack"] == "ACK":
            return "No probability data available"
        return f"Failed: {r}"

    # ── assess (end-to-end) ──────────────────────────────────
    elif action == "assess":
        if not primary_satellite or not secondary_satellite:
            return "Parameters 'primary_satellite' and 'secondary_satellite' are required"
        distances = await _distances(client, threshold_km=threshold_km)
        steps = []
        if not await _object_exists(client, f"*/Satellite/{primary_satellite}"):
            return f"Primary satellite '{primary_satellite}' does not exist"

        # Create secondary if needed
        if not await _object_exists(client, f"*/Satellite/{secondary_satellite}"):
            if not tle_secondary_line1 or not tle_secondary_line2:
                return (
                    f"Secondary satellite '{secondary_satellite}' does not exist; "
                    "provide both secondary TLE lines to create and initialize it"
                )
            await _send_checked(client, f"New / */Satellite {secondary_satellite}")
            steps.append(f"Created satellite: {secondary_satellite}")

        # Apply each requested orbit and verify propagation before assessment.
        for satellite, line1, line2 in (
            (primary_satellite, tle_primary_line1, tle_primary_line2),
            (secondary_satellite, tle_secondary_line1, tle_secondary_line2),
        ):
            if not line1:
                continue
            await _send_checked(
                client, f'SetState */Satellite/{satellite} TLE "{line1}" "{line2}"'
            )
            try:
                propagated = await _propagate_satellite_result(ctx, satellite)
            except Exception as error:
                raise _ConjunctionFailure(f"Failed to propagate {satellite}: {error}") from error
            if propagated.get("ack") != "ACK":
                raise _ConjunctionFailure(f"Failed to propagate {satellite}: {propagated}")
            steps.append(f"TLE set for {satellite}")

        # Create AdvCAT, configure, compute
        assessment_name = f"ConjunctionAssessment_{uuid4().hex[:12]}"
        # NoDefault prevents configured object defaults from adding old pairs.
        await _send_checked(client, f"New / */AdvCAT {assessment_name} NoDefault")
        steps.append(f"Assessment object: {assessment_name}")
        if start_time and stop_time:
            await _send_checked(
                client,
                f'ACAT */AdvCAT/{assessment_name} TimePeriod "{start_time}" "{stop_time}"'
            )
            steps.append(f"Time: {start_time} to {stop_time}")
        await _send_checked(
            client,
            f"ACAT */AdvCAT/{assessment_name} Threshold {distances['threshold_km']}"
        )
        await _send_checked(
            client,
            f"ACAT */AdvCAT/{assessment_name} Primary Add Satellite/{primary_satellite}"
        )
        await _send_checked(
            client,
            f"ACAT */AdvCAT/{assessment_name} Secondary Add Satellite/{secondary_satellite}"
        )
        steps.append(f"Primary: {primary_satellite}, Secondary: {secondary_satellite}")

        await _send_checked(client, f"ACAT */AdvCAT/{assessment_name} Compute")
        steps.append("Computation completed")

        ev = await client.send_command(f"ACATEvents_RM */AdvCAT/{assessment_name}")
        if ev["ack"] == "ACK" and ev["data"]:
            steps.append(f"\nEvents ({len(ev['data'])} events):")
            steps.append("\n".join(ev["data"]))
        elif ev["ack"] == "ACK":
            steps.append("No conjunction events found")
        else:
            return "Event retrieval failed:\n" + "\n".join(steps) + f"\nError: {ev}"

        return "\n".join(steps)

    else:
        return (
            f"Unknown action '{action}'. Valid actions: "
            "cat_setup, cat_compute, acat_setup, acat_add_primary, acat_add_secondary, "
            "acat_set_prefilters, acat_set_threat_volume, acat_compute, acat_events, "
            "acat_probability, assess"
        )
