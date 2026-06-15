"""Object management tools: add satellites, facilities, targets, sensors."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from stk_mcp.app import mcp


def _get_client(ctx: Context):
    state = ctx.request_context.lifespan_context
    return state.client


@mcp.tool()
async def stk_add_satellite(ctx: Context, name: str) -> str:
    """Add a new satellite to the current scenario.

    Args:
        name: Satellite name (no spaces)
    """
    client = _get_client(ctx)
    result = await client.send_command(f"New / */Satellite {name}")
    if result["ack"] == "ACK":
        return f"Satellite '{name}' added"
    return f"Failed to add satellite: {result}"


@mcp.tool()
async def stk_add_facility(
    ctx: Context,
    name: str,
    latitude: float = 0.0,
    longitude: float = 0.0,
    altitude: float = 0.0,
) -> str:
    """Add a ground facility/station to the scenario.

    Args:
        name: Facility name
        latitude: Latitude in degrees (-90 to 90)
        longitude: Longitude in degrees (-180 to 180)
        altitude: Altitude in meters above WGS84 ellipsoid
    """
    client = _get_client(ctx)

    # Create facility
    result = await client.send_command(f"New / */Facility {name}")
    if result["ack"] != "ACK":
        return f"Failed to add facility: {result}"

    # Set position
    pos_result = await client.send_command(
        f"SetPosition */Facility/{name} Geodetic {latitude} {longitude} {altitude}"
    )
    if pos_result["ack"] != "ACK":
        return f"Facility created but position failed: {pos_result}"

    return f"Facility '{name}' added at ({latitude}, {longitude}, {altitude}m)"


@mcp.tool()
async def stk_add_target(
    ctx: Context,
    name: str,
    latitude: float = 0.0,
    longitude: float = 0.0,
    altitude: float = 0.0,
) -> str:
    """Add a ground target to the scenario.

    Args:
        name: Target name
        latitude: Latitude in degrees (-90 to 90)
        longitude: Longitude in degrees (-180 to 180)
        altitude: Altitude in meters above WGS84 ellipsoid
    """
    client = _get_client(ctx)

    result = await client.send_command(f"New / */Target {name}")
    if result["ack"] != "ACK":
        return f"Failed to add target: {result}"

    pos_result = await client.send_command(
        f"SetPosition */Target/{name} Geodetic {latitude} {longitude} {altitude}"
    )
    if pos_result["ack"] != "ACK":
        return f"Target created but position failed: {pos_result}"

    return f"Target '{name}' added at ({latitude}, {longitude}, {altitude}m)"


@mcp.tool()
async def stk_add_sensor(
    ctx: Context,
    parent_path: str,
    name: str,
    cone_angle: float = 5.0,
) -> str:
    """Add a sensor to a parent object (satellite, facility, etc.).

    Args:
        parent_path: Parent object path, e.g. "Satellite/Sat1" or "Facility/Fac1"
        name: Sensor name
        cone_angle: Half-angle cone in degrees
    """
    client = _get_client(ctx)

    result = await client.send_command(
        f"New / */{parent_path}/Sensor {name}"
    )
    if result["ack"] != "ACK":
        return f"Failed to add sensor: {result}"

    # Define sensor as simple cone
    def_result = await client.send_command(
        f"Define */{parent_path}/Sensor/{name} SimpleCone {cone_angle}"
    )
    if def_result["ack"] != "ACK":
        return f"Sensor created but definition failed: {def_result}"

    return f"Sensor '{name}' added to {parent_path} (cone={cone_angle}deg)"


@mcp.tool()
async def stk_list_objects(ctx: Context, object_type: str = "") -> str:
    """List all objects in the current scenario.

    Args:
        object_type: Filter by type, e.g. "Satellite", "Facility", "Target". Empty for all.
    """
    client = _get_client(ctx)

    if object_type:
        cmd = f'AllInstanceNames / */{object_type}'
    else:
        cmd = "AllInstanceNames / *"

    result = await client.send_command(cmd)
    if result["ack"] == "ACK" and result["data"]:
        return "\n".join(result["data"])
    elif result["ack"] == "ACK":
        return "No objects found"
    return f"Failed to list objects: {result}"


@mcp.tool()
async def stk_unload_object(ctx: Context, object_path: str) -> str:
    """Remove an object from the scenario.

    Args:
        object_path: Object path, e.g. "Satellite/Sat1" or "Facility/Fac1"
    """
    client = _get_client(ctx)
    result = await client.send_command(f"Unload / */{object_path}")
    if result["ack"] == "ACK":
        return f"Object '{object_path}' removed"
    return f"Failed to remove object: {result}"
