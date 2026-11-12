# STK MCP Server — Agent Guide

MCP server that lets an AI agent control AGI STK through the Connect TCP
interface. See `README.md` for installation, client configuration, and the full
tool/action reference.

## Skills

Agent-agnostic workflow guides live in `skills/`. Each folder contains a
`SKILL.md` with YAML frontmatter (`name`, `description`). Read the matching file
before running a multi-step STK workflow.

| Skill | Use for |
|---|---|
| `skills/stk-scenario-scaffold/` | Create/load a scenario, set the time window, animation |
| `skills/stk-orbit-setup/` | TLE, Keplerian, Cartesian, ephemeris, propagation, position, lifetime |
| `skills/stk-object-management/` | Satellites, facilities, targets, sensors, constellations, chains |
| `skills/stk-walker-constellation/` | Walker Delta/Star constellation builds |
| `skills/stk-coverage-visibility/` | Coverage definitions, revisit/N-asset FOM, access windows |
| `skills/stk-access-rf-analysis/` | Access, AER, visibility, chain, comm link, sensor FOV, radar |
| `skills/stk-conjunction/` | CAT / Advanced CAT close approaches and collision probability |
| `skills/stk-util-operations/` | Reports, report styles, conversions, raw Connect commands |
| `skills/stk-report/` | Format analysis output into a risk-rated report |

Claude Code auto-discovers skills only under `.claude/skills/`. To enable that
locally without making `.claude/` the source of truth:

```bash
mkdir -p .claude && cp -r skills .claude/skills
```

Codex and other agents can read `skills/*/SKILL.md` directly.

## Development

```bash
# Windows
powershell -ExecutionPolicy Bypass -File scripts/install.ps1

# Linux / macOS
./scripts/install.sh

# Tests (offline, no STK required)
uv run --extra dev pytest

# Start the server
uv run stk-mcp
```

The server speaks stdio and expects STK Connect on `localhost:5001` by default
(`STK_HOST`, `STK_PORT`). Without a running STK instance the tools return
actionable connection errors; the server itself still starts.
