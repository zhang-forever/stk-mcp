---
name: stk-conjunction
description: Run conjunction assessment (close-approach screening and collision probability) in a live STK scenario via the stk MCP server. Use when the user wants CAT/Advanced CAT, to screen a satellite against a catalog, find close approaches between two objects, or compute collision probability (Pc).
---

# STK Conjunction Assessment

Screen for close approaches and collision probability using the `stk_conjunction` MCP tool.

## Two paths

- **Basic CAT** — quick range screening of one satellite against a catalog/database.
- **Advanced CAT (ACAT)** — full workflow: primary + secondaries, prefilters, threat volume, compute, events, probability.

Prerequisites: `stk` MCP connected, a scenario loaded, and every satellite involved must have **propagated ephemeris**.

## Fast path: end-to-end assess

For screening two known objects, use `stk_conjunction` action `assess` — it creates the secondary, sets TLEs, propagates, builds an AdvCAT, computes, and returns events in one call:

| Param | Meaning |
|---|---|
| `primary_satellite` | protected object (must exist or provide TLE) |
| `secondary_satellite` | threat object (created if missing) |
| `tle_primary_line1/2`, `tle_secondary_line1/2` | TLE lines |
| `start_time`, `stop_time` | screening window |
| `threshold_km` | close-approach distance threshold |

## Basic CAT

1. `stk_conjunction` action `cat_setup` (params: satellite_name, range_threshold, optional database_path, filters, add_threats).
2. `stk_conjunction` action `cat_compute` (params: satellite_name, range_threshold) → returns close approaches.

## Advanced CAT (step by step)

1. `acat_setup` — create/configure AdvCAT (params: acat_name, start_time, stop_time, threshold, sample_step_size).
2. `acat_add_primary` — add the protected object (param: object_path, e.g. `Satellite/Sat1`).
3. `acat_add_secondary` — add a threat (param: secondary_path) or a bulk catalog (param: database_path).
4. `acat_set_prefilters` — optional coarse filters (apogee/perigee, orbit-path, time, out-of-date).
5. `acat_set_threat_volume` — configure the threat ellipsoid (tangential/cross-track/normal km, hard-body radius).
6. `acat_compute` — run the assessment.
7. `acat_events` — list conjunction events (param: sort_by, e.g. by time or range).
8. `acat_probability` — compute Pc for a specific pair (params: primary_name, secondary_name, tca_time, method e.g. `Alfano`).

## Example: two-satellite screening

```
stk_conjunction assess \
  primary_satellite=SatA secondary_satellite=SatB \
  tle_primary_line1="..." tle_primary_line2="..." \
  tle_secondary_line1="..." tle_secondary_line2="..." \
  start_time="1 Jul 2026 00:00:00" stop_time="2 Jul 2026 00:00:00" \
  threshold_km=5
```

## Notes

- Object paths for primary/secondary are relative (`Satellite/<name>`).
- Probability methods include `Alfano` (default); pass others via the `method` param.
- If compute NAKs, confirm both objects have ephemeris and the time window overlaps their propagation span.

## Related

- Build objects to screen: [[stk-walker-constellation]]
- Scenario setup and time window: [[stk-scenario-scaffold]]
