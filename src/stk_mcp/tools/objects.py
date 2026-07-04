"""stk_objects — Object creation and management (satellites, facilities, sensors, chains, etc.)."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from stk_mcp.app import mcp


def _get_client(ctx: Context):
    return ctx.request_context.lifespan_context.client


@mcp.tool()
async def stk_objects(
    ctx: Context,
    action: str,
    name: str = "",
    object_path: str = "",
    parent_path: str = "",
    object_type: str = "",
    latitude: float = 0.0,
    longitude: float = 0.0,
    altitude: float = 0.0,
    cone_angle: float = 5.0,
    # constellation / chain params
    satellite_names: str = "",
    info_type: str = "properties",
    # walker params
    walker_type: str = "Delta",
    num_planes: int = 0,
    num_sats_per_plane: int = 0,
    inter_plane_phase_increment: int = 1,
    color_by_plane: bool = True,
    constellation_name: str = "",
    # coverage params
    coverage_name: str = "",
    grid_bounds: str = "Global",
    grid_resolution: float = 6.0,
    fom_type: str = "Revisit",
) -> str:
    """Create and manage STK objects.

    Actions:
        add_satellite    — Add a satellite. Param: name
        add_facility     — Add ground station. Params: name, latitude, longitude, altitude
        add_target       — Add ground target. Params: name, latitude, longitude, altitude
        add_sensor       — Attach sensor to object. Params: parent_path, name, cone_angle
        add_constellation — Create constellation from satellite list. Params: name, satellite_names (comma-separated)
        add_chain        — Create communication chain. Params: name
        add_aircraft     — Add aircraft object. Params: name
        walker           — Build a Walker constellation from a seed satellite. The seed MUST already
                           have propagated ephemeris. Params: name (seed sat name), walker_type
                           (Delta/Star/Custom), num_planes, num_sats_per_plane,
                           inter_plane_phase_increment, color_by_plane, constellation_name (optional).
                           Generates satellites named <seed><plane><index>.
        add_coverage     — Create a CoverageDefinition with grid, assets, and a figure of merit.
                           Params: coverage_name, grid_bounds ("Global" or "LatBounds <min> <max>"),
                           grid_resolution (deg), satellite_names (comma-separated assets to Assign;
                           empty = assign all satellites), fom_type (Revisit/NAsset).
        compute_coverage — Compute accesses for a CoverageDefinition and report the FOM. Params: coverage_name
        list             — List all objects. Param: object_type (optional filter: Satellite, Facility, Target, etc.)
        remove           — Remove object. Param: object_path (e.g. "Satellite/Sat1")
        get_info         — Query object info. Params: object_path, info_type (properties/description/subobjects/all)
    """
    client = _get_client(ctx)

    # ── add_satellite ────────────────────────────────────────
    if action == "add_satellite":
        if not name:
            return "Parameter 'name' is required"
        r = await client.send_command(f"New / */Satellite {name}")
        if r["ack"] == "ACK":
            return f"Satellite '{name}' added"
        return f"Failed to add satellite: {r}"

    # ── add_facility ─────────────────────────────────────────
    elif action == "add_facility":
        if not name:
            return "Parameter 'name' is required"
        r = await client.send_command(f"New / */Facility {name}")
        if r["ack"] != "ACK":
            return f"Failed to add facility: {r}"
        await client.send_command(
            f"SetPosition */Facility/{name} Geodetic {latitude} {longitude} {altitude}"
        )
        return f"Facility '{name}' added at ({latitude}, {longitude}, {altitude}m)"

    # ── add_target ───────────────────────────────────────────
    elif action == "add_target":
        if not name:
            return "Parameter 'name' is required"
        r = await client.send_command(f"New / */Target {name}")
        if r["ack"] != "ACK":
            return f"Failed to add target: {r}"
        await client.send_command(
            f"SetPosition */Target/{name} Geodetic {latitude} {longitude} {altitude}"
        )
        return f"Target '{name}' added at ({latitude}, {longitude}, {altitude}m)"

    # ── add_sensor ───────────────────────────────────────────
    elif action == "add_sensor":
        if not parent_path or not name:
            return "Parameters 'parent_path' and 'name' are required"
        r = await client.send_command(f"New / */{parent_path}/Sensor {name}")
        if r["ack"] != "ACK":
            return f"Failed to add sensor: {r}"
        await client.send_command(
            f"Define */{parent_path}/Sensor/{name} SimpleCone {cone_angle}"
        )
        return f"Sensor '{name}' added to {parent_path} (cone={cone_angle}deg)"

    # ── add_constellation ────────────────────────────────────
    elif action == "add_constellation":
        if not name:
            return "Parameter 'name' is required"
        # Create constellation object
        r = await client.send_command(f"New / */Constellation {name}")
        if r["ack"] != "ACK":
            return f"Failed to create constellation: {r}"
        # Add satellites if provided
        if satellite_names:
            added = []
            for sat_name in satellite_names.split(","):
                sat_name = sat_name.strip()
                if sat_name:
                    ar = await client.send_command(
                        f"Constellation */Constellation/{name} Add Satellite/{sat_name}"
                    )
                    if ar["ack"] == "ACK":
                        added.append(sat_name)
            return f"Constellation '{name}' created with {len(added)} satellites: {', '.join(added)}"
        return f"Constellation '{name}' created (empty — use Constellation Add to populate)"

    # ── add_chain ────────────────────────────────────────────
    elif action == "add_chain":
        if not name:
            return "Parameter 'name' is required"
        r = await client.send_command(f"New / */Chain {name}")
        if r["ack"] == "ACK":
            return f"Chain '{name}' created"
        return f"Failed to create chain: {r}"

    # ── add_aircraft ─────────────────────────────────────────
    elif action == "add_aircraft":
        if not name:
            return "Parameter 'name' is required"
        r = await client.send_command(f"New / */Aircraft {name}")
        if r["ack"] == "ACK":
            return f"Aircraft '{name}' added"
        return f"Failed to add aircraft: {r}"

    # ── walker ───────────────────────────────────────────────
    elif action == "walker":
        if not name:
            return "Parameter 'name' (seed satellite) is required"
        if num_planes <= 0 or num_sats_per_plane <= 0:
            return "Parameters 'num_planes' and 'num_sats_per_plane' must be > 0"
        cmd = (
            f"Walker */Satellite/{name} Type {walker_type} "
            f"NumPlanes {num_planes} NumSatsPerPlane {num_sats_per_plane}"
        )
        # Delta/Star require the phase increment; Custom uses different params.
        if walker_type in ("Delta", "Star"):
            cmd += f" InterPlanePhaseIncrement {inter_plane_phase_increment}"
        cmd += f" ColorByPlane {'Yes' if color_by_plane else 'No'}"
        if constellation_name:
            cmd += f" ConstellationName {constellation_name}"
        r = await client.send_command(cmd)
        if r["ack"] != "ACK":
            return (
                f"Failed to build Walker constellation: {r}. "
                "Ensure the seed satellite has propagated ephemeris."
            )
        total = num_planes * num_sats_per_plane
        return (
            f"Walker {walker_type} constellation built from seed '{name}': "
            f"{num_planes} planes x {num_sats_per_plane} sats = {total} satellites"
            + (f" (constellation '{constellation_name}')" if constellation_name else "")
        )

    # ── add_coverage ─────────────────────────────────────────
    elif action == "add_coverage":
        if not coverage_name:
            return "Parameter 'coverage_name' is required"
        cd = f"*/CoverageDefinition/{coverage_name}"
        # 1. Create the coverage definition (class path + instance name, per New syntax)
        r = await client.send_command(
            f"New / */CoverageDefinition {coverage_name}"
        )
        if r["ack"] != "ACK":
            return f"Failed to create coverage definition: {r}"
        # 2. Define the grid (bounds + resolution)
        bounds_cmd = (
            "AreaOfInterest Global"
            if grid_bounds.strip().lower() == "global"
            else f"AreaOfInterest {grid_bounds.strip()}"
        )
        await client.send_command(f"Cov {cd} Grid {bounds_cmd}")
        await client.send_command(
            f"Cov {cd} Grid PointGranularity LatLon {grid_resolution}"
        )
        # 3. Assign assets (Assign keyword, */ prefix)
        assets = [s.strip() for s in satellite_names.split(",") if s.strip()]
        if not assets:
            # No explicit list: assign every satellite in the scenario.
            lr = await client.send_command("AllInstanceNames / */Satellite")
            if lr["ack"] == "ACK" and lr["data"]:
                assets = [
                    n.strip() for line in lr["data"] for n in line.split() if n.strip()
                ]
        assigned = 0
        for sat in assets:
            ar = await client.send_command(
                f"Cov {cd} Asset */Satellite/{sat} Assign"
            )
            if ar["ack"] == "ACK":
                assigned += 1
        # 4. Define the figure of merit
        fom_name = fom_type
        await client.send_command(f"New / {cd}/FigureOfMerit {fom_name}")
        fom_path = f"{cd}/FigureOfMerit/{fom_name}"
        if fom_type.lower().startswith("nasset") or fom_type.lower() == "n-asset":
            fom_def = "Definition NAsset Compute Minimum"
        else:
            fom_def = "Definition RevisitTime Compute Maximum EndGaps Include"
        fr = await client.send_command(f"Cov {fom_path} FOMDefine {fom_def}")
        return (
            f"CoverageDefinition '{coverage_name}' created: "
            f"grid={grid_bounds} @ {grid_resolution}deg, "
            f"{assigned} assets assigned, FOM '{fom_name}' "
            + ("defined" if fr["ack"] == "ACK" else f"FOM failed: {fr}")
        )

    # ── compute_coverage ─────────────────────────────────────
    elif action == "compute_coverage":
        if not coverage_name:
            return "Parameter 'coverage_name' is required"
        cd = f"*/CoverageDefinition/{coverage_name}"
        cr = await client.send_command(f"Cov {cd} Access Compute")
        if cr["ack"] != "ACK":
            return f"Failed to compute coverage: {cr}"
        return f"Coverage '{coverage_name}' computed. Use stk_analysis coverage to read the FOM."

    # ── list ─────────────────────────────────────────────────
    elif action == "list":
        if object_type:
            cmd = f"AllInstanceNames / */{object_type}"
        else:
            cmd = "AllInstanceNames / *"
        r = await client.send_command(cmd)
        if r["ack"] == "ACK" and r["data"]:
            return "\n".join(r["data"])
        elif r["ack"] == "ACK":
            return "No objects found"
        return f"Failed to list objects: {r}"

    # ── remove ───────────────────────────────────────────────
    elif action == "remove":
        if not object_path:
            return "Parameter 'object_path' is required"
        r = await client.send_command(f"Unload / */{object_path}")
        if r["ack"] == "ACK":
            return f"Object '{object_path}' removed"
        return f"Failed to remove object: {r}"

    # ── get_info ─────────────────────────────────────────────
    elif action == "get_info":
        if not object_path:
            return "Parameter 'object_path' is required"
        results = []

        if info_type in ("properties", "all"):
            r = await client.send_command(f"GetProperties */{object_path}")
            if r["ack"] == "ACK" and r["data"]:
                results.append("=== Properties ===")
                results.append(r["raw"])

        if info_type in ("description", "all"):
            r = await client.send_command(f"GetDescription */{object_path}")
            if r["ack"] == "ACK" and r["data"]:
                results.append("=== Description ===")
                results.append(r["raw"])

        if info_type in ("subobjects", "all"):
            r = await client.send_command(f"ListSubObjects */{object_path}")
            if r["ack"] == "ACK" and r["data"]:
                results.append("=== Sub-Objects ===")
                results.append(r["raw"])

        if not results:
            return f"No info available for '{object_path}' (info_type={info_type})"
        return "\n".join(results)

    else:
        return (
            f"Unknown action '{action}'. Valid actions: "
            "add_satellite, add_facility, add_target, add_sensor, "
            "add_constellation, add_chain, add_aircraft, walker, add_coverage, "
            "compute_coverage, list, remove, get_info"
        )
