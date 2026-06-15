"""Orbit and propagation tools: SetState via TLE/Classical/Cartesian, propagate."""

from __future__ import annotations

import logging

from mcp.server.fastmcp import Context

from stk_mcp.app import mcp

logger = logging.getLogger("stk_mcp.tools.orbit")


def _get_client(ctx: Context):
    state = ctx.request_context.lifespan_context
    return state.client


def _get_state(ctx: Context):
    return ctx.request_context.lifespan_context


async def _propagate_satellite(ctx: Context, satellite_name: str, use_scenario_time: bool = True) -> str:
    """Propagate a satellite, using COM to set UseScenarioAnalysisTime if available.

    The Connect-only Propagate command defaults to a short propagation window
    (~1.5 hours from TLE epoch) because UseScenarioAnalysisTime is False by default.
    Using COM to set it True before propagating ensures the orbit covers the full
    scenario analytical time period.
    """
    state = _get_state(ctx)
    client = state.client

    # Try COM path: set UseScenarioAnalysisTime then propagate via Connect
    if use_scenario_time and state.com_available:
        try:
            sat_obj = state.com_root.GetObjectFromPath(f"Satellite/{satellite_name}")
            if sat_obj is not None:
                propagator = sat_obj.Propagator
                propagator.UseScenarioAnalysisTime = True
                logger.info("COM: set UseScenarioAnalysisTime=True for %s", satellite_name)
        except Exception as e:
            logger.warning("COM UseScenarioAnalysisTime failed for %s: %s", satellite_name, e)

    # Propagate via Connect
    result = await client.send_command(f"Propagate */Satellite/{satellite_name}")
    if result["ack"] == "ACK":
        return f"Satellite '{satellite_name}' propagated"
    return f"Failed to propagate: {result}"


@mcp.tool()
async def stk_set_orbit_tle(
    ctx: Context,
    satellite_name: str,
    tle_line1: str,
    tle_line2: str,
) -> str:
    """Set satellite orbit using Two-Line Element (TLE) data with SGP4 propagator.

    Args:
        satellite_name: Name of the satellite object
        tle_line1: First line of TLE data
        tle_line2: Second line of TLE data
    """
    client = _get_client(ctx)

    # Set TLE state directly (STK handles propagator internally)
    cmd = (
        f'SetState */Satellite/{satellite_name} TLE '
        f'"{tle_line1}" "{tle_line2}"'
    )
    result = await client.send_command(cmd)
    if result["ack"] == "ACK":
        # Propagate with UseScenarioAnalysisTime via COM
        prop_msg = await _propagate_satellite(ctx, satellite_name)
        return f"Orbit set via TLE for '{satellite_name}'. {prop_msg}"
    return f"Failed to set TLE: {result}"


@mcp.tool()
async def stk_set_orbit_classical(
    ctx: Context,
    satellite_name: str,
    semi_major_axis: float,
    eccentricity: float,
    inclination: float,
    arg_of_perigee: float,
    raan: float,
    true_anomaly: float,
    epoch: str = "",
    coordinate_system: str = "J2000",
    force_model: str = "HPOP",
    step_size: float = 60,
) -> str:
    """Set satellite orbit using classical orbital elements (Keplerian).

    Args:
        satellite_name: Name of the satellite object
        semi_major_axis: Semi-major axis in **meters** (e.g. 6778000 for ~400km LEO)
        eccentricity: Eccentricity (0 to <1)
        inclination: Inclination in degrees
        arg_of_perigee: Argument of perigee in degrees
        raan: Right ascension of ascending node in degrees
        true_anomaly: True anomaly in degrees
        epoch: Epoch time string, e.g. "14 Jun 2026 16:00:00.000". Empty for scenario start.
        coordinate_system: Coordinate system (default: J2000)
        force_model: Force model / propagator (default: HPOP)
        step_size: Propagation step size in seconds (default: 60)
    """
    client = _get_client(ctx)

    # If no epoch given, use scenario start time
    if not epoch:
        tp_result = await client.send_command("GetTimePeriod *")
        if tp_result["ack"] == "ACK" and tp_result["data"]:
            time_parts = tp_result["raw"].split(",")
            epoch = time_parts[0].strip().strip('"')
        else:
            return "Failed to get scenario start time for epoch"

    cmd = (
        f'SetState */Satellite/{satellite_name} Classical {force_model} '
        f'UseScenarioInterval {step_size} {coordinate_system} '
        f'"{epoch}" {semi_major_axis} {eccentricity} {inclination} '
        f'{arg_of_perigee} {raan} {true_anomaly}'
    )
    result = await client.send_command(cmd)
    if result["ack"] == "ACK":
        return (
            f"Classical orbit set for '{satellite_name}': "
            f"a={semi_major_axis}m, e={eccentricity}, i={inclination}deg"
        )
    return f"Failed to set classical orbit: {result}"


@mcp.tool()
async def stk_set_orbit_cartesian(
    ctx: Context,
    satellite_name: str,
    x: float,
    y: float,
    z: float,
    vx: float,
    vy: float,
    vz: float,
    epoch: str = "",
    coordinate_system: str = "J2000",
    force_model: str = "HPOP",
    step_size: float = 60,
) -> str:
    """Set satellite orbit using Cartesian position and velocity.

    Args:
        satellite_name: Name of the satellite object
        x: X position in km
        y: Y position in km
        z: Z position in km
        vx: X velocity in km/s
        vy: Y velocity in km/s
        vz: Z velocity in km/s
        epoch: Epoch time string, e.g. "14 Jun 2026 16:00:00.000". Empty for scenario start.
        coordinate_system: Coordinate system (default: J2000)
        force_model: Force model / propagator (default: HPOP)
        step_size: Propagation step size in seconds (default: 60)
    """
    client = _get_client(ctx)

    # If no epoch given, use scenario start time
    if not epoch:
        tp_result = await client.send_command("GetTimePeriod *")
        if tp_result["ack"] == "ACK" and tp_result["data"]:
            time_parts = tp_result["raw"].split(",")
            epoch = time_parts[0].strip().strip('"')
        else:
            return "Failed to get scenario start time for epoch"

    cmd = (
        f'SetState */Satellite/{satellite_name} Cartesian {force_model} '
        f'UseScenarioInterval {step_size} {coordinate_system} '
        f'"{epoch}" {x} {y} {z} {vx} {vy} {vz}'
    )
    result = await client.send_command(cmd)
    if result["ack"] == "ACK":
        return f"Cartesian orbit set for '{satellite_name}'"
    return f"Failed to set Cartesian orbit: {result}"


@mcp.tool()
async def stk_propagate(
    ctx: Context,
    satellite_name: str,
    use_scenario_time: bool = True,
) -> str:
    """Propagate a satellite's orbit.

    By default, sets UseScenarioAnalysisTime=True via COM before propagating,
    ensuring the orbit covers the full scenario time period. Without this,
    propagation only covers ~1.5 hours from the TLE epoch.

    Args:
        satellite_name: Name of the satellite object
        use_scenario_time: If True (default), use COM to set UseScenarioAnalysisTime
            before propagating. Set to False to skip this (Connect-only mode).
    """
    return await _propagate_satellite(ctx, satellite_name, use_scenario_time=use_scenario_time)


@mcp.tool()
async def stk_set_orbit_from_file(
    ctx: Context,
    satellite_name: str,
    file_path: str,
) -> str:
    """Set satellite orbit from an external ephemeris file (.e).

    Args:
        satellite_name: Name of the satellite object
        file_path: Path to the ephemeris file
    """
    client = _get_client(ctx)

    cmd = f'SetState */Satellite/{satellite_name} FromFile "{file_path}"'
    result = await client.send_command(cmd)
    if result["ack"] == "ACK":
        return f"Orbit loaded from file for '{satellite_name}'"
    return f"Failed to load orbit from file: {result}"
