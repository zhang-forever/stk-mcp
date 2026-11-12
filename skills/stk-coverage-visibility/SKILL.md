---
name: stk-coverage-visibility
description: Run coverage analysis and ground-station visibility in a live STK scenario via the stk MCP server. Use when the user wants global/regional coverage, revisit time, N-asset coverage, a coverage figure of merit, or access/visibility windows between a satellite and a ground station.
---

# STK Coverage & Visibility

Compute coverage and ground-station access in the connected STK instance using the `stk` MCP tools.

## Two distinct tasks

1. **Ground-station visibility** — access windows between a satellite (or constellation) and a facility.
2. **Area coverage** — a CoverageDefinition grid evaluated by a Figure of Merit (revisit time, N-asset).

## Ground-station visibility

1. **Add the facility** — `stk_objects` action `add_facility` (params: name, latitude, longitude, altitude).
2. **Compute access** — `stk_analysis` action `access` (params: from_object, to_object).
   - Object paths are relative, e.g. `from_object=Satellite/Seed11`, `to_object=Facility/Beijing`.
   - Add `time_period` / `max_step_size` to refine.
3. For azimuth/elevation/range: `stk_analysis` action `aer`.

Example:
```
stk_objects  add_facility name=Beijing latitude=39.9 longitude=116.4 altitude=0
stk_analysis access from_object=Satellite/Seed11 to_object=Facility/Beijing
```

Returns real STK-computed access intervals (start/stop/duration).

## Area coverage (verified on live STK v11.6.0)

Use `stk_objects` action `add_coverage` — it performs the full build in one call:
CoverageDefinition → grid bounds → grid resolution → asset assignment (`Assign`) → Figure of Merit.

| Param | Meaning |
|---|---|
| `coverage_name` | name of the CoverageDefinition |
| `grid_bounds` | `Global`, or `LatBounds <min> <max>` for a latitude band |
| `grid_resolution` | grid point spacing in degrees (larger = coarser/faster) |
| `satellite_names` | comma-separated assets to Assign; **empty = assign every satellite** |
| `fom_type` | `Revisit` (max revisit time) or `NAsset` (min # satellites in view) |

Then compute:
- `stk_objects` action `compute_coverage` (param: coverage_name)
- `stk_analysis` action `coverage` (param: coverage_name) to read the FOM result.

Example: global coverage of a whole constellation
```
stk_objects  add_coverage     coverage_name=GlobalCov grid_bounds=Global grid_resolution=6 fom_type=Revisit
stk_objects  compute_coverage coverage_name=GlobalCov
stk_analysis coverage         coverage_name=GlobalCov
```

## Critical syntax facts (learned from real-machine failures)

- **Assets use `Assign`, NOT `Add`**: `Cov */CoverageDefinition/<cd> Asset */Satellite/<sat> Assign`. Both paths need the `*/` prefix. `add_coverage` handles this for you.
- **`New` separates class path and name**: `New / */CoverageDefinition <name>` — the name is a separate token, NOT `New / */CoverageDefinition/<name>` (that NAKs).
- Grid bounds keyword is `AreaOfInterest` (`Global` / `LatBounds <min> <max>` / `LatLine` / `LonLine`).
- Grid density keyword is `PointGranularity LatLon <deg>`.
- Newly assigned assets are **active by default**; no separate Activate needed.

## Interpreting results

- **Revisit FOM Maximum = 0** → continuous coverage (no gaps) at every grid point.
- **N-Asset FOM min = max = 1** → exactly one satellite always in view (continuous single coverage).

## Related

- Build the constellation first: [[stk-walker-constellation]]
- Conjunction / close-approach: [[stk-conjunction]]
