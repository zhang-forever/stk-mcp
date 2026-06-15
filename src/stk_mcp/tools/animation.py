"""Animation control tools."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from stk_mcp.app import mcp


def _get_client(ctx: Context):
    state = ctx.request_context.lifespan_context
    return state.client


@mcp.tool()
async def stk_animate(
    ctx: Context,
    action: str = "Start",
) -> str:
    """Control STK animation.

    Args:
        action: Animation action:
            - "Start": Start animation forward
            - "Pause": Pause at current time
            - "Reset": Stop and reset to start
            - "Faster": Increase animation speed
            - "Slower": Decrease animation speed
            - "StepForward": Step one time step forward
            - "StepReverse": Step one time step backward
            - "Refresh": Refresh at current time
    """
    client = _get_client(ctx)

    action_map = {
        "Start": "Start End",
        "Pause": "Pause",
        "Reset": "Reset",
        "Faster": "Faster",
        "Slower": "Slower",
        "StepForward": "Step Forward",
        "StepReverse": "Step Reverse",
        "Refresh": "Refresh",
        "Loop": "Start Loop",
        "RealTime": "Start RealTime",
    }

    stk_action = action_map.get(action, action)
    result = await client.send_command(f"Animate * {stk_action}")
    if result["ack"] == "ACK":
        return f"Animation: {action}"
    return f"Animation failed: {result}"


@mcp.tool()
async def stk_get_animation_time(ctx: Context) -> str:
    """Get the current animation time."""
    client = _get_client(ctx)
    result = await client.send_command("GetAnimTime *")
    if result["ack"] == "ACK" and result["data"]:
        return f"Animation time: {result['raw']}"
    return f"Failed to get animation time: {result}"
