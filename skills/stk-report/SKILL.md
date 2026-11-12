---
name: stk-report
description: Format STK analysis results into structured reports. Use after any stk_conjunction, stk_analysis, stk_orbit, or stk_objects operation that returns analysis data. Produces a standardized report with scenario metadata, results table, risk/status interpretation, and recommended next steps.
---

# STK Analysis Report

After completing any STK analysis, format the results into a structured report using the templates below.

## When to apply

Apply this skill after:

- `stk_conjunction` `assess`, `acat_events`, or `acat_probability` → conjunction/collision report
- `stk_analysis` `access` or `all_access` → access windows report
- `stk_analysis` `aer` → AER observation report
- `stk_analysis` `coverage` → coverage statistics report
- `stk_orbit` `position` or `lifetime` → orbit state report
- `stk_util` `report` → generic STK formatted report

## Report structure (all types)

```
## STK Analysis Report — <Report Type>

**Scenario**: <name>  **Time Window**: <start> → <stop>  **Generated**: <UTC timestamp>

### Objects
- Primary: <object path>
- Secondary / Target: <object path>  (if applicable)

### Results
<type-specific table — see sections below>

### Summary
<1–3 sentence plain-language interpretation of the results>

**Status**: OK | CAUTION | WARNING | CRITICAL
**Next step**: <single most relevant action, naming the exact tool and action>
```

## Type-specific result sections

### Conjunction Assessment

```markdown
### Conjunction Events
| # | TCA | Miss Distance (km) | Pc | Risk |
|---|---|---|---|---|
| 1 | <time> | <dist> | <Pc> | <level> |

**Threshold**: <km>  **Events found**: <N>  **Max risk level**: <level>
```

Risk mapping:
| Condition | Status |
|---|---|
| No events within threshold, or Pc < 1e-5 | **OK** |
| Pc 1e-5 – 1e-4, or miss dist < threshold | **CAUTION** |
| Pc 1e-4 – 1e-3 | **WARNING** |
| Pc > 1e-3 or miss dist < 1 km | **CRITICAL** |

### Access / Visibility Windows

```markdown
### Access Intervals — <from_object> → <to_object>
| # | Start | Stop | Duration | Max Elevation (deg) |
|---|---|---|---|---|
| 1 | <time> | <time> | <hh:mm:ss> | <deg> |

**Total contact time**: <hh:mm:ss>  **Windows**: <N>
**Longest window**: <duration> starting <time>
```

### AER Data

```markdown
### AER — <from_object> → <to_object>
Observation window: <start> to <stop>  Step: <sec>

| Time | Az (deg) | El (deg) | Range (km) |
|---|---|---|---|
| <time> | <az> | <el> | <range> |

**Peak elevation**: <deg> at <time>  **Minimum range**: <km> at <time>
```

### Coverage

```markdown
### Coverage — <CoverageDefinition>
**Grid**: <bounds>  **Resolution**: <deg>  **Assets**: <N satellites>

| Figure of Merit | Value |
|---|---|
| Type | <Revisit / NAsset> |
| Max revisit time | <value> |
| Mean revisit time | <value> |
| Coverage % | <value>% |
```

### Orbit State / Position

```markdown
### Orbit State — <satellite>
| Parameter | Value |
|---|---|
| Semi-major axis | <km> |
| Eccentricity | <e> |
| Inclination | <deg> |
| RAAN | <deg> |
| Arg of perigee | <deg> |
| True anomaly | <deg> |
| Altitude (approx) | <km> |
| Orbital period | <min> |
```

### Orbit Lifetime

```markdown
### Orbit Lifetime — <satellite>
| Parameter | Value |
|---|---|
| Estimated decay date | <date> |
| Remaining lifetime | <days> |
| Perigee altitude | <km> |
| Apogee altitude | <km> |
```

## Formatting rules

- Round distances to 2 decimal places (km); Pc to 2 significant figures in scientific notation (e.g. `4.2e-05`).
- Always include the time window and object names in the report header.
- If raw STK output is irregularly formatted, extract the numbers and reformat — do not paste raw text blocks into the report table.
- If a tool returned NAK or empty data, state explicitly what was missing and which parameter to check.
- Keep "Next step" concrete: name the exact `tool(action=...)` call to make next.
- For CRITICAL or WARNING status, bold the status line and add a one-line risk statement before the next-step.

## Example — conjunction report

```markdown
## STK Analysis Report — Conjunction Assessment

**Scenario**: ISS_CAT  **Time Window**: 1 Jul 2026 00:00 → 2 Jul 2026 00:00  **Generated**: 2026-07-04 06:30 UTC

### Objects
- Primary: Satellite/ISS
- Secondary: Satellite/Debris_30259

### Conjunction Events
| # | TCA | Miss Distance (km) | Pc | Risk |
|---|---|---|---|---|
| 1 | 2026-07-01 14:23:11 | 3.42 | 2.1e-05 | CAUTION |
| 2 | 2026-07-01 22:47:05 | 8.17 | 4.3e-06 | OK |

**Threshold**: 10 km  **Events found**: 2  **Max risk level**: CAUTION

### Summary
Two close approaches found within the 10 km threshold. The first event at 14:23 UTC has a miss distance of 3.42 km and Pc of 2.1e-05, which is within the monitoring threshold (Pc > 1e-05). No immediate maneuver required, but continued monitoring is recommended.

**Status**: CAUTION
**Next step**: `stk_conjunction(action="acat_probability", primary_name="ISS", secondary_name="Debris_30259", tca_time="2026-07-01 14:23:11")`
```

## Related

- Run conjunction screening: [[stk-conjunction]]
- Set up scenario and objects: [[stk-scenario-scaffold]]
- Walker constellation: [[stk-walker-constellation]]
- Coverage and visibility: [[stk-coverage-visibility]]
