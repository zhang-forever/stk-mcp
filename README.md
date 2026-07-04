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

- **6 domain tools, 55 actions** — clean, action-based API designed for LLM consumption
- **Scenario lifecycle** — create, load, save, configure time windows, animate
- **Object management** — satellites, ground stations, sensors, constellations, aircraft, comm chains
- **Orbit definition** — TLE (SGP4), Keplerian elements, Cartesian vectors, ephemeris files, position queries, lifetime estimation
- **Conjunction assessment** — CAT close-approach screening + ACAT advanced collision probability (Pc) analysis
- **Analysis suite** — access/visibility windows, AER data, coverage footprints, comm link budgets, sensor FOV, radar cross-section, lighting conditions
- **Hybrid Connect + COM** — COM fallback (`pywin32`) fixes the `UseScenarioAnalysisTime` propagation limitation
- **Raw command passthrough** — send any of STK's 1100+ Connect commands directly

### Quick Start

```bash
# 1. Clone and install
git clone https://github.com/zhang-forever/stk-mcp.git
cd stk-mcp
pip install -e ".[com]"    # COM support included (recommended)

# 2. Make sure STK is running with Connect enabled (port 5001)

# 3. Start the server
stk-mcp
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
> scaffold). Open the project in Claude Code and they load automatically.

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

| Tool | Actions | Description |
|---|---|---|
| **`stk_scenario`** | `connect`, `disconnect`, `status`, `new`, `load`, `save`, `unload`, `set_time_period`, `animate` | Scenario lifecycle and time management |
| **`stk_objects`** | `add_satellite`, `add_facility`, `add_target`, `add_sensor`, `add_constellation`, `add_chain`, `add_aircraft`, `list`, `remove`, `get_info` | Create and manage scene objects |
| **`stk_orbit`** | `set_tle`, `set_classical`, `set_cartesian`, `from_file`, `propagate`, `position`, `lifetime` | Orbit definition, propagation, and queries |
| **`stk_conjunction`** | `cat_setup`, `cat_compute`, `acat_setup`, `acat_add_primary`, `acat_add_secondary`, `acat_set_prefilters`, `acat_set_threat_volume`, `acat_compute`, `acat_events`, `acat_probability`, `assess` | Collision warning (CAT + ACAT) |
| **`stk_analysis`** | `access`, `all_access`, `aer`, `chain_access`, `chain_intervals`, `coverage`, `comm_link`, `sensor_fov`, `visibility`, `radar` | Visibility, coverage, and RF analysis |
| **`stk_util`** | `report`, `save_report`, `list_report_styles`, `convert_coord`, `convert_date`, `convert_unit`, `get_animation_time`, `send_command` | Reports, conversions, raw commands |

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
│  │ 9 actions  │  │ 10 actions│  │7 actions│ │
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
├── src/stk_mcp/
│   ├── app.py                  # FastMCP instance + lifespan
│   ├── server.py               # Entry point, tool registration
│   ├── connect_client.py       # STK Connect TCP protocol client
│   ├── logic/
│   │   └── stk_state.py        # State management (Connect + COM)
│   └── tools/
│       ├── scenario.py         # stk_scenario (9 actions)
│       ├── objects.py          # stk_objects (10 actions)
│       ├── orbit.py            # stk_orbit (7 actions)
│       ├── cat.py              # stk_conjunction (11 actions)
│       ├── analysis.py         # stk_analysis (10 actions)
│       └── util.py             # stk_util (8 actions)
├── skill/
│   └── SKILL.md                # QoderWork skill definition
└── test_com.py                 # COM interface integration test
```

### Known Limitations

- **Orbit propagation window**: Connect's `Propagate` defaults to ~1.5 hours from TLE epoch. COM fixes this on Windows. Without COM (e.g. Linux), orbits may not cover the full scenario period.
- **ACAT database format**: `Secondary AddDatabase` only accepts `.sd`/`.tce` files, not plain-text TLE. For TLE catalogs, create satellite objects individually.
- **STK must be running**: Start STK before launching the server, or use `stk_scenario(action="connect")` to retry.
- **Windows-only COM**: COM (`STK11.Application`) requires Windows. Connect TCP works cross-platform.

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

- **6 个领域工具，55 个动作** — 为 LLM 设计的简洁 action 分发接口
- **场景生命周期** — 创建、加载、保存、配置时间窗口、动画控制
- **对象管理** — 卫星、地面站、传感器、星座、飞行器、通信链
- **轨道定义** — TLE (SGP4)、经典轨道根数、笛卡尔向量、星历文件、位置查询、寿命估算
- **碰撞预警** — CAT 近距离筛查 + ACAT 高级碰撞概率 (Pc) 分析
- **分析套件** — 可见性窗口、AER 数据、覆盖足迹、通信链路预算、传感器视场、雷达截面、光照条件
- **Connect + COM 混合架构** — COM 辅助 (`pywin32`) 修复 `UseScenarioAnalysisTime` 传播窗口限制
- **原始命令透传** — 直接发送 STK 的 1100+ Connect 命令

### 快速开始

```bash
# 1. 克隆并安装
git clone https://github.com/zhang-forever/stk-mcp.git
cd stk-mcp
pip install -e ".[com]"    # 包含 COM 支持（推荐）

# 2. 确保 STK 已启动且 Connect 已启用（端口 5001）

# 3. 启动服务器
stk-mcp
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

| 工具 | Actions | 说明 |
|---|---|---|
| **`stk_scenario`** | `connect`, `disconnect`, `status`, `new`, `load`, `save`, `unload`, `set_time_period`, `animate` | 场景生命周期与时间管理 |
| **`stk_objects`** | `add_satellite`, `add_facility`, `add_target`, `add_sensor`, `add_constellation`, `add_chain`, `add_aircraft`, `list`, `remove`, `get_info` | 对象创建与管理 |
| **`stk_orbit`** | `set_tle`, `set_classical`, `set_cartesian`, `from_file`, `propagate`, `position`, `lifetime` | 轨道定义、传播与查询 |
| **`stk_conjunction`** | `cat_setup`, `cat_compute`, `acat_setup`, `acat_add_primary`, `acat_add_secondary`, `acat_set_prefilters`, `acat_set_threat_volume`, `acat_compute`, `acat_events`, `acat_probability`, `assess` | 碰撞预警 (CAT + ACAT) |
| **`stk_analysis`** | `access`, `all_access`, `aer`, `chain_access`, `chain_intervals`, `coverage`, `comm_link`, `sensor_fov`, `visibility`, `radar` | 可见性、覆盖与射频分析 |
| **`stk_util`** | `report`, `save_report`, `list_report_styles`, `convert_coord`, `convert_date`, `convert_unit`, `get_animation_time`, `send_command` | 报告、转换与原始命令 |

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
│  │  9 actions │  │ 10 actions│  │7 actions│ │
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
├── src/stk_mcp/
│   ├── app.py                  # FastMCP 实例 + 生命周期
│   ├── server.py               # 入口点，工具注册
│   ├── connect_client.py       # STK Connect TCP 协议客户端
│   ├── logic/
│   │   └── stk_state.py        # 状态管理 (Connect + COM)
│   └── tools/
│       ├── scenario.py         # stk_scenario (9 动作)
│       ├── objects.py          # stk_objects (10 动作)
│       ├── orbit.py            # stk_orbit (7 动作)
│       ├── cat.py              # stk_conjunction (11 动作)
│       ├── analysis.py         # stk_analysis (10 动作)
│       └── util.py             # stk_util (8 动作)
├── skill/
│   └── SKILL.md                # QoderWork 技能定义
└── test_com.py                 # COM 接口集成测试
```

### 已知限制

- **轨道传播窗口**：Connect 的 `Propagate` 默认只传播 TLE 历元起约 1.5 小时。COM 在 Windows 上可修复此问题。没有 COM 时轨道可能无法覆盖完整场景。
- **ACAT 数据库格式**：`Secondary AddDatabase` 仅接受 `.sd`/`.tce` 文件，不支持纯文本 TLE。TLE 编目需逐个创建卫星对象。
- **STK 必须运行中**：启动服务器前请先启动 STK，或使用 `stk_scenario(action="connect")` 重试。
- **COM 仅限 Windows**：COM (`STK11.Application`) 仅在 Windows 上可用。Connect TCP 可跨平台使用。

### 参与贡献

欢迎贡献代码。添加新的工具动作：

1. Fork 仓库并创建功能分支
2. 在 `src/stk_mcp/tools/` 下对应模块中添加 action
3. 遵循现有的 action 分发模式（`if action == "your_action":`）
4. 在运行中的 STK 实例上测试
5. 提交 Pull Request

### 许可证

[MIT](LICENSE) — 个人和商业使用自由。
