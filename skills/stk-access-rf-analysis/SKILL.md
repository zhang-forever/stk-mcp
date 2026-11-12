---
name: stk-access-rf-analysis
description: Compute access windows, AER data, lighting/visibility, chain access, communication-link queries, sensor field of view, and radar data in a live STK scenario through the stk MCP server. Use when the user asks for ground-station contacts, pass geometry, chain connectivity, link budgets, sensor footprints, or RCS/radar queries.
---

# STK Access & RF Analysis

Use `stk_analysis` for geometry and RF queries. Every object involved must have
propagated ephemeris, and the analysis window must overlap that ephemeris.

## Access and AER

| Action | Purpose | Parameters |
|---|---|---|
| `access` | Access intervals between two objects | `from_object`, `to_object`, optional `time_period`, `max_step_size` |
| `all_access` | Access from one object to every other object | `from_object` |
| `aer` | Azimuth/elevation/range records | `from_object`, `to_object`, optional `time_period`, `max_step_size` |
| `visibility` | Lighting/visibility conditions | `from_object`, `to_object` |

```
stk_analysis access from_object=Satellite/ISS to_object=Facility/Beijing
stk_analysis aer from_object=Facility/Beijing to_object=Satellite/ISS max_step_size=60
```

- Object paths are relative (`Satellite/ISS`, `Facility/Beijing`), without `*/`.
- `access` defaults to `TimePeriod UseScenarioInterval`; pass
  `time_period="1 Jul 2026 00:00:00 2 Jul 2026 00:00:00"` to narrow it.
- `max_step_size` is in seconds and controls sampling density.
- For AER geometry, put the **facility first** so azimuth/elevation are
  observer-relative.

## Chains

```
stk_analysis chain_access chain_name=MyChain
stk_analysis chain_intervals chain_name=MyChain
```

A chain must contain at least two members before access can be computed. The
object-management skill shows how to add members with a raw `Chains ... Add`
command.

## RF, sensor, and radar

| Action | Purpose | Parameters |
|---|---|---|
| `comm_link` | Query a communication system | `comm_system`, optional `query_type` |
| `sensor_fov` | Sensor field-of-view data | `sensor_path` (e.g. `Satellite/ISS/Sensor/Cam`) |
| `radar` | Radar attributes/analysis | `object_path` |

```
stk_analysis comm_link comm_system=MyCommSystem
stk_analysis sensor_fov sensor_path=Satellite/ISS/Sensor/Cam
stk_analysis radar object_path=Satellite/ISS
```

With no `comm_system`, `comm_link` falls back to a general `CommQuery`. RF
results only exist if the scenario contains the corresponding transmitter,
receiver, or radar objects; the MCP action queries them, it does not create them.

## Interpreting results

- Access output is a list of intervals with start, stop, and duration.
- `No access intervals` is a valid result, not an error.
- AER output includes date/time, azimuth, elevation, and range per sample.
- Lighting results describe sun/eclipse state, not sensor detections.

## Verification

1. `stk_analysis access` with a known geometry (e.g. ISS over a mid-latitude site).
2. If empty, `stk_orbit report` or `stk_util report style="LLA Position"` to
   confirm the satellite has ephemeris.
3. `stk_scenario status` to confirm the scenario window.

## Pitfalls

- Analysis before propagation returns no data or `NAK`.
- A time window outside the ephemeris span silently yields empty results.
- `chain_access` requires chain members; an empty chain returns nothing.
- Sensor FOV requires a sensor attached to the correct parent path.
- Radar and comm queries require the relevant RF objects to exist.

## Related

- Build objects and chains: [[stk-object-management]]
- Orbit definition: [[stk-orbit-setup]]
- Coverage figures of merit: [[stk-coverage-visibility]]
- Report formatting: [[stk-report]]
