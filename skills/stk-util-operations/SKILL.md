---
name: stk-util-operations
description: Export STK reports, list report styles, convert coordinates/dates/units, read animation time, and send raw Connect commands through the stk MCP server. Use when the user needs tabular report data, unit or coordinate conversion, the current animation time, or a Connect command that has no dedicated tool action.
---

# STK Reports & Utilities

`stk_util` is the reporting and escape-hatch tool. It returns text exactly as STK
produces it; format or summarize it afterwards (for example with
[[stk-report]]).

## Reports

| Action | Parameters | Result |
|---|---|---|
| `report` | `object_path`, `style`, optional `time_period`, `time_step`, `access_object`, `all_lines` | Report lines in the tool response |
| `save_report` | same, plus `file_path` | Writes the report to disk |
| `list_report_styles` | `object_path` | Available styles, or a common fallback list |

```
stk_util report object_path=Satellite/ISS style="LLA Position" time_step=60
stk_util report object_path=Satellite/ISS style="J2000 Position Velocity" \
  time_period="1 Jul 2026 00:00:00 2 Jul 2026 00:00:00"
stk_util save_report object_path=Satellite/ISS style="LLA Position" \
  file_path="C:/temp/iss_lla.txt"
```

- `time_step` is in seconds; omit it to use STK's default sampling.
- `access_object` switches to `TimePeriod UseAccessTimes` and adds an
  `AccessObject` scope.
- `all_lines` requests the full report rather than the abbreviated form.
- Common satellite styles: `LLA Position`, `J2000 Position Velocity`,
  `Classical Orbit Elements`, `Lighting Times`, `Ephemeris-IFT`.
- Access styles: `AER`, `Access Data`. Facility/target styles: `Cartesian Position`,
  `LLA Position`, `Azimuth Elevation Mask`.

## Conversions

| Action | Parameters | Notes |
|---|---|---|
| `convert_coord` | `from_coord`, `to_coord`, `coord_values` | Comma-separated values |
| `convert_date` | `date_string`, optional `date_format` | STK date formats |
| `convert_unit` | `from_unit`, `to_unit`, `value` | Same-dimension units only |

```
stk_util convert_unit from_unit=km to_unit=m value=7000
stk_util convert_coord from_coord="J2000" to_coord="Fixed" coord_values="7000,0,0"
stk_util convert_date date_string="1 Jul 2026 12:00:00" date_format="UTCG"
```

`convert_unit` uses the supported `Units_Convert` command when both units are
recognized (common distance, time, angle, velocity, mass, temperature, and
frequency units). Unknown unit pairs fall back to STK's deprecated `ConvertUnit`;
if that returns `NAK`, use the raw command:

```
stk_util send_command command='Units_Convert * Unit Distance km "m" 7000'
```

## Animation time

```
stk_util get_animation_time
```

Returns the current animation clock. Use `stk_scenario` action `animate` to
change it.

## Raw Connect commands

`send_command` passes any STK Connect command through and shows the ACK/NAK plus
the returned payload:

```
stk_util send_command command="GetSTKVersion /"
stk_util send_command command="Chains */Chain/MyChain Add */Satellite/ISS"
```

- Only commands listed in `RETURN_DATA_COMMANDS` have their response body read.
  For other commands you receive the ACK/NAK only.
- The raw passthrough is **disabled by default**. Set
  `STK_MCP_ALLOW_RAW_COMMAND=1` in the server environment to enable
  `stk_util(action="send_command")`.
- Include the scope token (`/`, `*`) required by the command; omitting it is a
  common cause of `NAK`.
- Multi-line responses are returned as one line per row.

## Pitfalls

- Report styles are case-sensitive and object-class-specific.
- Large `all_lines` reports can produce very long tool output; prefer a time
  window or `save_report` for big exports.
- File paths for `save_report` are resolved by STK, not by the MCP server.
- A `NAK` from `send_command` is a command-syntax or scenario-state problem, not
  an MCP transport failure.

## Related

- Orbit state and propagation: [[stk-orbit-setup]]
- Report formatting: [[stk-report]]
- Access and RF data: [[stk-access-rf-analysis]]
