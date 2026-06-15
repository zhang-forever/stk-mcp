"""stk_scenario — Scenario lifecycle management (connect, create, load, save, animate)."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from stk_mcp.app import mcp


def _get_state(ctx: Context):
    return ctx.request_context.lifespan_context


@mcp.tool()
async def stk_scenario(
    ctx: Context,
    action: str,
    name: str = "",
    file_path: str = "",
    start_time: str = "",
    stop_time: str = "",
    host: str = "localhost",
    port: int = 5001,
    animate_action: str = "Start",
) -> str:
    """Manage STK scenario lifecycle.

    Actions:
        connect          — Connect to STK Connect port. Params: host, port
        disconnect       — Disconnect from STK
        status           — Show connection status, STK version, current scenario
        new              — Create new scenario. Params: name, start_time, stop_time
        load             — Load a .sc scenario file. Params: file_path
        save             — Save current scenario. Params: file_path (optional)
        unload           — Close current scenario
        set_time_period  — Set analytical time window. Params: start_time, stop_time
        animate          — Control animation. Param: animate_action (Start/Pause/Reset/Faster/Slower/StepForward/StepReverse/Loop/RealTime/Refresh)
    """
    state = _get_state(ctx)
    client = state.client

    # ── connect ──────────────────────────────────────────────
    if action == "connect":
        if client.connected:
            return f"Already connected to STK at {state.host}:{state.port}"
        client.host = host
        client.port = port
        await client.connect()
        state.host = host
        state.port = port
        return f"Connected to STK at {host}:{port}"

    # ── disconnect ───────────────────────────────────────────
    elif action == "disconnect":
        if not client.connected:
            return "Not connected"
        await client.disconnect()
        return "Disconnected from STK"

    # ── status ───────────────────────────────────────────────
    elif action == "status":
        if not client.connected:
            return "Not connected to STK"
        lines = ["Connected to STK"]
        try:
            r = await client.send_command("GetSTKVersion")
            if r["ack"] == "ACK" and r["data"]:
                lines.append(f"Version: {r['raw']}")
        except Exception as e:
            lines.append(f"Version check failed: {e}")
        try:
            r = await client.send_command("CheckScenario")
            if r["ack"] == "ACK" and r["data"]:
                lines.append(f"Scenario: {r['raw']}")
            else:
                lines.append("Scenario: None loaded")
        except Exception as e:
            lines.append(f"Scenario check failed: {e}")
        return "\n".join(lines)

    # ── new ──────────────────────────────────────────────────
    elif action == "new":
        if not name:
            return "Parameter 'name' is required for action 'new'"
        r = await client.send_command(f"New / Scenario {name}")
        if r["ack"] != "ACK":
            return f"Failed to create scenario: {r}"
        if start_time and stop_time:
            tp = await client.send_command(
                f'SetTimePeriod * "{start_time}" "{stop_time}"'
            )
            if tp["ack"] != "ACK":
                return f"Scenario created but time period failed: {tp}"
        await client.send_command("Animate * Reset")
        return f"Scenario '{name}' created" + (
            f" [{start_time} to {stop_time}]" if start_time and stop_time else ""
        )

    # ── load ─────────────────────────────────────────────────
    elif action == "load":
        if not file_path:
            return "Parameter 'file_path' is required for action 'load'"
        r = await client.send_command(f'Load / Scenario "{file_path}"')
        if r["ack"] == "ACK":
            return f"Scenario loaded from: {file_path}"
        return f"Failed to load scenario: {r}"

    # ── save ─────────────────────────────────────────────────
    elif action == "save":
        cmd = "Save / *"
        if file_path:
            cmd += f' "{file_path}"'
        r = await client.send_command(cmd)
        if r["ack"] == "ACK":
            return f"Scenario saved" + (f" to {file_path}" if file_path else "")
        return f"Failed to save scenario: {r}"

    # ── unload ───────────────────────────────────────────────
    elif action == "unload":
        r = await client.send_command("Unload / *")
        if r["ack"] == "ACK":
            return "Scenario unloaded"
        return f"Failed to unload scenario: {r}"

    # ── set_time_period ──────────────────────────────────────
    elif action == "set_time_period":
        if not start_time or not stop_time:
            return "Parameters 'start_time' and 'stop_time' are required"
        r = await client.send_command(
            f'SetTimePeriod * "{start_time}" "{stop_time}"'
        )
        if r["ack"] == "ACK":
            return f"Time period set: {start_time} to {stop_time}"
        return f"Failed to set time period: {r}"

    # ── animate ──────────────────────────────────────────────
    elif action == "animate":
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
        stk_act = action_map.get(animate_action, animate_action)
        r = await client.send_command(f"Animate * {stk_act}")
        if r["ack"] == "ACK":
            # If just querying time or refreshing, also return current time
            if animate_action in ("Refresh",):
                t = await client.send_command("GetAnimTime *")
                if t["ack"] == "ACK" and t["data"]:
                    return f"Animation: {animate_action}, time: {t['raw']}"
            return f"Animation: {animate_action}"
        return f"Animation failed: {r}"

    else:
        return (
            f"Unknown action '{action}'. Valid actions: "
            "connect, disconnect, status, new, load, save, unload, "
            "set_time_period, animate"
        )
