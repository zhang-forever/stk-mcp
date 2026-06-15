"""stk_orbit — Orbit definition, propagation, position queries, and lifetime estimation."""

from __future__ import annotations

import logging

from mcp.server.fastmcp import Context

from stk_mcp.app import mcp

logger = logging.getLogger("stk_mcp.tools.orbit")


def _get_client(ctx: Context):
    return ctx.request_context.lifespan_context.client


def _get_state(ctx: Context):
    return ctx.request_context.lifespan_context


async def _propagate_satellite(
    ctx: Context, satellite_name: str, use_scenario_time: bool = True
) -> str:
    """Propagate a satellite, using COM to set UseScenarioAnalysisTime if available."""
    state = _get_state(ctx)
    client = state.client
    if use_scenario_time and state.com_available:
        try:
            sat_obj = state.com_root.GetObjectFromPath(f"Satellite/{satellite_name}")
            if sat_obj is not None:
                propagator = sat_obj.Propagator
                propagator.UseScenarioAnalysisTime = True
                logger.info("COM: set UseScenarioAnalysisTime=True for %s", satellite_name)
        except Exception as e:
            logger.warning("COM UseScenarioAnalysisTime failed for %s: %s", satellite_name, e)
    result = await client.send_command(f"Propagate */Satellite/{satellite_name}")
    if result["ack"] == "ACK":
        return f"Satellite '{satellite_name}' propagated"
    return f"Failed to propagate: {result}"


@mcp.tool()
async def stk_orbit(
    ctx: Context,
    action: str,
    satellite_name: str = "",
    # TLE params
    tle_line1: str = "",
    tle_line2: str = "",
    # Classical / Cartesian params
    semi_major_axis: float = 0.0,
    eccentricity: float = 0.0,
    inclination: float = 0.0,
    arg_of_perigee: float = 0.0,
    raan: float = 0.0,
    true_anomaly: float = 0.0,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
    vx: float = 0.0,
    vy: float = 0.0,
    vz: float = 0.0,
    epoch: str = "",
    coordinate_system: str = "J2000",
    force_model: str = "HPOP",
    step_size: float = 60.0,
    # File path
    file_path: str = "",
    # Propagate params
    use_scenario_time: bool = True,
    # Position query
    time: str = "",
    # Lifetime
    satellite_id: str = "",
) -> str:
    """Define orbits, propagate, query position, and estimate orbit lifetime.

    Actions:
        set_tle        — Set orbit from TLE data (SGP4). Params: satellite_name, tle_line1, tle_line2
        set_classical  — Set orbit from Keplerian elements. Params: satellite_name, semi_major_axis(m), eccentricity, inclination(deg), arg_of_perigee(deg), raan(deg), true_anomaly(deg), epoch, coordinate_system, force_model, step_size
        set_cartesian  — Set orbit from position/velocity. Params: satellite_name, x/y/z(km), vx/vy/vz(km/s), epoch, coordinate_system, force_model, step_size
        from_file      — Load orbit from ephemeris file. Params: satellite_name, file_path
        propagate      — Propagate orbit. Params: satellite_name, use_scenario_time
        position       — Query position at a given time. Params: satellite_name, time
        lifetime       — Estimate orbit lifetime/decay. Params: satellite_name
    """
    client = _get_client(ctx)

    # ── set_tle ──────────────────────────────────────────────
    if action == "set_tle":
        if not satellite_name or not tle_line1 or not tle_line2:
            return "Parameters 'satellite_name', 'tle_line1', 'tle_line2' are required"
        cmd = f'SetState */Satellite/{satellite_name} TLE "{tle_line1}" "{tle_line2}"'
        r = await client.send_command(cmd)
        if r["ack"] == "ACK":
            msg = await _propagate_satellite(ctx, satellite_name)
            return f"Orbit set via TLE for '{satellite_name}'. {msg}"
        return f"Failed to set TLE: {r}"

    # ── set_classical ────────────────────────────────────────
    elif action == "set_classical":
        if not satellite_name:
            return "Parameter 'satellite_name' is required"
        if not epoch:
            tp = await client.send_command("GetTimePeriod *")
            if tp["ack"] == "ACK" and tp["data"]:
                epoch = tp["raw"].split(",")[0].strip().strip('"')
            else:
                return "Failed to get scenario start time for epoch"
        cmd = (
            f"SetState */Satellite/{satellite_name} Classical {force_model} "
            f"UseScenarioInterval {step_size} {coordinate_system} "
            f'"{epoch}" {semi_major_axis} {eccentricity} {inclination} '
            f"{arg_of_perigee} {raan} {true_anomaly}"
        )
        r = await client.send_command(cmd)
        if r["ack"] == "ACK":
            return (
                f"Classical orbit set for '{satellite_name}': "
                f"a={semi_major_axis}m, e={eccentricity}, i={inclination}deg"
            )
        return f"Failed to set classical orbit: {r}"

    # ── set_cartesian ────────────────────────────────────────
    elif action == "set_cartesian":
        if not satellite_name:
            return "Parameter 'satellite_name' is required"
        if not epoch:
            tp = await client.send_command("GetTimePeriod *")
            if tp["ack"] == "ACK" and tp["data"]:
                epoch = tp["raw"].split(",")[0].strip().strip('"')
            else:
                return "Failed to get scenario start time for epoch"
        cmd = (
            f"SetState */Satellite/{satellite_name} Cartesian {force_model} "
            f"UseScenarioInterval {step_size} {coordinate_system} "
            f'"{epoch}" {x} {y} {z} {vx} {vy} {vz}'
        )
        r = await client.send_command(cmd)
        if r["ack"] == "ACK":
            return f"Cartesian orbit set for '{satellite_name}'"
        return f"Failed to set Cartesian orbit: {r}"

    # ── from_file ────────────────────────────────────────────
    elif action == "from_file":
        if not satellite_name or not file_path:
            return "Parameters 'satellite_name' and 'file_path' are required"
        r = await client.send_command(
            f'SetState */Satellite/{satellite_name} FromFile "{file_path}"'
        )
        if r["ack"] == "ACK":
            return f"Orbit loaded from file for '{satellite_name}'"
        return f"Failed to load orbit from file: {r}"

    # ── propagate ────────────────────────────────────────────
    elif action == "propagate":
        if not satellite_name:
            return "Parameter 'satellite_name' is required"
        return await _propagate_satellite(ctx, satellite_name, use_scenario_time)

    # ── position ─────────────────────────────────────────────
    elif action == "position":
        if not satellite_name:
            return "Parameter 'satellite_name' is required"
        cmd = f"Position_RM */Satellite/{satellite_name}"
        if time:
            cmd += f' Time "{time}"'
        r = await client.send_command(cmd)
        if r["ack"] == "ACK" and r["data"]:
            return f"Position of '{satellite_name}':\n" + r["raw"]
        elif r["ack"] == "ACK":
            return f"No position data for '{satellite_name}'"
        return f"Failed to get position: {r}"

    # ── lifetime ─────────────────────────────────────────────
    elif action == "lifetime":
        if not satellite_name:
            return "Parameter 'satellite_name' is required"
        cmd = f"Lifetime */Satellite/{satellite_name}"
        r = await client.send_command(cmd)
        if r["ack"] == "ACK" and r["data"]:
            return f"Orbit lifetime for '{satellite_name}':\n" + r["raw"]
        elif r["ack"] == "ACK":
            return f"No lifetime data for '{satellite_name}'"
        return f"Failed to compute lifetime: {r}"

    else:
        return (
            f"Unknown action '{action}'. Valid actions: "
            "set_tle, set_classical, set_cartesian, from_file, propagate, position, lifetime"
        )
