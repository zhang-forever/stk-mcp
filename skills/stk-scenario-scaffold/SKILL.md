---
name: stk-scenario-scaffold
description: Standard opening moves for any STK task via the stk MCP server — connect, create or confirm a scenario, set the analysis time window, and add objects. Use at the start of any STK simulation to establish a clean baseline before constellation, coverage, or conjunction work.
---

# STK Scenario Scaffold

The standard startup sequence for any STK task using the `stk` MCP tools. Run this before more specific workflows.

## 1. Confirm the connection

`stk_scenario` action `status` — returns connection state, STK version, and whether a scenario is loaded.

- If "Not connected", run `stk_scenario` action `connect` (params: host, port; defaults localhost:5001).
- The `stk` MCP server auto-connects on startup, so `status` is usually enough.

## 2. Create or confirm a scenario

- **New scenario**: `stk_scenario` action `new` (params: name, start_time, stop_time).
  - Times use STK format: `"1 Jul 2026 00:00:00"`.
  - This also resets the animation clock.
- **Existing file**: `stk_scenario` action `load` (param: file_path to a `.sc`).
- If `status` shows "Scenario: loaded" and you want a clean slate, `unload` first.

## 3. Set the analysis time window

If not set at creation, `stk_scenario` action `set_time_period` (params: start_time, stop_time).
This window bounds all propagation and analysis — set it before adding time-dependent objects.

## 4. Add objects

- Satellite: `stk_objects` action `add_satellite` (param: name), then define orbit via `stk_orbit`.
- Ground station: `stk_objects` action `add_facility` (params: name, latitude, longitude, altitude).
- Target: `stk_objects` action `add_target`.
- Sensor: `stk_objects` action `add_sensor` (params: parent_path, name, cone_angle).

## 5. Verify

`stk_objects` action `list` (optional param: object_type filter) to confirm what's in the scenario.

## Canonical opening

```
stk_scenario status
stk_scenario new  name=MyScenario start_time="1 Jul 2026 00:00:00" stop_time="2 Jul 2026 00:00:00"
stk_objects  add_satellite name=Sat1
stk_orbit    set_classical name=Sat1 ...
stk_orbit    propagate     name=Sat1
stk_objects  list
```

## Time format reference

STK expects `"D Mon YYYY HH:MM:SS"` (e.g. `"1 Jul 2026 00:00:00"`), quoted because of the spaces.

## Gotchas

- **Modal dialogs block Connect**: destructive commands (new/save/unload) can pop a confirmation dialog in the STK GUI that freezes all Connect responses until dismissed. If commands start timing out, check the STK window for a dialog.
- Always set the time period before propagating; propagation is clipped to the scenario window.

## Related

- Constellation build: [[stk-walker-constellation]]
- Coverage & visibility: [[stk-coverage-visibility]]
- Conjunction assessment: [[stk-conjunction]]
