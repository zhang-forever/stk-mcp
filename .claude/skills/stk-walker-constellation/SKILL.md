---
name: stk-walker-constellation
description: Build a Walker (Delta/Star) satellite constellation in a live STK scenario via the stk MCP server. Use when the user wants to create a constellation, deploy multiple orbital planes, or simulate a Walker pattern (e.g. Walker Delta 24/3/1).
---

# STK Walker Constellation

Build a Walker constellation in the connected STK instance using the `stk` MCP tools.

## Prerequisites

- The `stk` MCP server is connected (`stk_scenario` action `status` returns "Connected").
- A scenario is loaded. If not, create one first with `stk_scenario` action `new`.
- **Critical**: the Walker command replicates a *seed satellite that already has propagated ephemeris*. You MUST create and propagate the seed before calling walker, or STK rejects it.

## Workflow

1. **Ensure a scenario exists** — `stk_scenario` action `new` (params: name, start_time, stop_time) or `status` to confirm one is loaded.

2. **Create + propagate the seed satellite**:
   - `stk_objects` action `add_satellite` (param: name, e.g. `Seed`).
   - `stk_orbit` action `set_classical` to set the orbit (semi-major axis, eccentricity, inclination, etc.).
   - `stk_orbit` action `propagate` — the seed must have ephemeris before the Walker step.

3. **Build the Walker constellation** — `stk_objects` action `walker`:
   | Param | Meaning |
   |---|---|
   | `name` | seed satellite name (must be propagated) |
   | `walker_type` | `Delta` (default), `Star`, or `Custom` |
   | `num_planes` | number of orbital planes |
   | `num_sats_per_plane` | satellites per plane |
   | `inter_plane_phase_increment` | Walker phasing factor (Delta/Star only) |
   | `color_by_plane` | `true` to color-code planes |
   | `constellation_name` | optional; groups all generated sats into a Constellation object |

## Naming rule (verified on live STK v11.6.0)

The Walker command generates satellites named `<seed><plane><index>`, both 1-based.
Example: seed `Seed`, 3 planes x 8 sats → `Seed11`..`Seed18`, `Seed21`..`Seed28`, `Seed31`..`Seed38`.
The original seed satellite remains and becomes `<seed>11`'s plane-1 anchor.

## Example: Walker Delta 24/3/1

```
stk_scenario  new           name=WalkerDemo start_time="1 Jul 2026 00:00:00" stop_time="2 Jul 2026 00:00:00"
stk_objects   add_satellite name=Seed
stk_orbit     set_classical name=Seed  (a≈26558 km / MEO, ecc=0, inc=55, ...)
stk_orbit     propagate     name=Seed
stk_objects   walker        name=Seed walker_type=Delta num_planes=3 num_sats_per_plane=8 inter_plane_phase_increment=1 color_by_plane=true
```

Result: 24 satellites `Seed11`–`Seed38` across 3 planes.

## Verified raw Connect command

```
Walker */Satellite/Seed Type Delta NumPlanes 3 NumSatsPerPlane 8 InterPlanePhaseIncrement 1 ColorByPlane Yes
```

## Common failures

- **NAK on walker** → seed has no ephemeris. Run `stk_orbit propagate` first.
- **Wrong sat count** → `num_planes * num_sats_per_plane` must equal the intended total.
- For `Custom` type, phase increment is ignored; use RAAN / true-anomaly increments instead (raw command via `stk_util`).

## Related

- Follow-on coverage analysis: [[stk-coverage-visibility]]
- Scenario setup: [[stk-scenario-scaffold]]
