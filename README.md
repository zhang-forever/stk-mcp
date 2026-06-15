# STK MCP Server

**[English](#english)** | **[中文](#中文)**

---

## English

An MCP (Model Context Protocol) server that provides AI agents with programmatic control over [AGI STK](https://www.agi.com/products/stk) (Systems Tool Kit) via the Connect TCP interface. Enables LLM-powered satellite mission analysis, conjunction assessment, and scenario automation.

### Features

- **6 consolidated domain tools** with action-based dispatch — clean API for LLM agents
- **Scenario management** — connect, create, load, save, unload scenarios, set time periods, animation control
- **Object creation** — satellites, facilities, targets, sensors, constellations, chains, aircraft; object info queries
- **Orbit definition** — TLE (SGP4), classical Keplerian, Cartesian, ephemeris files; position queries; orbit lifetime estimation
- **Hybrid Connect + COM architecture** — uses COM (`pywin32`) to fix the `UseScenarioAnalysisTime` propagation issue
- **Conjunction Assessment (CAT/ACAT)** — basic close approach screening and advanced collision probability (Pc) analysis
- **Analysis suite** — access/visibility, coverage, communication chains, sensor FOV, radar, lighting conditions
- **Utilities** — reports, coordinate/date/unit conversion, raw Connect command passthrough (1100+ commands)

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| **AGI STK** | 11+ | With Connect module enabled (Edit → Preferences → Connect, port 5001) |
| **Python** | 3.10+ | 3.11 recommended |
| **pywin32** | latest | Optional — enables COM-backed propagation fix |

### Installation

```bash
git clone https://github.com/zhang-forever/stk-mcp.git
cd stk-mcp
pip install -e .

# With COM support (recommended on Windows, fixes orbit propagation):
pip install -e ".[com]"
```

### STK Setup Guide

Before using this MCP server, STK must be configured to accept Connect commands:

**1. Enable the Connect module in STK:**

Open STK → **Edit** → **Preferences** → **Connect** (under Modules). Check **Enable Connect Server** and set the port to `5001` (default). Click OK.

**2. Verify Connect is listening:**

After enabling, STK should show a small green indicator in the status bar. You can verify with a simple TCP test:

```bash
# On the same machine as STK:
echo "GetSTKVersion" | nc localhost 5001
# Should return something like: "STK 11.7.1"
```

**3. Firewall (if connecting remotely):**

If the MCP server runs on a different machine, allow inbound TCP on port 5001:

```powershell
# Windows Firewall (run as Administrator):
netsh advfirewall firewall add rule name="STK Connect" dir=in action=allow protocol=TCP localport=5001
```

**4. COM support (Windows only, recommended):**

The Connect `Propagate` command has a known limitation: orbits only propagate ~1.5 hours from the TLE epoch by default (`UseScenarioAnalysisTime=False`). This server uses STK's COM interface (`pywin32`) to set `UseScenarioAnalysisTime=True` before propagation, ensuring orbits cover the full scenario time period.

To enable COM:
```bash
pip install pywin32
```

STK must be **running** for COM to attach. The server auto-detects STK via `GetActiveObject("STK11.Application")`. Without COM, orbit propagation is limited to ~1.5 hours — conjunction assessment and access analysis may return incomplete results.

### Configuration

The server connects to STK via TCP on startup. Configure with environment variables:

| Variable | Default | Description |
|---|---|---|
| `STK_HOST` | `localhost` | STK host address (use IP if remote) |
| `STK_PORT` | `5001` | STK Connect TCP port |

### Usage

**As a standalone MCP server (stdio transport):**

```bash
stk-mcp
```

**Configure in your MCP client** (e.g. Claude Desktop, QoderWork, Cursor):

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

**With environment overrides:**

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

### Tool Reference

| Tool | Actions | Description |
|---|---|---|
| **`stk_scenario`** | `connect`, `disconnect`, `status`, `new`, `load`, `save`, `unload`, `set_time_period`, `animate` | Scenario lifecycle management |
| **`stk_objects`** | `add_satellite`, `add_facility`, `add_target`, `add_sensor`, `add_constellation`, `add_chain`, `add_aircraft`, `list`, `remove`, `get_info` | Object creation and management |
| **`stk_orbit`** | `set_tle`, `set_classical`, `set_cartesian`, `from_file`, `propagate`, `position`, `lifetime` | Orbit definition, propagation, queries |
| **`stk_conjunction`** | `cat_setup`, `cat_compute`, `acat_setup`, `acat_add_primary`, `acat_add_secondary`, `acat_set_prefilters`, `acat_set_threat_volume`, `acat_compute`, `acat_events`, `acat_probability`, `assess` | Collision warning (CAT + ACAT) |
| **`stk_analysis`** | `access`, `all_access`, `aer`, `chain_access`, `chain_intervals`, `coverage`, `comm_link`, `sensor_fov`, `visibility`, `radar` | Visibility, coverage, chain, RF analysis |
| **`stk_util`** | `report`, `save_report`, `list_report_styles`, `convert_coord`, `convert_date`, `convert_unit`, `get_animation_time`, `send_command` | Reports, conversion, raw commands |

**Example usage:**
```
stk_scenario(action="new", name="MyScene", start_time="11 Jun 2026 00:00:00", stop_time="+7days")
stk_objects(action="add_satellite", name="ISS")
stk_orbit(action="set_tle", satellite_name="ISS", tle_line1="1 25544U ...", tle_line2="2 25544 ...")
stk_orbit(action="position", satellite_name="ISS", time="14 Jun 2026 12:00:00")
stk_conjunction(action="assess", primary_satellite="ISS", secondary_satellite="Debris1", ...)
stk_analysis(action="access", from_object="Satellite/ISS", to_object="Facility/GroundStation")
stk_util(action="convert_coord", from_coord="ICRF", to_coord="Fixed", coord_values="6778000,0,0")
stk_util(action="send_command", command="New / */Constellation MyConstellation")
```

### Architecture

```
┌─────────────────────────────────────────────┐
│            MCP Client (LLM Agent)           │
│              stdio / SSE transport           │
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
│  │        StkState (lifespan)              │ │
│  │  ┌──────────────┐  ┌────────────────┐  │ │
│  │  │ConnectClient │  │  COM (pywin32) │  │ │
│  │  │  TCP :5001   │  │ STK11.Application│ │ │
│  │  └──────┬───────┘  └───────┬────────┘  │ │
│  └─────────┼──────────────────┼────────────┘ │
└────────────┼──────────────────┼──────────────┘
             │                  │
      ┌──────▼──────────────────▼──────┐
      │         AGI STK 11+            │
      │    (running on localhost)       │
      └────────────────────────────────┘
```

The server uses a **dual-protocol** approach:

- **Connect TCP** (primary): Object creation, orbit setting, ACAT computation, reports — fast and covers 1100+ commands
- **COM** (supplementary): Fixes the critical `UseScenarioAnalysisTime` property that Connect cannot set, ensuring orbit propagation covers the full scenario time period

### Known Limitations

1. **`UseScenarioAnalysisTime`**: The Connect `Propagate` command defaults to a ~1.5-hour window from TLE epoch. The server uses COM to set `UseScenarioAnalysisTime=True` before propagation. Without COM (e.g. on Linux or without pywin32), orbits may not cover the full scenario period.

2. **ACAT database loading**: `Secondary AddDatabase` only accepts STK proprietary formats (`.sd`, `.tce`), not plain-text TLE files. For TLE catalogs, create satellite objects individually via `stk_add_satellite` + `stk_set_orbit_tle`.

3. **STK must be running**: The server connects to a running STK instance. Start STK before launching the MCP server, or use `stk_connect` to retry.

4. **Windows-only COM**: The COM interface (`STK11.Application`) is only available on Windows with STK installed. Connect TCP works cross-platform if STK is reachable over the network.

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
└── test_com.py                 # COM interface integration test
```

### Connect Protocol

STK Connect is a text-based TCP protocol on port 5001:

- **Send**: `CommandName ObjectPath Options\n`
- **Response**: `ACK\n` (success) or `NAK\n` (failure)
- **Return data**: 40-byte header `COMMANDNAME  NUMBYTES\n` followed by data payload
- **Multi-line**: First payload is row count, then repeated header+data per row

See *STK Help → Programming → Connect Command Library* for the full command reference.

### License

MIT

---

## 中文

基于 MCP (Model Context Protocol) 的 STK 控制服务器，通过 Connect TCP 接口让 AI Agent 能够程序化控制 [AGI STK](https://www.agi.com/products/stk)（Systems Tool Kit），实现 LLM 驱动的卫星任务分析、碰撞预警和场景自动化。

### 功能特性

- **6 个领域工具**，基于 action 参数分发 — 简洁的 LLM Agent 调用接口
- **场景管理** — 连接、创建、加载、保存、卸载场景，设置时间窗口，动画控制
- **对象创建** — 卫星、地面站、目标点、传感器、星座、通信链、飞行器；对象属性查询
- **轨道定义** — TLE（SGP4）、经典轨道根数、笛卡尔状态向量、星历文件；位置查询；轨道寿命估算
- **Connect + COM 混合架构** — 通过 COM（`pywin32`）修复 `UseScenarioAnalysisTime` 传播窗口问题
- **碰撞预警（CAT/ACAT）** — 基础近距离筛查和高级碰撞概率（Pc）分析
- **分析套件** — 可见性、覆盖分析、通信链、传感器视场、雷达、光照条件
- **工具集** — 报告生成、坐标/时间/单位转换、原始 Connect 命令透传（1100+ 命令）

### 环境要求

| 依赖 | 版本 | 说明 |
|---|---|---|
| **AGI STK** | 11+ | 需启用 Connect 模块（Edit → Preferences → Connect，端口 5001） |
| **Python** | 3.10+ | 推荐 3.11 |
| **pywin32** | 最新 | 可选 — 启用 COM 传播修复（仅 Windows） |

### 安装

```bash
git clone https://github.com/zhang-forever/stk-mcp.git
cd stk-mcp
pip install -e .

# 启用 COM 支持（推荐，修复轨道传播窗口问题）：
pip install -e ".[com]"
```

### STK 配置指南

在使用本 MCP 服务器之前，需要在 STK 中启用 Connect 模块：

**1. 启用 Connect 模块：**

打开 STK → **Edit** → **Preferences** → **Connect**（在 Modules 下）。勾选 **Enable Connect Server**，端口设为 `5001`（默认值）。点击 OK。

**2. 验证 Connect 是否正常监听：**

启用后，STK 状态栏应出现绿色连接指示器。可用简单的 TCP 测试验证：

```bash
# 在 STK 所在机器上执行：
echo "GetSTKVersion" | nc localhost 5001
# 应返回类似：STK 11.7.1
```

**3. 防火墙设置（远程连接时）：**

如果 MCP 服务器运行在与 STK 不同的机器上，需开放 TCP 5001 端口：

```powershell
# Windows 防火墙（以管理员身份运行）：
netsh advfirewall firewall add rule name="STK Connect" dir=in action=allow protocol=TCP localport=5001
```

**4. COM 支持（仅 Windows，推荐）：**

Connect 的 `Propagate` 命令有一个已知限制：默认只传播 TLE 历元起约 1.5 小时（`UseScenarioAnalysisTime=False`）。本服务器通过 STK 的 COM 接口（`pywin32`）在传播前设置 `UseScenarioAnalysisTime=True`，确保轨道覆盖完整场景时段。

启用 COM：
```bash
pip install pywin32
```

STK 必须处于**运行状态**才能挂载 COM。服务器通过 `GetActiveObject("STK11.Application")` 自动检测。没有 COM 时，轨道传播仅限约 1.5 小时——碰撞预警和可见性分析可能返回不完整的结果。

### 配置

服务器启动时通过 TCP 连接 STK，可通过环境变量配置：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `STK_HOST` | `localhost` | STK 主机地址（远程时填 IP） |
| `STK_PORT` | `5001` | STK Connect TCP 端口 |

### 使用方法

**作为独立 MCP 服务器运行（stdio 传输）：**

```bash
stk-mcp
```

**在 MCP 客户端中配置**（如 Claude Desktop、QoderWork、Cursor）：

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

**自定义环境变量：**

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

### 工具列表

| 工具 | Actions | 说明 |
|---|---|---|
| **`stk_scenario`** | `connect`, `disconnect`, `status`, `new`, `load`, `save`, `unload`, `set_time_period`, `animate` | 场景生命周期管理 |
| **`stk_objects`** | `add_satellite`, `add_facility`, `add_target`, `add_sensor`, `add_constellation`, `add_chain`, `add_aircraft`, `list`, `remove`, `get_info` | 对象创建与管理 |
| **`stk_orbit`** | `set_tle`, `set_classical`, `set_cartesian`, `from_file`, `propagate`, `position`, `lifetime` | 轨道定义、传播、查询 |
| **`stk_conjunction`** | `cat_setup`, `cat_compute`, `acat_setup`, `acat_add_primary`, `acat_add_secondary`, `acat_set_prefilters`, `acat_set_threat_volume`, `acat_compute`, `acat_events`, `acat_probability`, `assess` | 碰撞预警 (CAT + ACAT) |
| **`stk_analysis`** | `access`, `all_access`, `aer`, `chain_access`, `chain_intervals`, `coverage`, `comm_link`, `sensor_fov`, `visibility`, `radar` | 可见性、覆盖、链路、射频分析 |
| **`stk_util`** | `report`, `save_report`, `list_report_styles`, `convert_coord`, `convert_date`, `convert_unit`, `get_animation_time`, `send_command` | 报告、转换、原始命令 |

**调用示例：**
```
stk_scenario(action="new", name="CAT_Scene", start_time="11 Jun 2026 00:00:00", stop_time="+7days")
stk_objects(action="add_satellite", name="Primary")
stk_orbit(action="set_tle", satellite_name="Primary", tle_line1="1 55107U ...", tle_line2="2 55107 ...")
stk_orbit(action="position", satellite_name="Primary", time="14 Jun 2026 12:00:00")
stk_conjunction(action="assess", primary_satellite="Primary", secondary_satellite="Debris1", ...)
stk_analysis(action="access", from_object="Satellite/Primary", to_object="Facility/GS1")
stk_util(action="convert_coord", from_coord="ICRF", to_coord="Fixed", coord_values="6778000,0,0")
stk_util(action="send_command", command="New / */Constellation MyConstellation")
```

### 架构设计

服务器采用**双协议**架构：

- **Connect TCP**（主通道）：对象创建、轨道设置、ACAT 计算、报告查询 — 速度快，覆盖 1100+ 命令
- **COM**（辅助通道）：修复 Connect 无法设置的 `UseScenarioAnalysisTime` 属性，确保轨道传播覆盖完整场景时段

### 已知限制

1. **`UseScenarioAnalysisTime`**：Connect 的 `Propagate` 命令默认只传播 TLE 历元起约 1.5 小时。服务器通过 COM 在传播前设置 `UseScenarioAnalysisTime=True`。没有 COM 时（如 Linux 或未安装 pywin32），轨道可能无法覆盖完整场景。

2. **ACAT 数据库加载**：`Secondary AddDatabase` 仅接受 STK 专有格式（`.sd`、`.tce`），不支持纯文本 TLE 文件。TLE 编目数据需通过 `stk_add_satellite` + `stk_set_orbit_tle` 逐个创建。

3. **STK 必须运行中**：服务器连接到正在运行的 STK 实例。启动 MCP 服务器前请先启动 STK，或使用 `stk_connect` 重试连接。

4. **COM 仅限 Windows**：COM 接口（`STK11.Application`）仅在 Windows 上可用。Connect TCP 可跨平台使用（只要网络可达 STK）。

### Connect 协议

STK Connect 是基于 TCP 端口 5001 的文本协议：

- **发送**：`命令名 对象路径 参数\n`
- **响应**：`ACK\n`（成功）或 `NAK\n`（失败）
- **返回数据**：40 字节头 `COMMANDNAME  NUMBYTES\n` + 数据载荷
- **多行数据**：首个载荷为行数，然后逐行返回 头+数据

完整命令参考见 *STK Help → Programming → Connect Command Library*。

### 许可证

MIT
