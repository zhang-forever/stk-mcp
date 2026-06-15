"""stk_conjunction — Conjunction Assessment (CAT + Advanced CAT) for collision warning."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from stk_mcp.app import mcp
from stk_mcp.tools.orbit import _propagate_satellite


def _get_client(ctx: Context):
    return ctx.request_context.lifespan_context.client


@mcp.tool()
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

    Actions:
        cat_setup              — Configure basic CAT. Params: satellite_name, range_threshold, database_path, filter_apogee_perigee, filter_orbit_path, add_threats, max_threats
        cat_compute            — Run basic CAT. Params: satellite_name, range_threshold
        acat_setup             — Configure Advanced CAT. Params: acat_name, start_time, stop_time, threshold, sample_step_size
        acat_add_primary      — Add primary (protected) object. Params: object_path, acat_name
        acat_add_secondary    — Add secondary (threat) object. Params: object_path or database_path, acat_name
        acat_set_prefilters   — Set pre-computation filters. Params: acat_name, out_of_date, apogee_perigee, orbit_path, time_filter
        acat_set_threat_volume — Configure threat volume ellipsoid. Params: acat_name, dimension_type, tangential_km, cross_track_km, normal_km, hard_body_radius_m
        acat_compute           — Run Advanced CAT. Params: acat_name
        acat_events            — Get conjunction events. Params: acat_name, sort_by
        acat_probability       — Compute Pc for a pair. Params: acat_name, primary_name, secondary_name, tca_time, method
        assess                 — End-to-end conjunction assessment. Params: primary_satellite, secondary_satellite, tle_*_line1/2, start_time, stop_time, threshold_km
    """
    client = _get_client(ctx)

    # ── cat_setup ────────────────────────────────────────────
    if action == "cat_setup":
        if not satellite_name:
            return "Parameter 'satellite_name' is required"
        results = []
        r = await client.send_command(
            f"CAT */Satellite/{satellite_name} Range {range_threshold}"
        )
        if r["ack"] != "ACK":
            return f"Failed to set CAT range: {r}"
        results.append(f"Range threshold: {range_threshold} km")

        if database_path:
            r = await client.send_command(
                f'CAT */Satellite/{satellite_name} Database "{database_path}"'
            )
            if r["ack"] == "ACK":
                results.append(f"Database: {database_path}")

        if filter_apogee_perigee > 0:
            await client.send_command(
                f"CAT */Satellite/{satellite_name} Filter ApogeePerigee {filter_apogee_perigee}"
            )
            results.append(f"Apogee/Perigee filter: {filter_apogee_perigee} km")

        if filter_orbit_path > 0:
            await client.send_command(
                f"CAT */Satellite/{satellite_name} Filter OrbitPath {filter_orbit_path}"
            )
            results.append(f"Orbit path filter: {filter_orbit_path} km")

        if add_threats:
            await client.send_command(
                f"CAT */Satellite/{satellite_name} AddThreats On {max_threats}"
            )
            results.append(f"Add threats: On (max {max_threats})")

        return "CAT configured:\n" + "\n".join(results)

    # ── cat_compute ──────────────────────────────────────────
    elif action == "cat_compute":
        if not satellite_name:
            return "Parameter 'satellite_name' is required"
        r = await client.send_command(
            f"CAT_RM */Satellite/{satellite_name} Range {range_threshold}"
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
        results = []
        # Create AdvCAT if not exists
        exist = await client.send_command(f"DoesObjExist */AdvCAT/{acat_name}")
        if exist["ack"] == "ACK" and "No" in str(exist.get("data", "")):
            cr = await client.send_command(f"New / */AdvCAT {acat_name}")
            if cr["ack"] == "ACK":
                results.append(f"AdvCAT '{acat_name}' created")

        if start_time and stop_time:
            r = await client.send_command(
                f'ACAT */AdvCAT/{acat_name} TimePeriod "{start_time}" "{stop_time}"'
            )
            if r["ack"] == "ACK":
                results.append(f"Time period: {start_time} to {stop_time}")

        if threshold > 0:
            r = await client.send_command(
                f"ACAT */AdvCAT/{acat_name} Threshold {threshold}"
            )
            if r["ack"] == "ACK":
                results.append(f"Threshold: {threshold} km")

        if sample_step_size > 0:
            r = await client.send_command(
                f"ACAT */AdvCAT/{acat_name} SampleStepSize {sample_step_size}"
            )
            if r["ack"] == "ACK":
                results.append(f"Sample step: {sample_step_size}s")

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
        results = []
        if out_of_date:
            await client.send_command(
                f"ACAT */AdvCAT/{acat_name} PreFilters OutOfDate {out_of_date}"
            )
            results.append(f"OutOfDate: {out_of_date}")
        if apogee_perigee > 0:
            await client.send_command(
                f"ACAT */AdvCAT/{acat_name} PreFilters ApogeePerigee {apogee_perigee}"
            )
            results.append(f"ApogeePerigee: {apogee_perigee} km")
        if orbit_path > 0:
            await client.send_command(
                f"ACAT */AdvCAT/{acat_name} PreFilters OrbitPath {orbit_path}"
            )
            results.append(f"OrbitPath: {orbit_path} km")
        if time_filter:
            await client.send_command(
                f"ACAT */AdvCAT/{acat_name} PreFilters Time {time_filter}"
            )
            results.append(f"Time: {time_filter}")
        return "Prefilters:\n" + "\n".join(results) if results else "No filters changed"

    # ── acat_set_threat_volume ───────────────────────────────
    elif action == "acat_set_threat_volume":
        results = [f"Dimension type: {dimension_type}"]
        r = await client.send_command(
            f"ACAT */AdvCAT/{acat_name} ScaleFactor 1.0"
        )
        results.append(
            f"Fixed threat volume: {tangential_km}x{cross_track_km}x{normal_km} km"
        )
        if hard_body_radius_m > 0:
            results.append(f"Hard body radius: {hard_body_radius_m} m")
        results.append("(Use send_command for precise .foc/.qdb database config)")
        return "\n".join(results)

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
        steps = []

        # Create secondary if needed
        exist = await client.send_command(
            f"DoesObjExist */Satellite/{secondary_satellite}"
        )
        if "No" in str(exist.get("data", "")):
            r = await client.send_command(f"New / */Satellite {secondary_satellite}")
            if r["ack"] == "ACK":
                steps.append(f"Created satellite: {secondary_satellite}")

        # Set TLE orbits
        if tle_primary_line1 and tle_primary_line2:
            r = await client.send_command(
                f'SetState */Satellite/{primary_satellite} TLE '
                f'"{tle_primary_line1}" "{tle_primary_line2}"'
            )
            if r["ack"] == "ACK":
                await _propagate_satellite(ctx, primary_satellite)
                steps.append(f"TLE set for {primary_satellite}")

        if tle_secondary_line1 and tle_secondary_line2:
            r = await client.send_command(
                f'SetState */Satellite/{secondary_satellite} TLE '
                f'"{tle_secondary_line1}" "{tle_secondary_line2}"'
            )
            if r["ack"] == "ACK":
                await _propagate_satellite(ctx, secondary_satellite)
                steps.append(f"TLE set for {secondary_satellite}")

        # Create AdvCAT, configure, compute
        await client.send_command("New / */AdvCAT ConjunctionAssessment Ignore")
        if start_time and stop_time:
            await client.send_command(
                f'ACAT */AdvCAT/ConjunctionAssessment TimePeriod "{start_time}" "{stop_time}"'
            )
            steps.append(f"Time: {start_time} to {stop_time}")
        await client.send_command(
            f"ACAT */AdvCAT/ConjunctionAssessment Threshold {threshold_km}"
        )
        await client.send_command(
            f"ACAT */AdvCAT/ConjunctionAssessment Primary Add Satellite/{primary_satellite}"
        )
        await client.send_command(
            f"ACAT */AdvCAT/ConjunctionAssessment Secondary Add Satellite/{secondary_satellite}"
        )
        steps.append(f"Primary: {primary_satellite}, Secondary: {secondary_satellite}")

        cr = await client.send_command("ACAT */AdvCAT/ConjunctionAssessment Compute")
        if cr["ack"] != "ACK":
            return "Computation failed:\n" + "\n".join(steps) + f"\nError: {cr}"
        steps.append("Computation completed")

        ev = await client.send_command("ACATEvents_RM */AdvCAT/ConjunctionAssessment")
        if ev["ack"] == "ACK" and ev["data"]:
            steps.append(f"\nEvents ({len(ev['data'])} events):")
            steps.append("\n".join(ev["data"]))
        else:
            steps.append("No conjunction events found")

        return "\n".join(steps)

    else:
        return (
            f"Unknown action '{action}'. Valid actions: "
            "cat_setup, cat_compute, acat_setup, acat_add_primary, acat_add_secondary, "
            "acat_set_prefilters, acat_set_threat_volume, acat_compute, acat_events, "
            "acat_probability, assess"
        )
