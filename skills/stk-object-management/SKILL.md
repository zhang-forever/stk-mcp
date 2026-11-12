---
name: stk-object-management
description: Create and inspect STK scene objects through the stk MCP server, including satellites, facilities, targets, sensors, constellations, chains, and aircraft. Use when the user needs to add a ground station, attach a sensor, build a constellation or communication chain, list scene objects, inspect properties, or remove an object.
---

# STK Object Management

All object creation goes through `stk_objects`. Object paths are relative to the
scenario: `Satellite/ISS`, `Facility/Beijing`, `Satellite/Sat1/Sensor/S1`.

## Create objects

| Object | Action | Parameters |
|---|---|---|
| Satellite | `add_satellite` | `name` |
| Facility (ground station) | `add_facility` | `name`, `latitude` (deg), `longitude` (deg), `altitude` (**m**) |
| Target | `add_target` | `name`, `latitude`, `longitude`, `altitude` |
| Sensor | `add_sensor` | `parent_path`, `name`, `cone_angle` (deg) — creates a simple cone |
| Constellation | `add_constellation` | `name`, `satellite_names` (comma-separated) |
| Chain | `add_chain` | `name` |
| Aircraft | `add_aircraft` | `name` |

```
stk_objects add_facility name=Beijing latitude=39.9 longitude=116.4 altitude=50
stk_objects add_satellite name=ISS
stk_objects add_sensor parent_path=Satellite/ISS name=Cam cone_angle=30
stk_objects add_constellation name=LeoCats satellite_names=ISS,SatA,SatB
```

`add_facility` and `add_target` set the position with `SetPosition Geodetic`
immediately after creation. If the position command is rejected, the MCP call
still reports success in the current version — verify with `get_info` or
`stk_analysis access` when coordinates matter.

## Chains need members

`add_chain` creates an **empty** chain. The tool does not expose an add-member
action, so add members with the raw Connect command:

```
stk_util send_command command="Chains */Chain/MyChain Add */Satellite/ISS"
stk_util send_command command="Chains */Chain/MyChain Add */Facility/Beijing"
```

Then run chain analysis with `stk_analysis` actions `chain_access` or
`chain_intervals`.

## Inspect and remove

```
stk_objects list object_type=Satellite
stk_objects get_info object_path=Satellite/ISS info_type=all
stk_objects remove object_path=Satellite/OldSat
```

`info_type` accepts `properties`, `description`, `subobjects`, or `all`.
`list` without `object_type` returns every instance in the scenario.

## Naming and paths

- Names cannot contain spaces; use `CamelCase` or underscores.
- Creating a duplicate name returns `NAK`; remove the old object first.
- `add_sensor` takes the **parent path** (`Satellite/ISS`), not a full sensor path.
- `remove` takes the object path relative to the scenario (`Satellite/ISS`).

## Verification

1. `stk_objects list object_type=Facility` — confirm the object exists.
2. `stk_objects get_info object_path=Facility/Beijing info_type=properties`
   — confirm coordinates and altitude.
3. `stk_analysis access from_object=Satellite/ISS to_object=Facility/Beijing`
   — confirms both objects have usable ephemeris/geometry.

## Related

- Orbit definition: [[stk-orbit-setup]]
- Walker constellations: [[stk-walker-constellation]]
- Coverage definitions: [[stk-coverage-visibility]]
- Access and link analysis: [[stk-access-rf-analysis]]
