---
name: stk-orbit-setup
description: Define, propagate, and query satellite orbits in a live STK scenario through the stk MCP server. Covers TLE/SGP4, Keplerian elements, Cartesian state vectors, ephemeris files, propagation windows, position queries, and lifetime estimates. Use when the user needs to create or replace an orbit, fix a short propagation window, query position at a specific time, or estimate orbital decay.
---

# STK Orbit Setup

Set the orbit of an existing satellite and make sure it is propagated before any
analysis. All calls go through `stk_orbit`; the satellite itself must already
exist (`stk_objects` action `add_satellite`).

## Choose the orbit source

| Source | Action | Key parameters |
|---|---|---|
| TLE (SGP4) | `set_tle` | `satellite_name`, `tle_line1`, `tle_line2` |
| Keplerian elements | `set_classical` | `semi_major_axis` (**m**), `eccentricity`, `inclination` (deg), `arg_of_perigee`, `raan`, `true_anomaly`, optional `epoch`, `coordinate_system`, `force_model`, `step_size` |
| Position/velocity | `set_cartesian` | `x`/`y`/`z` (**km**), `vx`/`vy`/`vz` (**km/s**), optional `epoch`, `coordinate_system`, `force_model`, `step_size` |
| Ephemeris file | `from_file` | `satellite_name`, `file_path` |

`set_tle` propagates automatically. For the other sources, call `propagate`
after the state is accepted.

```
stk_objects  add_satellite name=LeoSat
stk_orbit    set_tle satellite_name=LeoSat tle_line1="1 ..." tle_line2="2 ..."
stk_orbit    propagate satellite_name=LeoSat
```

## Classical and Cartesian calls

```
stk_orbit set_classical satellite_name=LeoSat \
  semi_major_axis=7178137 eccentricity=0.001 inclination=53.0 \
  arg_of_perigee=0 raan=45 true_anomaly=0

stk_orbit set_cartesian satellite_name=LeoSat \
  x=6998.2 y=0 z=0 vx=0 vy=7.541 vz=0.03 \
  epoch="1 Jul 2026 00:00:00"
```

- `semi_major_axis` is in **meters**; Cartesian positions are in **km**.
- Omitting `epoch` uses the scenario start time.
- `force_model` defaults to `HPOP`; `coordinate_system` defaults to `J2000`.
- `step_size` is the ephemeris step in seconds.

## Propagation window

Connect's `Propagate` defaults to roughly **1.5 hours** from the TLE epoch.
On Windows with `pywin32`, this server sets `UseScenarioAnalysisTime=True` via
COM so the ephemeris spans the full scenario. Without COM (Linux/macOS, or no
active STK instance at server start), conjunction and access results may be
incomplete. Leave `use_scenario_time=True` unless you deliberately want the
Connect default.

## Position and lifetime

```
stk_orbit position satellite_name=LeoSat time="1 Jul 2026 12:00:00"
stk_orbit lifetime satellite_name=LeoSat
```

- `position` without `time` queries the current scenario time and returns
  multi-line position data.
- `lifetime` runs STK's `Lifetime` command and returns the decay estimate.
  It is most meaningful for LEO objects with a suitable force model.

## Verification

1. `stk_orbit position` at the scenario start time.
2. `stk_util report object_path=Satellite/LeoSat style="LLA Position"`
   to confirm the ephemeris exists over the intended window.
3. Re-run `stk_scenario status` if commands start returning `Not connected`.

## Pitfalls

- Satellite names cannot contain spaces or newlines.
- A TLE set after a scenario time change still needs a fresh `propagate` if you
  later move the scenario window.
- `set_classical` with `a` in kilometres produces an orbit thousands of times
  too small; the parameter is metres.
- Position output uses the current Connect distance unit, not necessarily km.
  Use `stk_util convert_unit` or `send_command "Units_Get * Connect"` if exact
  units matter.

## Related

- Create the satellite first: [[stk-object-management]]
- Scenario and time window: [[stk-scenario-scaffold]]
- Constellation orbits: [[stk-walker-constellation]]
- Access and visibility: [[stk-access-rf-analysis]]
