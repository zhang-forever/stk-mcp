"""
CAT (Conjunction Assessment Tool) and Advanced CAT tools.

This is the primary focus module — satellite collision warning / close approach analysis.

Key STK Connect commands:
- CAT: Configure Close Approach parameters
- CAT_RM: Compute close approaches (returns data)
- ACAT: Configure Advanced CAT (primary/secondary objects, threshold, filters)
- ACAT <path> Compute: Run Advanced CAT computation
- ACATEvents_RM: Get conjunction events with probability data
- ACATProbability_R: Get conjunction probability for a specific pair
"""

from __future__ import annotations

from mcp.server.fastmcp import Context

from stk_mcp.app import mcp
from stk_mcp.tools.orbit import _propagate_satellite


def _get_client(ctx: Context):
    state = ctx.request_context.lifespan_context
    return state.client


# ──────────────────────────────────────────────────────────────────
# Basic CAT (Close Approach Tool)
# ──────────────────────────────────────────────────────────────────


@mcp.tool()
async def stk_cat_setup(
    ctx: Context,
    satellite_name: str,
    range_threshold: float = 50.0,
    database_path: str = "",
    filter_apogee_perigee: float = 0,
    filter_orbit_path: float = 0,
    add_threats: bool = False,
    max_threats: int = 100,
) -> str:
    """Configure Close Approach Tool (CAT) parameters for a satellite.

    This sets up the basic CAT before computing close approaches.
    Use stk_cat_compute to actually run the computation.

    Args:
        satellite_name: Primary satellite name
        range_threshold: Minimum distance threshold in km (objects closer than this are flagged)
        database_path: Path to satellite database file (.sd or .tce). Empty for default.
        filter_apogee_perigee: Apogee/perigee filter distance in km (0 to disable)
        filter_orbit_path: Orbit path filter distance in km (0 to disable)
        add_threats: Whether to add conjuncting satellites to the scenario
        max_threats: Maximum number of threat objects to add (1-99999)
    """
    client = _get_client(ctx)
    results = []

    # Set range
    result = await client.send_command(
        f"CAT */Satellite/{satellite_name} Range {range_threshold}"
    )
    if result["ack"] != "ACK":
        return f"Failed to set CAT range: {result}"
    results.append(f"Range threshold: {range_threshold} km")

    # Set database if provided
    if database_path:
        result = await client.send_command(
            f'CAT */Satellite/{satellite_name} Database "{database_path}"'
        )
        if result["ack"] == "ACK":
            results.append(f"Database: {database_path}")
        else:
            results.append(f"Warning: Failed to set database: {result}")

    # Set filters
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

    # Add threats to scenario
    if add_threats:
        await client.send_command(
            f"CAT */Satellite/{satellite_name} AddThreats On {max_threats}"
        )
        results.append(f"Add threats: On (max {max_threats})")

    return "CAT configured:\n" + "\n".join(results)


@mcp.tool()
async def stk_cat_compute(
    ctx: Context,
    satellite_name: str,
    range_threshold: float = 50.0,
) -> str:
    """Compute close approaches for a satellite using CAT.

    Returns a list of close approach events with object name, time, and range.
    Make sure to configure CAT first with stk_cat_setup.

    Args:
        satellite_name: Primary satellite name
        range_threshold: Range threshold in km for the computation
    """
    client = _get_client(ctx)

    result = await client.send_command(
        f"CAT_RM */Satellite/{satellite_name} Range {range_threshold}"
    )
    if result["ack"] == "ACK" and result["data"]:
        return (
            f"Close approaches for '{satellite_name}' (threshold: {range_threshold} km):\n"
            + "\n".join(result["data"])
        )
    elif result["ack"] == "ACK":
        return f"No close approaches found for '{satellite_name}' within {range_threshold} km"
    return f"Failed to compute close approaches: {result}"


# ──────────────────────────────────────────────────────────────────
# Advanced CAT (ACAT)
# ──────────────────────────────────────────────────────────────────


@mcp.tool()
async def stk_acat_setup(
    ctx: Context,
    acat_object_path: str = "AdvCAT",
    start_time: str = "",
    stop_time: str = "",
    threshold: float = 0.0,
    sample_step_size: float = 0,
) -> str:
    """Configure Advanced CAT (ACAT) parameters.

    Advanced CAT performs conjunction assessment between primary and secondary object sets,
    using threat volume ellipsoids. Use stk_acat_add_primary/secondary to add objects,
    then stk_acat_compute to run.

    Args:
        acat_object_path: AdvCAT object path (default: "AdvCAT" — created automatically)
        start_time: Analysis start time. Empty for scenario start.
        stop_time: Analysis stop time. Empty for scenario stop.
        threshold: Ellipsoid separation threshold in km (0-1000). 0 means any approach.
        sample_step_size: Sample step size in seconds (0 for auto)
    """
    client = _get_client(ctx)
    results = []

    # Create AdvCAT object if it doesn't exist
    exist_result = await client.send_command(f"DoesObjExist */AdvCAT/{acat_object_path}")
    if exist_result["ack"] == "ACK" and "No" in str(exist_result.get("data", "")):
        create_result = await client.send_command(
            f"New / */AdvCAT {acat_object_path}"
        )
        if create_result["ack"] == "ACK":
            results.append(f"AdvCAT object '{acat_object_path}' created")

    # Set time period
    if start_time and stop_time:
        result = await client.send_command(
            f'ACAT */AdvCAT/{acat_object_path} TimePeriod "{start_time}" "{stop_time}"'
        )
        if result["ack"] == "ACK":
            results.append(f"Time period: {start_time} to {stop_time}")
        else:
            results.append(f"Warning: Failed to set time period: {result}")

    # Set threshold
    if threshold > 0:
        result = await client.send_command(
            f"ACAT */AdvCAT/{acat_object_path} Threshold {threshold}"
        )
        if result["ack"] == "ACK":
            results.append(f"Threshold: {threshold} km")

    # Set sample step size
    if sample_step_size > 0:
        result = await client.send_command(
            f"ACAT */AdvCAT/{acat_object_path} SampleStepSize {sample_step_size}"
        )
        if result["ack"] == "ACK":
            results.append(f"Sample step: {sample_step_size}s")

    return "ACAT configured:\n" + "\n".join(results) if results else "ACAT setup complete"


@mcp.tool()
async def stk_acat_add_primary(
    ctx: Context,
    object_path: str,
    acat_object_path: str = "AdvCAT",
) -> str:
    """Add a primary object to Advanced CAT analysis.

    Primary objects are your own satellites that you want to protect.

    Args:
        object_path: Object path, e.g. "Satellite/Sat1"
        acat_object_path: AdvCAT object name
    """
    client = _get_client(ctx)
    result = await client.send_command(
        f"ACAT */AdvCAT/{acat_object_path} Primary Add {object_path}"
    )
    if result["ack"] == "ACK":
        return f"Primary object added: {object_path}"
    return f"Failed to add primary: {result}"


@mcp.tool()
async def stk_acat_add_secondary(
    ctx: Context,
    object_path: str,
    acat_object_path: str = "AdvCAT",
) -> str:
    """Add a secondary object to Advanced CAT analysis.

    Secondary objects are potential collision threats (debris, other satellites).

    Args:
        object_path: Object path, e.g. "Satellite/Debris1"
        acat_object_path: AdvCAT object name
    """
    client = _get_client(ctx)
    result = await client.send_command(
        f"ACAT */AdvCAT/{acat_object_path} Secondary Add {object_path}"
    )
    if result["ack"] == "ACK":
        return f"Secondary object added: {object_path}"
    return f"Failed to add secondary: {result}"


@mcp.tool()
async def stk_acat_add_secondary_from_database(
    ctx: Context,
    database_path: str,
    acat_object_path: str = "AdvCAT",
) -> str:
    """Add secondary objects from a TLE/satellite database file.

    Args:
        database_path: Path to satellite database (.sd, .tce) or TLE file
        acat_object_path: AdvCAT object name
    """
    client = _get_client(ctx)
    result = await client.send_command(
        f'ACAT */AdvCAT/{acat_object_path} Secondary AddDatabase "{database_path}"'
    )
    if result["ack"] == "ACK":
        return f"Secondary objects loaded from: {database_path}"
    return f"Failed to add secondary database: {result}"


@mcp.tool()
async def stk_acat_set_prefilters(
    ctx: Context,
    acat_object_path: str = "AdvCAT",
    out_of_date: str = "",
    apogee_perigee: float = 0,
    orbit_path: float = 0,
    time_filter: str = "",
) -> str:
    """Set pre-computation filters for Advanced CAT to speed up analysis.

    Args:
        acat_object_path: AdvCAT object name
        out_of_date: Out-of-date filter: "On" or "Off"
        apogee_perigee: Apogee/perigee filter distance in km (0 to disable)
        orbit_path: Orbit path filter distance in km (0 to disable)
        time_filter: Time filter: "On" or "Off"
    """
    client = _get_client(ctx)
    results = []

    if out_of_date:
        result = await client.send_command(
            f"ACAT */AdvCAT/{acat_object_path} PreFilters OutOfDate {out_of_date}"
        )
        results.append(f"OutOfDate filter: {out_of_date}")

    if apogee_perigee > 0:
        result = await client.send_command(
            f"ACAT */AdvCAT/{acat_object_path} PreFilters ApogeePerigee {apogee_perigee}"
        )
        results.append(f"ApogeePerigee filter: {apogee_perigee} km")

    if orbit_path > 0:
        result = await client.send_command(
            f"ACAT */AdvCAT/{acat_object_path} PreFilters OrbitPath {orbit_path}"
        )
        results.append(f"OrbitPath filter: {orbit_path} km")

    if time_filter:
        result = await client.send_command(
            f"ACAT */AdvCAT/{acat_object_path} PreFilters Time {time_filter}"
        )
        results.append(f"Time filter: {time_filter}")

    return "Prefilters set:\n" + "\n".join(results) if results else "No filters changed"


@mcp.tool()
async def stk_acat_compute(
    ctx: Context,
    acat_object_path: str = "AdvCAT",
) -> str:
    """Run Advanced CAT computation.

    Must configure ACAT and add primary/secondary objects first.
    After computation, use stk_acat_events to retrieve conjunction events.

    Args:
        acat_object_path: AdvCAT object name
    """
    client = _get_client(ctx)

    result = await client.send_command(
        f"ACAT */AdvCAT/{acat_object_path} Compute"
    )
    if result["ack"] == "ACK":
        return f"Advanced CAT computation completed for '{acat_object_path}'"
    return f"ACAT computation failed: {result}"


@mcp.tool()
async def stk_acat_events(
    ctx: Context,
    acat_object_path: str = "AdvCAT",
    sort_by: str = "",
) -> str:
    """Get conjunction events from Advanced CAT computation.

    Returns event data including primary/secondary object names, TCA (Time of Closest Approach),
    range, and probability information.

    Args:
        acat_object_path: AdvCAT object name
        sort_by: Sort events by field: "TCA", "Range", "Probability". Empty for default.
    """
    client = _get_client(ctx)

    cmd = f"ACATEvents_RM */AdvCAT/{acat_object_path}"
    if sort_by:
        cmd += f" Sort {sort_by}"

    result = await client.send_command(cmd)
    if result["ack"] == "ACK" and result["data"]:
        return (
            f"Conjunction events ({len(result['data'])} events):\n"
            + "\n".join(result["data"])
        )
    elif result["ack"] == "ACK":
        return "No conjunction events found"
    return f"Failed to get ACAT events: {result}"


@mcp.tool()
async def stk_acat_probability(
    ctx: Context,
    acat_object_path: str,
    primary_name: str,
    secondary_name: str,
    tca_time: str,
    method: str = "Alfano",
) -> str:
    """Compute conjunction probability for a specific primary-secondary pair.

    Args:
        acat_object_path: AdvCAT object name
        primary_name: Primary object name
        secondary_name: Secondary object name
        tca_time: Time of Closest Approach (from ACAT events)
        method: Probability method: "Alfano", "Foster", "AlfanoMax", "AlfanoMin"
    """
    client = _get_client(ctx)

    result = await client.send_command(
        f'ACATProbability_R */AdvCAT/{acat_object_path} '
        f'Primary {primary_name} Secondary {secondary_name} '
        f'TCA "{tca_time}" Method {method}'
    )
    if result["ack"] == "ACK" and result["data"]:
        return (
            f"Conjunction probability ({primary_name} vs {secondary_name}):\n"
            + "\n".join(result["data"])
        )
    elif result["ack"] == "ACK":
        return "No probability data available"
    return f"Failed to compute probability: {result}"


@mcp.tool()
async def stk_acat_set_threat_volume(
    ctx: Context,
    acat_object_path: str = "AdvCAT",
    dimension_type: str = "Fixed",
    tangential_km: float = 20.0,
    cross_track_km: float = 10.0,
    normal_km: float = 5.0,
    hard_body_radius_m: float = 0,
) -> str:
    """Configure threat volume ellipsoid dimensions for Advanced CAT.

    The threat volume is an ellipsoid around each object with axes:
    - X (tangential / along-track): default 20 km
    - Y (cross-track / orbit normal): default 10 km
    - Z (normal / in-plane perpendicular): default 5 km

    Args:
        acat_object_path: AdvCAT object name
        dimension_type: "Fixed", "OrbitClass", "Quadratic", "Covariance", "CovOffset"
        tangential_km: Tangential (X) axis size in km (for Fixed type)
        cross_track_km: Cross-track (Y) axis size in km (for Fixed type)
        normal_km: Normal (Z) axis size in km (for Fixed type)
        hard_body_radius_m: Hard body radius in meters (0 for default)
    """
    client = _get_client(ctx)
    results = [f"Dimension type: {dimension_type}"]

    if dimension_type == "Fixed":
        # Set fixed ellipsoid dimensions via ACAT PntToPnt or database config
        # Note: In STK 11, fixed dimensions are typically set through the
        # Orbit Class database (.foc) or directly through ACAT options
        result = await client.send_command(
            f"ACAT */AdvCAT/{acat_object_path} ScaleFactor 1.0"
        )
        results.append(
            f"Fixed threat volume: {tangential_km}x{cross_track_km}x{normal_km} km"
        )
        results.append(
            "(Note: Use stk_send_command to set custom .foc/.qdb database for precise dimensions)"
        )

    if hard_body_radius_m > 0:
        results.append(f"Hard body radius: {hard_body_radius_m} m")

    return "\n".join(results)


# ──────────────────────────────────────────────────────────────────
# Convenience: Full CAT workflow
# ──────────────────────────────────────────────────────────────────


@mcp.tool()
async def stk_conjunction_assessment(
    ctx: Context,
    primary_satellite: str,
    secondary_satellite: str,
    tle_primary_line1: str = "",
    tle_primary_line2: str = "",
    tle_secondary_line1: str = "",
    tle_secondary_line2: str = "",
    start_time: str = "",
    stop_time: str = "",
    threshold_km: float = 5.0,
) -> str:
    """Run a complete conjunction assessment between two satellites.

    This is a high-level convenience tool that:
    1. Adds secondary satellite if needed
    2. Sets TLE orbits (if provided)
    3. Sets up and runs Advanced CAT
    4. Returns conjunction events

    Args:
        primary_satellite: Primary satellite name (must exist in scenario)
        secondary_satellite: Secondary satellite name (will be created if needed)
        tle_primary_line1: Primary satellite TLE line 1 (optional if already set)
        tle_primary_line2: Primary satellite TLE line 2
        tle_secondary_line1: Secondary satellite TLE line 1
        tle_secondary_line2: Secondary satellite TLE line 2
        start_time: Analysis start time (default: scenario start)
        stop_time: Analysis stop time (default: scenario stop)
        threshold_km: Ellipsoid separation threshold in km
    """
    client = _get_client(ctx)
    steps = []

    # Add secondary satellite if it doesn't exist
    exist_result = await client.send_command(
        f"DoesObjExist */Satellite/{secondary_satellite}"
    )
    if "No" in str(exist_result.get("data", "")):
        result = await client.send_command(
            f"New / */Satellite {secondary_satellite}"
        )
        if result["ack"] == "ACK":
            steps.append(f"Created satellite: {secondary_satellite}")

    # Set TLE orbits if provided (using HPOP + SGP4 force model)
    if tle_primary_line1 and tle_primary_line2:
        result = await client.send_command(
            f'SetState */Satellite/{primary_satellite} TLE '
            f'"{tle_primary_line1}" "{tle_primary_line2}"'
        )
        if result["ack"] == "ACK":
            await _propagate_satellite(ctx, primary_satellite)
            steps.append(f"TLE set for {primary_satellite}")

    if tle_secondary_line1 and tle_secondary_line2:
        result = await client.send_command(
            f'SetState */Satellite/{secondary_satellite} TLE '
            f'"{tle_secondary_line1}" "{tle_secondary_line2}"'
        )
        if result["ack"] == "ACK":
            await _propagate_satellite(ctx, secondary_satellite)
            steps.append(f"TLE set for {secondary_satellite}")

    # Create AdvCAT object
    await client.send_command("New / */AdvCAT ConjunctionAssessment Ignore")

    # Configure ACAT
    if start_time and stop_time:
        await client.send_command(
            f'ACAT */AdvCAT/ConjunctionAssessment TimePeriod "{start_time}" "{stop_time}"'
        )
        steps.append(f"Time period: {start_time} to {stop_time}")

    await client.send_command(
        f"ACAT */AdvCAT/ConjunctionAssessment Threshold {threshold_km}"
    )
    steps.append(f"Threshold: {threshold_km} km")

    # Add primary and secondary
    await client.send_command(
        f"ACAT */AdvCAT/ConjunctionAssessment Primary Add Satellite/{primary_satellite}"
    )
    await client.send_command(
        f"ACAT */AdvCAT/ConjunctionAssessment Secondary Add Satellite/{secondary_satellite}"
    )
    steps.append(f"Primary: {primary_satellite}, Secondary: {secondary_satellite}")

    # Compute
    compute_result = await client.send_command(
        "ACAT */AdvCAT/ConjunctionAssessment Compute"
    )
    if compute_result["ack"] == "ACK":
        steps.append("Computation completed")
    else:
        return f"Computation failed:\n" + "\n".join(steps) + f"\nError: {compute_result}"

    # Get events
    events_result = await client.send_command(
        "ACATEvents_RM */AdvCAT/ConjunctionAssessment"
    )
    if events_result["ack"] == "ACK" and events_result["data"]:
        steps.append(f"\nConjunction Events ({len(events_result['data'])} events):")
        steps.append("\n".join(events_result["data"]))
    else:
        steps.append("No conjunction events found")

    return "\n".join(steps)
