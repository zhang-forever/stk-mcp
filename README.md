# STK MCP Server

<div align="center">

**Give AI agents direct control over [AGI STK](https://www.agi.com/products/stk) — the industry-standard astrodynamics platform.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![STK](https://img.shields.io/badge/STK-11%2B-orange)](https://www.agi.com/products/stk)
[![MCP](https://img.shields.io/badge/MCP-1.6%2B-purple)](https://modelcontextprotocol.io/)
[![GitHub Stars](https://img.shields.io/github/stars/zhang-forever/stk-mcp?style=social)](https://github.com/zhang-forever/stk-mcp)

[English](#english) | [中文](#中文)

</div>

---

## English

An MCP (Model Context Protocol) server that bridges AI agents with [AGI STK](https://www.agi.com/products/stk) (Systems Tool Kit) via the Connect TCP interface. It enables LLM-powered satellite mission analysis, conjunction assessment, coverage prediction, and scenario automation — all through natural language.

### Why STK + MCP?

STK is the gold standard for space mission analysis, but driving it programmatically requires deep domain knowledge and manual scripting. This server exposes STK's full 1100+ command library through 6 structured MCP tools, letting any AI agent (Claude, GPT, Gemini, etc.) perform complex orbital mechanics, collision screening, and visibility analysis via simple function calls.

### Features

- **6 domain tools, 58 actions** — clean, action-based API designed for LLM consumption
- **Scenario lifecycle** — create, load, save, configure time windows, animate
- **Object management** — satellites, ground stations, sensors, constellations, Walker arrays, coverage regions, aircraft, comm chains
- **Orbit definition** — TLE (SGP4), Keplerian elements, Cartesian vectors, ephemeris files, position queries, lifetime estimation
- **Conjunction assessment** — CAT close-approach screening + ACAT advanced collision probability (Pc) analysis
- **Analysis suite** — access/visibility windows, AER data, coverage footprints, comm link budgets, sensor FOV, radar cross-section, lighting conditions
- **Hybrid Connect + COM** — COM fallback (`pywin32`) fixes the `UseScenarioAnalysisTime` propagation limitation
- **Raw command passthrough** — send any of STK's 1100+ Connect commands directly

### Quick Start

**One-click install (recommended):**

```powershell
# Windows (PowerShell) — installs with COM support
git clone https://github.com/zhang-forever/stk-mcp.git
cd stk-mcp
powershell -ExecutionPolicy Bypass -File install.ps1
```

```bash
# Linux / macOS — Connect TCP only (COM is Windows-only)
git clone https://github.com/zhang-forever/stk-mcp.git
cd stk-mcp
./install.sh
```

The installer verifies prerequisites, installs dependencies (via `uv` if
available, otherwise `pip`), creates `.env`, checks that all 6 tools register,
and prints the client-configuration snippet.

**Manual install:**

```bash
git clone https://github.com/zhang-forever/stk-mcp.git
cd stk-mcp
pip install -e ".[com]"    # COM support included (recommended on Windows)
stk-mcp                     # start the server (STK must be running)
```

Then add to your MCP client (see [Client Configuration](#client-configuration) below).

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| **AGI STK** | 11+ | Connect module enabled (Edit → Preferences → Connect, port 5001) |
| **Python** | 3.10+ | 3.11 recommended |
| **pywin32** | latest | Optional — fixes orbit propagation on Windows (included with `[com]` extra) |

### STK Setup

**Enable Connect in STK:**

Open STK → **Edit** → **Preferences** → **Connect** → Check **Enable Connect Server**, port `5001`.

**Verify connectivity:**

```bash
echo "GetSTKVersion" | nc localhost 5001
# Expected: "STK 11.7.1" (or your version)
```

**Firewall (remote connections only):**

```powershell
netsh advfirewall firewall add rule name="STK Connect" dir=in action=allow protocol=TCP localport=5001
```

**COM support (Windows, recommended):**

STK's Connect `Propagate` command defaults to a ~1.5-hour window from TLE epoch. This server uses COM (`pywin32`) to set `UseScenarioAnalysisTime=True`, ensuring orbits span the full scenario period. Without COM, conjunction assessment and access analysis may return incomplete results.

### Client Configuration

The server uses **stdio transport** (default for MCP). Add it to your client's MCP configuration:

<details open>
<summary><b>Claude Code</b></summary>

**Recommended — `uvx` (no PATH setup, isolated Python 3.11):**

```bash
claude mcp add stk --scope user \
  --env STK_HOST=localhost --env STK_PORT=5001 \
  -- uvx --python 3.11 --from /path/to/stk-mcp stk-mcp
```

`--scope user` makes the server available in every project. `uvx` auto-provisions
Python 3.11 and dependencies in an isolated environment, so it works even when your
system `python` is older than 3.10 and does not require `stk-mcp` on your `PATH`.

**Alternative — installed console script:**

```bash
pip install -e ".[com]"     # installs the stk-mcp entry point
claude mcp add stk -- stk-mcp
```

Or manually create `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "stk": {
      "command": "uvx",
      "args": ["--python", "3.11", "--from", "/path/to/stk-mcp", "stk-mcp"],
      "env": { "STK_HOST": "localhost", "STK_PORT": "5001" }
    }
  }
}
```

> **Bundled skills**: this repo ships `.claude/skills/` with guided workflows
> (Walker constellation, coverage & visibility, conjunction assessment, scenario
> scaffold, and **analysis report formatting**). Open the project in Claude Code
> and they load automatically.

</details>

<details>
<summary><b>Claude Desktop</b></summary>

Edit `claude_desktop_config.json` (File → Settings → Developer → Edit Config):

```json
{
  "mcpServers": {
    "stk": {
      "command": "stk-mcp",
      "args": []
    }
  }
}
```

</details>

<details>
<summary><b>Cursor</b></summary>

Add to `.cursor/mcp.json` in your project root, or configure in Settings → MCP:

```json
{
  "mcpServers": {
    "stk": {
      "command": "stk-mcp",
      "args": []
    }
  }
}
```

</details>

<details>
<summary><b>Windsurf</b></summary>

Edit `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "stk": {
      "command": "stk-mcp",
      "args": []
    }
  }
}
```

</details>

<details>
<summary><b>QoderWork</b></summary>

Add via the MCP server settings panel, or configure manually:

```json
{
  "mcpServers": {
    "stk": {
      "command": "stk-mcp",
      "args": []
    }
  }
}
```

</details>

<details>
<summary><b>Other MCP Clients</b></summary>

Any MCP-compatible client can use this server. Add the following to your client's MCP configuration:

```json
{
  "mcpServers": {
    "stk": {
      "command": "stk-mcp",
      "args": []
    }
  }
}
```

For remote STK instances, pass environment variables:

```json
{
  "mcpServers": {
    "stk": {
      "command": "stk-mcp",
      "args": [],
      "env": {
        "STK_HOST": "192.168.1.100",
        "STK_PORT": "5001"
      }
    }
  }
}
```

If `stk-mcp` is not in your PATH, use the full path:

```json
{
  "command": "/path/to/stk-mcp/.venv/Scripts/stk-mcp.exe"
}
```

</details>

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `STK_HOST` | `localhost` | STK host address (use IP for remote) |
| `STK_PORT` | `5001` | STK Connect TCP port |

### Tool Reference

Six domain tools, 58 actions. Each tool takes an `action` string plus action-specific
parameters. Expand each tool below for its full action/parameter table.

| Tool | Actions | Description |
|---|---|---|
| **`stk_scenario`** | 9 | Scenario lifecycle and time management |
| **`stk_objects`** | 13 | Create and manage scene objects |
| **`stk_orbit`** | 7 | Orbit definition, propagation, and queries |
| **`stk_conjunction`** | 11 | Collision warning (CAT + ACAT) |
| **`stk_analysis`** | 10 | Visibility, coverage, and RF analysis |
| **`stk_util`** | 8 | Reports, conversions, raw commands |

<details>
<summary><b>stk_scenario — Scenario Lifecycle (9 actions)</b></summary>

| Action | Required | Optional | Returns |
|---|---|---|---|
| `connect` | — | `host`, `port` | Connection confirmation |
| `disconnect` | — | — | Disconnect confirmation |
| `status` | — | — | STK version + scenario loaded state |
| `new` | `name` | `start_time`, `stop_time` | Scenario created |
| `load` | `file_path` | — | Scenario loaded from `.sc` |
| `save` | — | `file_path` | Save confirmation |
| `unload` | — | — | Scenario closed |
| `set_time_period` | `start_time`, `stop_time` | — | Analytical window set |
| `animate` | — | `animate_action` (Start/Pause/Reset/Faster/Slower/StepForward/StepReverse/Loop/RealTime/Refresh) | Animation state |

</details>

<details>
<summary><b>stk_objects — Object Management (13 actions)</b></summary>

| Action | Required | Optional | Returns |
|---|---|---|---|
| `add_satellite` | `name` | — | Satellite created |
| `add_facility` | `name` | `latitude`, `longitude`, `altitude` | Ground station created |
| `add_target` | `name` | `latitude`, `longitude`, `altitude` | Ground target created |
| `add_sensor` | `parent_path`, `name` | `cone_angle` (deg) | Sensor attached |
| `add_constellation` | `name` | `satellite_names` (comma-sep) | Constellation created |
| `add_chain` | `name` | — | Comm chain created |
| `add_aircraft` | `name` | — | Aircraft created |
| `walker` | `name` (seed sat), `num_planes`, `num_sats_per_plane` | `walker_type` (Delta/Star/Custom), `inter_plane_phase_increment`, `color_by_plane`, `constellation_name` | Walker array built |
| `add_coverage` | `coverage_name` | `grid_bounds` (Global/LatBounds), `grid_resolution` (deg), `satellite_names`, `fom_type` (Revisit/NAsset) | CoverageDefinition created |
| `compute_coverage` | `coverage_name` | — | Coverage computed |
| `list` | — | `object_type` (filter) | Object list |
| `remove` | `object_path` | — | Object removed |
| `get_info` | `object_path` | `info_type` (properties/description/subobjects/all) | Object info |

> **Note**: the `walker` seed satellite must already have propagated ephemeris.

</details>

<details>
<summary><b>stk_orbit — Orbit Definition & Propagation (7 actions)</b></summary>

| Action | Required | Optional | Returns |
|---|---|---|---|
| `set_tle` | `satellite_name`, `tle_line1`, `tle_line2` | — | Orbit set (SGP4) + propagated |
| `set_classical` | `satellite_name` | `semi_major_axis` (m), `eccentricity`, `inclination` (deg), `arg_of_perigee`, `raan`, `true_anomaly`, `epoch`, `coordinate_system`, `force_model`, `step_size` | Keplerian orbit set |
| `set_cartesian` | `satellite_name` | `x`/`y`/`z` (km), `vx`/`vy`/`vz` (km/s), `epoch`, `coordinate_system`, `force_model`, `step_size` | Cartesian orbit set |
| `from_file` | `satellite_name`, `file_path` | — | Ephemeris loaded |
| `propagate` | `satellite_name` | `use_scenario_time` | Propagation confirmation |
| `position` | `satellite_name` | `time` | Position at time |
| `lifetime` | `satellite_name` | — | Decay/lifetime estimate |

> `set_classical`/`set_cartesian` default `epoch` to the scenario start time if omitted.
> COM (Windows) sets `UseScenarioAnalysisTime=True` so propagation spans the full scenario.

</details>

<details>
<summary><b>stk_conjunction — Collision Warning (11 actions)</b></summary>

| Action | Required | Optional | Returns |
|---|---|---|---|
| `cat_setup` | `satellite_name` | `range_threshold` (km), `database_path`, `filter_apogee_perigee`, `filter_orbit_path`, `add_threats`, `max_threats` | CAT configured |
| `cat_compute` | `satellite_name` | `range_threshold` | Close approaches |
| `acat_setup` | — | `acat_name`, `start_time`, `stop_time`, `threshold` (km), `sample_step_size` | AdvCAT configured |
| `acat_add_primary` | `object_path` | `acat_name` | Primary added |
| `acat_add_secondary` | `secondary_path` **or** `database_path` | `acat_name` | Secondary added |
| `acat_set_prefilters` | — | `out_of_date`, `apogee_perigee`, `orbit_path`, `time_filter` | Prefilters set |
| `acat_set_threat_volume` | — | `dimension_type`, `tangential_km`, `cross_track_km`, `normal_km`, `hard_body_radius_m` | Unsupported; no settings changed (see below) |
| `acat_compute` | — | `acat_name` | Computation done |
| `acat_events` | — | `acat_name`, `sort_by` | Conjunction events |
| `acat_probability` | `primary_name`, `secondary_name`, `tca_time` | `method` (Alfano) | Collision probability (Pc) |
| `assess` | `primary_satellite`, `secondary_satellite` | `tle_*_line1/2`, `start_time`, `stop_time`, `threshold_km` | End-to-end assessment |

> `acat_set_threat_volume` currently returns an explicit unsupported result and changes no STK settings. Dimensions and hard-body radius must be bound to a primary/secondary object using STK or the [ACAT command](https://help.agi.com/stk/Subsystems/connectCmds/Content/cmd_ACAT.htm), with the appropriate Connect units.

> `assess` is the fast path: creates the secondary, sets TLEs, propagates, builds AdvCAT,
> computes, and returns events in a single call.

</details>

<details>
<summary><b>stk_analysis — Visibility, Coverage & RF (10 actions)</b></summary>

| Action | Required | Optional | Returns |
|---|---|---|---|
| `access` | `from_object`, `to_object` | `time_period`, `max_step_size` | Access intervals |
| `all_access` | `from_object` | — | Access to all objects |
| `aer` | `from_object`, `to_object` | `time_period`, `max_step_size` | Azimuth/Elevation/Range |
| `chain_access` | `chain_name` | — | Chain access analysis |
| `chain_intervals` | `chain_name` | — | Chain time intervals |
| `coverage` | `coverage_name` | — | Coverage FOM data |
| `comm_link` | — | `comm_system`, `query_type` | Comm system query |
| `sensor_fov` | `sensor_path` | — | Sensor field-of-view |
| `visibility` | `from_object`, `to_object` | — | Lighting/visibility |
| `radar` | `object_path` | — | Radar analysis |

> Object paths are relative, e.g. `Satellite/ISS`, `Facility/GS1`, `Satellite/Sat1/Sensor/Sensor1`.

</details>

<details>
<summary><b>stk_util — Reports, Conversions & Raw Commands (8 actions)</b></summary>

| Action | Required | Optional | Returns |
|---|---|---|---|
| `report` | `object_path`, `style` | `time_period`, `time_step`, `access_object`, `all_lines` | Report data |
| `save_report` | `object_path`, `style`, `file_path` | `time_period`, `time_step`, `access_object` | Save confirmation |
| `list_report_styles` | `object_path` | — | Available report styles |
| `convert_coord` | `from_coord`, `to_coord`, `coord_values` | — | Converted coordinates |
| `convert_date` | `date_string` | `date_format` | Converted date |
| `convert_unit` | `from_unit`, `to_unit`, `value` | — | Converted value |
| `get_animation_time` | — | — | Current animation time |
| `send_command` | `command` | — | Raw Connect command result |

</details>

### Usage Examples

**Create a scenario and add a satellite:**

```python
stk_scenario(action="new", name="ISS_Track",
             start_time="11 Jun 2026 00:00:00", stop_time="+7days")
stk_objects(action="add_satellite", name="ISS")
stk_orbit(action="set_tle", satellite_name="ISS",
          tle_line1="1 25544U 98067A   ...",
          tle_line2="2 25544  51.6442 ...")
stk_orbit(action="propagate", satellite_name="ISS")
```

**Query satellite position:**

```python
stk_orbit(action="position", satellite_name="ISS",
          time="14 Jun 2026 12:00:00")
```

**Run conjunction assessment:**

```python
stk_conjunction(action="assess",
                primary_satellite="ISS",
                secondary_satellite="Debris_30259",
                threshold_km=10)
```

**Compute access windows:**

```python
stk_analysis(action="access",
             from_object="Satellite/ISS",
             to_object="Facility/GroundStation")
```

**Send any raw STK command:**

```python
stk_util(action="send_command",
         command="New / */Constellation MyConstellation")
```

### Workflow Examples

End-to-end sequences an agent can drive with natural-language prompts.

**1. Conjunction assessment (two objects → risk report)**

```python
# 1. Scenario + time window
stk_scenario(action="new", name="CAT_Demo",
             start_time="1 Jul 2026 00:00:00", stop_time="+2days")
# 2. End-to-end screen: creates secondary, sets TLEs, propagates, computes
stk_conjunction(action="assess",
                primary_satellite="ISS",
                secondary_satellite="Debris",
                tle_primary_line1="1 25544U ...", tle_primary_line2="2 25544 ...",
                tle_secondary_line1="1 30259U ...", tle_secondary_line2="2 30259 ...",
                start_time="1 Jul 2026 00:00:00", stop_time="3 Jul 2026 00:00:00",
                threshold_km=10)
# 3. Drill into a specific pair's collision probability
stk_conjunction(action="acat_probability",
                acat_name="ConjunctionAssessment",
                primary_name="ISS", secondary_name="Debris",
                tca_time="1 Jul 2026 14:23:11", method="Alfano")
# → the stk-report skill formats events + Pc into a risk-rated report
```

**2. Walker constellation + coverage analysis**

```python
# 1. Seed satellite with propagated ephemeris
stk_objects(action="add_satellite", name="Seed")
stk_orbit(action="set_classical", satellite_name="Seed",
          semi_major_axis=7178137, eccentricity=0.0, inclination=53.0)
stk_orbit(action="propagate", satellite_name="Seed")
# 2. Build a 6×4 Walker Delta (24 satellites)
stk_objects(action="walker", name="Seed", walker_type="Delta",
            num_planes=6, num_sats_per_plane=4,
            constellation_name="MyWalker")
# 3. Define a global coverage grid and compute revisit time
stk_objects(action="add_coverage", coverage_name="GlobalCov",
            grid_bounds="Global", grid_resolution=6.0, fom_type="Revisit")
stk_objects(action="compute_coverage", coverage_name="GlobalCov")
stk_analysis(action="coverage", coverage_name="GlobalCov")
# → stk-report skill formats the FOM into a coverage statistics report
```

**3. Ground-station access + AER report**

```python
stk_objects(action="add_facility", name="GS1",
            latitude=40.0, longitude=-105.0, altitude=1600)
stk_analysis(action="access",
             from_object="Satellite/ISS", to_object="Facility/GS1")
stk_analysis(action="aer",
             from_object="Facility/GS1", to_object="Satellite/ISS",
             max_step_size=60)
# → stk-report skill formats contact windows + peak elevation into an access report
```

### Result Reports

The bundled **`stk-report`** skill (`.claude/skills/stk-report/`) formats raw STK output
into structured, risk-rated reports. After any analysis, the agent produces a report with:

- **Header** — scenario name, time window, objects involved
- **Results table** — type-specific (conjunction events, access intervals, AER, coverage, orbit state)
- **Summary** — plain-language interpretation
- **Status** — `OK` / `CAUTION` / `WARNING` / `CRITICAL` (conjunction risk is mapped from Pc and miss distance)
- **Next step** — the concrete follow-up tool/action to call

Example conjunction report:

```markdown
## STK Analysis Report — Conjunction Assessment

**Scenario**: ISS_CAT  **Time Window**: 1 Jul 2026 00:00 → 2 Jul 2026 00:00

### Conjunction Events
| # | TCA | Miss Distance (km) | Pc | Risk |
|---|---|---|---|---|
| 1 | 2026-07-01 14:23:11 | 3.42 | 2.1e-05 | CAUTION |

**Status**: CAUTION — Pc above monitoring threshold (1e-05)
**Next step**: continue monitoring; recompute Pc closer to TCA
```

### Architecture

```
┌─────────────────────────────────────────────┐
│            MCP Client (LLM Agent)           │
│                  stdio transport             │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│           stk-mcp Server (FastMCP)           │
│                                              │
│  ┌────────────┐  ┌───────────┐  ┌─────────┐ │
│  │stk_scenario│  │stk_objects│  │stk_orbit│ │
│  │ 9 actions  │  │ 13 actions│  │7 actions│ │
│  └────────────┘  └───────────┘  └─────────┘ │
│  ┌──────────────┐ ┌───────────┐ ┌──────────┐│
│  │stk_conjunct. │ │stk_analys.│ │ stk_util ││
│  │  11 actions  │ │ 10 actions│ │ 8 actions││
│  └──────────────┘ └───────────┘ └──────────┘│
│                                              │
│  ┌─────────────────────────────────────────┐ │
│  │          StkState (lifespan)            │ │
│  │  ┌──────────────┐  ┌────────────────┐  │ │
│  │  │ConnectClient │  │  COM (pywin32) │  │ │
│  │  │  TCP :5001   │  │STK11.Application│  │ │
│  │  └──────┬───────┘  └───────┬────────┘  │ │
│  └─────────┼──────────────────┼────────────┘ │
└────────────┼──────────────────┼──────────────┘
             │                  │
      ┌──────▼──────────────────▼──────┐
      │         AGI STK 11+            │
      │    (running on localhost)       │
      └────────────────────────────────┘
```

**Dual-protocol design:**

- **Connect TCP** (primary): Object creation, orbit setting, ACAT computation, reports — fast, covers 1100+ commands
- **COM** (supplementary): Fixes the `UseScenarioAnalysisTime` property that Connect cannot set, ensuring full-scenario orbit propagation

### Connect Protocol Reference

STK Connect is a text-based TCP protocol on port 5001:

| Operation | Format |
|---|---|
| **Send command** | `CommandName ObjectPath Options\n` |
| **Success** | `ACK\n` |
| **Failure** | `NAK\n` |
| **Return data** | 40-byte header `COMMANDNAME  NUMBYTES\n` + data payload |
| **Multi-line** | Row count first, then repeated header+data per row |

Full command reference: *STK Help → Programming → Connect Command Library*.

### Project Structure

```
stk-mcp/
├── pyproject.toml              # Package config (hatchling build)
├── install.ps1                 # One-click installer (Windows)
├── install.sh                  # One-click installer (Linux/macOS)
├── src/stk_mcp/
│   ├── app.py                  # FastMCP instance + lifespan
│   ├── server.py               # Entry point, tool registration
│   ├── connect_client.py       # STK Connect TCP protocol client
│   ├── logic/
│   │   └── stk_state.py        # State management (Connect + COM)
│   └── tools/
│       ├── scenario.py         # stk_scenario (9 actions)
│       ├── objects.py          # stk_objects (13 actions)
│       ├── orbit.py            # stk_orbit (7 actions)
│       ├── cat.py              # stk_conjunction (11 actions)
│       ├── analysis.py         # stk_analysis (10 actions)
│       └── util.py             # stk_util (8 actions)
├── .claude/skills/             # Bundled Claude Code skills
│   ├── stk-scenario-scaffold/  # Scenario setup workflow
│   ├── stk-walker-constellation/ # Walker constellation build
│   ├── stk-coverage-visibility/  # Coverage & visibility analysis
│   ├── stk-conjunction/        # Conjunction assessment workflow
│   └── stk-report/             # Analysis report formatting
└── tests/
    ├── mock_stk_server.py      # Mock STK Connect server for offline tests
    ├── test_connect_protocol.py # Offline protocol tests (no STK required)
    └── test_com.py             # COM interface integration test
```

### Known Limitations

- **Orbit propagation window**: Connect's `Propagate` defaults to ~1.5 hours from TLE epoch. COM fixes this on Windows. Without COM (e.g. Linux), orbits may not cover the full scenario period.
- **ACAT database format**: `Secondary AddDatabase` only accepts `.sd`/`.tce` files, not plain-text TLE. For TLE catalogs, create satellite objects individually.
- **STK must be running**: Start STK before launching the server, or use `stk_scenario(action="connect")` to retry.
- **Windows-only COM**: COM (`STK11.Application`) requires Windows. Connect TCP works cross-platform.

### Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Not connected to STK` | STK not running, or Connect Server disabled | Start STK, enable Connect (Edit → Preferences → Connect, port 5001), then `stk_scenario(action="connect")` |
| Connection refused / timeout | Wrong host/port, or firewall blocking | Verify `STK_PORT=5001`; for remote hosts open the firewall rule and set `STK_HOST` to the STK machine IP |
| Tool returns `NAK` | Invalid object path, or command needs a loaded scenario | Check the path is relative (`Satellite/ISS`, not `*/Satellite/ISS`); confirm a scenario is loaded via `stk_scenario(action="status")` |
| Conjunction/access returns no data | Orbits not propagated, or window outside propagation span | Run `stk_orbit(action="propagate", ...)`; ensure the analysis time window overlaps the propagated ephemeris |
| Orbit only spans ~1.5 h | Connect propagation default (no COM) | Install with `[com]` on Windows so `UseScenarioAnalysisTime` is set automatically |
| `walker` fails | Seed satellite has no ephemeris | Propagate the seed satellite before calling `walker` |
| Server won't import | Wrong Python version | Requires Python 3.10+ (3.11 recommended); use `uvx --python 3.11` to avoid PATH issues |

To inspect the raw protocol exchange, use `stk_util(action="send_command", command="...")`
and read the `ACK`/`NAK` plus data payload directly.

### Contributing

Contributions are welcome. To add new tool actions:

1. Fork the repo and create a feature branch
2. Add your action in the appropriate tool module under `src/stk_mcp/tools/`
3. Follow the existing action-dispatch pattern (`if action == "your_action":`)
4. Test against a running STK instance
5. Submit a pull request

### License

[MIT](LICENSE) — free for personal and commercial use.

---

## 中文

基于 MCP (Model Context Protocol) 的 STK 控制服务器，通过 Connect TCP 接口让 AI Agent 直接操控 [AGI STK](https://www.agi.com/products/stk)（Systems Tool Kit）——航天任务分析的行业标准平台。通过自然语言即可驱动卫星任务分析、碰撞预警、覆盖预测和场景自动化。

### 为什么选择 STK + MCP？

STK 是航天任务分析的黄金标准，但编程驱动它需要深厚的领域知识和大量手工脚本。本项目将 STK 的 1100+ 命令库封装为 6 个结构化 MCP 工具，让任何 AI Agent（Claude、GPT、Gemini 等）通过简单的函数调用完成复杂轨道力学、碰撞筛查和可见性分析。

### 功能特性

- **6 个领域工具，58 个动作** — 为 LLM 设计的简洁 action 分发接口
- **场景生命周期** — 创建、加载、保存、配置时间窗口、动画控制
- **对象管理** — 卫星、地面站、传感器、星座、Walker 星座、覆盖区域、飞行器、通信链
- **轨道定义** — TLE (SGP4)、经典轨道根数、笛卡尔向量、星历文件、位置查询、寿命估算
- **碰撞预警** — CAT 近距离筛查 + ACAT 高级碰撞概率 (Pc) 分析
- **分析套件** — 可见性窗口、AER 数据、覆盖足迹、通信链路预算、传感器视场、雷达截面、光照条件
- **Connect + COM 混合架构** — COM 辅助 (`pywin32`) 修复 `UseScenarioAnalysisTime` 传播窗口限制
- **原始命令透传** — 直接发送 STK 的 1100+ Connect 命令

### 快速开始

**一键安装（推荐）：**

```powershell
# Windows (PowerShell) — 含 COM 支持
git clone https://github.com/zhang-forever/stk-mcp.git
cd stk-mcp
powershell -ExecutionPolicy Bypass -File install.ps1
```

```bash
# Linux / macOS — 仅 Connect TCP（COM 仅限 Windows）
git clone https://github.com/zhang-forever/stk-mcp.git
cd stk-mcp
./install.sh
```

安装脚本会自动检查环境、安装依赖（优先用 `uv`，否则回退 `pip`）、创建 `.env`、
验证 6 个工具注册成功，并打印客户端配置片段。

**手动安装：**

```bash
git clone https://github.com/zhang-forever/stk-mcp.git
cd stk-mcp
pip install -e ".[com]"    # 包含 COM 支持（Windows 推荐）
stk-mcp                     # 启动服务器（需 STK 已运行）
```

然后在你的 MCP 客户端中配置（见下方[客户端配置](#客户端配置)）。

### 环境要求

| 依赖 | 版本 | 说明 |
|---|---|---|
| **AGI STK** | 11+ | 需启用 Connect 模块（Edit → Preferences → Connect，端口 5001） |
| **Python** | 3.10+ | 推荐 3.11 |
| **pywin32** | 最新 | 可选 — 修复 Windows 上的轨道传播（`[com]` 已包含） |

### STK 配置

**启用 Connect 模块：**

打开 STK → **Edit** → **Preferences** → **Connect** → 勾选 **Enable Connect Server**，端口 `5001`。

**验证连通性：**

```bash
echo "GetSTKVersion" | nc localhost 5001
# 预期返回："STK 11.7.1"（或你的版本号）
```

**防火墙（仅远程连接）：**

```powershell
netsh advfirewall firewall add rule name="STK Connect" dir=in action=allow protocol=TCP localport=5001
```

**COM 支持（Windows，推荐）：**

Connect 的 `Propagate` 命令默认只传播 TLE 历元起约 1.5 小时。本服务器通过 COM (`pywin32`) 设置 `UseScenarioAnalysisTime=True`，确保轨道覆盖完整场景时段。没有 COM 时碰撞预警和可见性分析可能返回不完整结果。

### 客户端配置

服务器使用 **stdio 传输**（MCP 默认）。将以下配置添加到你的 MCP 客户端：

<details open>
<summary><b>Claude Code</b></summary>

在项目目录中运行：

```bash
claude mcp add stk -- stk-mcp
```

或在项目根目录创建 `.mcp.json`：

```json
{
  "mcpServers": {
    "stk": {
      "command": "stk-mcp",
      "args": []
    }
  }
}
```

</details>

<details>
<summary><b>Claude Desktop</b></summary>

编辑 `claude_desktop_config.json`（File → Settings → Developer → Edit Config）：

```json
{
  "mcpServers": {
    "stk": {
      "command": "stk-mcp",
      "args": []
    }
  }
}
```

</details>

<details>
<summary><b>Cursor</b></summary>

在项目根目录创建 `.cursor/mcp.json`，或在 Settings → MCP 中配置：

```json
{
  "mcpServers": {
    "stk": {
      "command": "stk-mcp",
      "args": []
    }
  }
}
```

</details>

<details>
<summary><b>Windsurf</b></summary>

编辑 `~/.codeium/windsurf/mcp_config.json`：

```json
{
  "mcpServers": {
    "stk": {
      "command": "stk-mcp",
      "args": []
    }
  }
}
```

</details>

<details>
<summary><b>QoderWork</b></summary>

在 MCP 服务器设置面板中添加，或手动配置：

```json
{
  "mcpServers": {
    "stk": {
      "command": "stk-mcp",
      "args": []
    }
  }
}
```

</details>

<details>
<summary><b>其他 MCP 客户端</b></summary>

任何兼容 MCP 的客户端均可使用。添加到你的 MCP 配置中：

```json
{
  "mcpServers": {
    "stk": {
      "command": "stk-mcp",
      "args": []
    }
  }
}
```

远程 STK 实例可传入环境变量：

```json
{
  "mcpServers": {
    "stk": {
      "command": "stk-mcp",
      "args": [],
      "env": {
        "STK_HOST": "192.168.1.100",
        "STK_PORT": "5001"
      }
    }
  }
}
```

如果 `stk-mcp` 不在 PATH 中，使用完整路径：

```json
{
  "command": "/path/to/stk-mcp/.venv/Scripts/stk-mcp.exe"
}
```

</details>

### 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `STK_HOST` | `localhost` | STK 主机地址（远程时填 IP） |
| `STK_PORT` | `5001` | STK Connect TCP 端口 |

### 工具列表

6 个领域工具，58 个动作。每个工具接受一个 `action` 字符串加动作专属参数。
展开下方各工具查看完整的动作/参数表。

| 工具 | 动作数 | 说明 |
|---|---|---|
| **`stk_scenario`** | 9 | 场景生命周期与时间管理 |
| **`stk_objects`** | 13 | 对象创建与管理 |
| **`stk_orbit`** | 7 | 轨道定义、传播与查询 |
| **`stk_conjunction`** | 11 | 碰撞预警 (CAT + ACAT) |
| **`stk_analysis`** | 10 | 可见性、覆盖与射频分析 |
| **`stk_util`** | 8 | 报告、转换与原始命令 |

<details>
<summary><b>stk_scenario — 场景生命周期（9 动作）</b></summary>

| 动作 | 必填 | 可选 | 返回 |
|---|---|---|---|
| `connect` | — | `host`, `port` | 连接确认 |
| `disconnect` | — | — | 断开确认 |
| `status` | — | — | STK 版本 + 场景加载状态 |
| `new` | `name` | `start_time`, `stop_time` | 场景已创建 |
| `load` | `file_path` | — | 从 `.sc` 加载 |
| `save` | — | `file_path` | 保存确认 |
| `unload` | — | — | 场景已关闭 |
| `set_time_period` | `start_time`, `stop_time` | — | 分析时间窗口已设 |
| `animate` | — | `animate_action`（Start/Pause/Reset/Faster/Slower/StepForward/StepReverse/Loop/RealTime/Refresh） | 动画状态 |

</details>

<details>
<summary><b>stk_objects — 对象管理（13 动作）</b></summary>

| 动作 | 必填 | 可选 | 返回 |
|---|---|---|---|
| `add_satellite` | `name` | — | 卫星已创建 |
| `add_facility` | `name` | `latitude`, `longitude`, `altitude` | 地面站已创建 |
| `add_target` | `name` | `latitude`, `longitude`, `altitude` | 地面目标已创建 |
| `add_sensor` | `parent_path`, `name` | `cone_angle`（度） | 传感器已挂载 |
| `add_constellation` | `name` | `satellite_names`（逗号分隔） | 星座已创建 |
| `add_chain` | `name` | — | 通信链已创建 |
| `add_aircraft` | `name` | — | 飞行器已创建 |
| `walker` | `name`（种子卫星）, `num_planes`, `num_sats_per_plane` | `walker_type`（Delta/Star/Custom）, `inter_plane_phase_increment`, `color_by_plane`, `constellation_name` | Walker 星座已构建 |
| `add_coverage` | `coverage_name` | `grid_bounds`（Global/LatBounds）, `grid_resolution`（度）, `satellite_names`, `fom_type`（Revisit/NAsset） | 覆盖定义已创建 |
| `compute_coverage` | `coverage_name` | — | 覆盖已计算 |
| `list` | — | `object_type`（过滤） | 对象列表 |
| `remove` | `object_path` | — | 对象已移除 |
| `get_info` | `object_path` | `info_type`（properties/description/subobjects/all） | 对象信息 |

> **注意**：`walker` 的种子卫星必须已有传播好的星历。

</details>

<details>
<summary><b>stk_orbit — 轨道定义与传播（7 动作）</b></summary>

| 动作 | 必填 | 可选 | 返回 |
|---|---|---|---|
| `set_tle` | `satellite_name`, `tle_line1`, `tle_line2` | — | 轨道已设 (SGP4) 并传播 |
| `set_classical` | `satellite_name` | `semi_major_axis`（米）, `eccentricity`, `inclination`（度）, `arg_of_perigee`, `raan`, `true_anomaly`, `epoch`, `coordinate_system`, `force_model`, `step_size` | 经典轨道已设 |
| `set_cartesian` | `satellite_name` | `x`/`y`/`z`（km）, `vx`/`vy`/`vz`（km/s）, `epoch`, `coordinate_system`, `force_model`, `step_size` | 笛卡尔轨道已设 |
| `from_file` | `satellite_name`, `file_path` | — | 星历已加载 |
| `propagate` | `satellite_name` | `use_scenario_time` | 传播确认 |
| `position` | `satellite_name` | `time` | 指定时刻位置 |
| `lifetime` | `satellite_name` | — | 寿命/衰减估算 |

> `set_classical`/`set_cartesian` 省略 `epoch` 时默认取场景起始时间。
> COM（Windows）会设置 `UseScenarioAnalysisTime=True`，使传播覆盖完整场景。

</details>

<details>
<summary><b>stk_conjunction — 碰撞预警（11 动作）</b></summary>

| 动作 | 必填 | 可选 | 返回 |
|---|---|---|---|
| `cat_setup` | `satellite_name` | `range_threshold`（km）, `database_path`, `filter_apogee_perigee`, `filter_orbit_path`, `add_threats`, `max_threats` | CAT 已配置 |
| `cat_compute` | `satellite_name` | `range_threshold` | 近距离事件 |
| `acat_setup` | — | `acat_name`, `start_time`, `stop_time`, `threshold`（km）, `sample_step_size` | AdvCAT 已配置 |
| `acat_add_primary` | `object_path` | `acat_name` | 主对象已添加 |
| `acat_add_secondary` | `secondary_path` **或** `database_path` | `acat_name` | 次对象已添加 |
| `acat_set_prefilters` | — | `out_of_date`, `apogee_perigee`, `orbit_path`, `time_filter` | 预筛选已设 |
| `acat_set_threat_volume` | — | `dimension_type`, `tangential_km`, `cross_track_km`, `normal_km`, `hard_body_radius_m` | 暂不支持，不修改设置（见下文） |
| `acat_compute` | — | `acat_name` | 计算完成 |
| `acat_events` | — | `acat_name`, `sort_by` | 交会事件 |
| `acat_probability` | `primary_name`, `secondary_name`, `tca_time` | `method`（Alfano） | 碰撞概率 (Pc) |
| `assess` | `primary_satellite`, `secondary_satellite` | `tle_*_line1/2`, `start_time`, `stop_time`, `threshold_km` | 端到端评估 |

> `acat_set_threat_volume` 暂不支持，会明确返回提示且不修改 STK 设置。尺寸和硬体半径需通过 STK 或 [ACAT 命令](https://help.agi.com/stk/Subsystems/connectCmds/Content/cmd_ACAT.htm)绑定到具体主/次对象，并核对 Connect 单位。

> `assess` 是快捷路径：一次调用完成创建次对象、设 TLE、传播、建 AdvCAT、计算并返回事件。

</details>

<details>
<summary><b>stk_analysis — 可见性、覆盖与射频（10 动作）</b></summary>

| 动作 | 必填 | 可选 | 返回 |
|---|---|---|---|
| `access` | `from_object`, `to_object` | `time_period`, `max_step_size` | 访问时段 |
| `all_access` | `from_object` | — | 对所有对象的访问 |
| `aer` | `from_object`, `to_object` | `time_period`, `max_step_size` | 方位/俯仰/距离 |
| `chain_access` | `chain_name` | — | 通信链访问分析 |
| `chain_intervals` | `chain_name` | — | 通信链时段 |
| `coverage` | `coverage_name` | — | 覆盖 FOM 数据 |
| `comm_link` | — | `comm_system`, `query_type` | 通信系统查询 |
| `sensor_fov` | `sensor_path` | — | 传感器视场 |
| `visibility` | `from_object`, `to_object` | — | 光照/可见性 |
| `radar` | `object_path` | — | 雷达分析 |

> 对象路径为相对路径，如 `Satellite/ISS`、`Facility/GS1`、`Satellite/Sat1/Sensor/Sensor1`。

</details>

<details>
<summary><b>stk_util — 报告、转换与原始命令（8 动作）</b></summary>

| 动作 | 必填 | 可选 | 返回 |
|---|---|---|---|
| `report` | `object_path`, `style` | `time_period`, `time_step`, `access_object`, `all_lines` | 报告数据 |
| `save_report` | `object_path`, `style`, `file_path` | `time_period`, `time_step`, `access_object` | 保存确认 |
| `list_report_styles` | `object_path` | — | 可用报告样式 |
| `convert_coord` | `from_coord`, `to_coord`, `coord_values` | — | 转换后坐标 |
| `convert_date` | `date_string` | `date_format` | 转换后日期 |
| `convert_unit` | `from_unit`, `to_unit`, `value` | — | 转换后数值 |
| `get_animation_time` | — | — | 当前动画时间 |
| `send_command` | `command` | — | 原始 Connect 命令结果 |

</details>

### 调用示例

**创建场景并添加卫星：**

```python
stk_scenario(action="new", name="CAT_Scene",
             start_time="11 Jun 2026 00:00:00", stop_time="+7days")
stk_objects(action="add_satellite", name="Primary")
stk_orbit(action="set_tle", satellite_name="Primary",
          tle_line1="1 55107U ...",
          tle_line2="2 55107 ...")
stk_orbit(action="propagate", satellite_name="Primary")
```

**查询卫星位置：**

```python
stk_orbit(action="position", satellite_name="Primary",
          time="14 Jun 2026 12:00:00")
```

**执行碰撞预警分析：**

```python
stk_conjunction(action="assess",
                primary_satellite="Primary",
                secondary_satellite="Debris_30259",
                threshold_km=10)
```

**计算可见性窗口：**

```python
stk_analysis(action="access",
             from_object="Satellite/Primary",
             to_object="Facility/GS1")
```

**发送任意 STK 命令：**

```python
stk_util(action="send_command",
         command="New / */Constellation MyConstellation")
```

### 工作流示例

Agent 可通过自然语言驱动的端到端流程。

**1. 碰撞预警（两个对象 → 风险报告）**

```python
# 1. 场景 + 时间窗口
stk_scenario(action="new", name="CAT_Demo",
             start_time="1 Jul 2026 00:00:00", stop_time="+2days")
# 2. 端到端筛查：创建次对象、设 TLE、传播、计算
stk_conjunction(action="assess",
                primary_satellite="ISS",
                secondary_satellite="Debris",
                tle_primary_line1="1 25544U ...", tle_primary_line2="2 25544 ...",
                tle_secondary_line1="1 30259U ...", tle_secondary_line2="2 30259 ...",
                start_time="1 Jul 2026 00:00:00", stop_time="3 Jul 2026 00:00:00",
                threshold_km=10)
# 3. 深入分析某对交会的碰撞概率
stk_conjunction(action="acat_probability",
                acat_name="ConjunctionAssessment",
                primary_name="ISS", secondary_name="Debris",
                tca_time="1 Jul 2026 14:23:11", method="Alfano")
# → stk-report 技能将事件 + Pc 格式化为风险评级报告
```

**2. Walker 星座 + 覆盖分析**

```python
# 1. 种子卫星（需传播星历）
stk_objects(action="add_satellite", name="Seed")
stk_orbit(action="set_classical", satellite_name="Seed",
          semi_major_axis=7178137, eccentricity=0.0, inclination=53.0)
stk_orbit(action="propagate", satellite_name="Seed")
# 2. 构建 6×4 Walker Delta（24 颗卫星）
stk_objects(action="walker", name="Seed", walker_type="Delta",
            num_planes=6, num_sats_per_plane=4,
            constellation_name="MyWalker")
# 3. 定义全球覆盖网格并计算重访时间
stk_objects(action="add_coverage", coverage_name="GlobalCov",
            grid_bounds="Global", grid_resolution=6.0, fom_type="Revisit")
stk_objects(action="compute_coverage", coverage_name="GlobalCov")
stk_analysis(action="coverage", coverage_name="GlobalCov")
# → stk-report 技能将 FOM 格式化为覆盖统计报告
```

**3. 地面站访问 + AER 报告**

```python
stk_objects(action="add_facility", name="GS1",
            latitude=40.0, longitude=-105.0, altitude=1600)
stk_analysis(action="access",
             from_object="Satellite/ISS", to_object="Facility/GS1")
stk_analysis(action="aer",
             from_object="Facility/GS1", to_object="Satellite/ISS",
             max_step_size=60)
# → stk-report 技能将接触窗口 + 峰值仰角格式化为访问报告
```

### 结果报告

内置的 **`stk-report`** 技能（`.claude/skills/stk-report/`）将 STK 原始输出格式化为
结构化、带风险评级的报告。任意分析完成后，agent 生成包含以下内容的报告：

- **头部** — 场景名、时间窗口、涉及对象
- **结果表** — 按类型区分（交会事件、访问时段、AER、覆盖、轨道状态）
- **摘要** — 通俗语言解读
- **状态** — `OK` / `CAUTION` / `WARNING` / `CRITICAL`（交会风险由 Pc 和最小距离映射）
- **后续建议** — 具体的下一步工具/动作调用

交会报告示例：

```markdown
## STK Analysis Report — Conjunction Assessment

**Scenario**: ISS_CAT  **Time Window**: 1 Jul 2026 00:00 → 2 Jul 2026 00:00

### Conjunction Events
| # | TCA | Miss Distance (km) | Pc | Risk |
|---|---|---|---|---|
| 1 | 2026-07-01 14:23:11 | 3.42 | 2.1e-05 | CAUTION |

**Status**: CAUTION — Pc 超过监控阈值 (1e-05)
**Next step**: 持续监控；临近 TCA 时重算 Pc
```

### 架构设计

```
┌─────────────────────────────────────────────┐
│            MCP 客户端 (LLM Agent)            │
│                  stdio 传输                   │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│           stk-mcp Server (FastMCP)           │
│                                              │
│  ┌────────────┐  ┌───────────┐  ┌─────────┐ │
│  │stk_scenario│  │stk_objects│  │stk_orbit│ │
│  │  9 actions │  │ 13 actions│  │7 actions│ │
│  └────────────┘  └───────────┘  └─────────┘ │
│  ┌──────────────┐ ┌───────────┐ ┌──────────┐│
│  │stk_conjunct. │ │stk_analys.│ │ stk_util ││
│  │  11 actions  │ │ 10 actions│ │ 8 actions││
│  └──────────────┘ └───────────┘ └──────────┘│
│                                              │
│  ┌─────────────────────────────────────────┐ │
│  │          StkState (lifespan)            │ │
│  │  ┌──────────────┐  ┌────────────────┐  │ │
│  │  │ConnectClient │  │  COM (pywin32) │  │ │
│  │  │  TCP :5001   │  │STK11.Application│  │ │
│  │  └──────┬───────┘  └───────┬────────┘  │ │
│  └─────────┼──────────────────┼────────────┘ │
└────────────┼──────────────────┼──────────────┘
             │                  │
      ┌──────▼──────────────────▼──────┐
      │         AGI STK 11+            │
      │      (运行于本地主机)           │
      └────────────────────────────────┘
```

**双协议架构：**

- **Connect TCP**（主通道）：对象创建、轨道设置、ACAT 计算、报告查询 — 速度快，覆盖 1100+ 命令
- **COM**（辅助通道）：修复 Connect 无法设置的 `UseScenarioAnalysisTime` 属性，确保轨道传播覆盖完整场景时段

### Connect 协议参考

STK Connect 是基于 TCP 端口 5001 的文本协议：

| 操作 | 格式 |
|---|---|
| **发送命令** | `命令名 对象路径 参数\n` |
| **成功** | `ACK\n` |
| **失败** | `NAK\n` |
| **返回数据** | 40 字节头 `COMMANDNAME  NUMBYTES\n` + 数据载荷 |
| **多行数据** | 首载荷为行数，然后逐行返回 头+数据 |

完整命令参考：*STK Help → Programming → Connect Command Library*。

### 项目结构

```
stk-mcp/
├── pyproject.toml              # 包配置 (hatchling 构建)
├── install.ps1                 # 一键安装脚本 (Windows)
├── install.sh                  # 一键安装脚本 (Linux/macOS)
├── src/stk_mcp/
│   ├── app.py                  # FastMCP 实例 + 生命周期
│   ├── server.py               # 入口点，工具注册
│   ├── connect_client.py       # STK Connect TCP 协议客户端
│   ├── logic/
│   │   └── stk_state.py        # 状态管理 (Connect + COM)
│   └── tools/
│       ├── scenario.py         # stk_scenario (9 动作)
│       ├── objects.py          # stk_objects (13 动作)
│       ├── orbit.py            # stk_orbit (7 动作)
│       ├── cat.py              # stk_conjunction (11 动作)
│       ├── analysis.py         # stk_analysis (10 动作)
│       └── util.py             # stk_util (8 动作)
├── .claude/skills/             # 内置 Claude Code 技能
│   ├── stk-scenario-scaffold/  # 场景搭建流程
│   ├── stk-walker-constellation/ # Walker 星座构建
│   ├── stk-coverage-visibility/  # 覆盖与可见性分析
│   ├── stk-conjunction/        # 碰撞预警流程
│   └── stk-report/             # 分析报告格式化
└── tests/
    ├── mock_stk_server.py      # 离线测试用的模拟 STK Connect 服务器
    ├── test_connect_protocol.py # 离线协议测试（无需 STK）
    └── test_com.py             # COM 接口集成测试
```

### 已知限制

- **轨道传播窗口**：Connect 的 `Propagate` 默认只传播 TLE 历元起约 1.5 小时。COM 在 Windows 上可修复此问题。没有 COM 时轨道可能无法覆盖完整场景。
- **ACAT 数据库格式**：`Secondary AddDatabase` 仅接受 `.sd`/`.tce` 文件，不支持纯文本 TLE。TLE 编目需逐个创建卫星对象。
- **STK 必须运行中**：启动服务器前请先启动 STK，或使用 `stk_scenario(action="connect")` 重试。
- **COM 仅限 Windows**：COM (`STK11.Application`) 仅在 Windows 上可用。Connect TCP 可跨平台使用。

### 故障排查

| 现象 | 可能原因 | 解决 |
|---|---|---|
| `Not connected to STK` | STK 未运行，或 Connect Server 未启用 | 启动 STK，启用 Connect（Edit → Preferences → Connect，端口 5001），再执行 `stk_scenario(action="connect")` |
| 连接被拒 / 超时 | host/port 错误，或防火墙拦截 | 确认 `STK_PORT=5001`；远程主机需开放防火墙规则并将 `STK_HOST` 设为 STK 机器 IP |
| 工具返回 `NAK` | 对象路径无效，或命令需要已加载场景 | 检查路径为相对路径（`Satellite/ISS`，非 `*/Satellite/ISS`）；用 `stk_scenario(action="status")` 确认场景已加载 |
| 交会/访问无数据 | 轨道未传播，或时间窗口超出传播范围 | 执行 `stk_orbit(action="propagate", ...)`；确保分析时间窗口与已传播星历重叠 |
| 轨道只覆盖约 1.5 小时 | Connect 传播默认值（无 COM） | 在 Windows 上以 `[com]` 安装，`UseScenarioAnalysisTime` 会自动设置 |
| `walker` 失败 | 种子卫星无星历 | 调用 `walker` 前先传播种子卫星 |
| 服务器无法导入 | Python 版本错误 | 需 Python 3.10+（推荐 3.11）；用 `uvx --python 3.11` 避免 PATH 问题 |

如需查看原始协议交互，使用 `stk_util(action="send_command", command="...")`，
可直接读取 `ACK`/`NAK` 及数据载荷。

### 参与贡献

欢迎贡献代码。添加新的工具动作：

1. Fork 仓库并创建功能分支
2. 在 `src/stk_mcp/tools/` 下对应模块中添加 action
3. 遵循现有的 action 分发模式（`if action == "your_action":`）
4. 在运行中的 STK 实例上测试
5. 提交 Pull Request

### 许可证

[MIT](LICENSE) — 个人和商业使用自由。
