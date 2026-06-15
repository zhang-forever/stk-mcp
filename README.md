# STK MCP Server

**[English](#english)** | **[中文](#中文)**

---

## English

An MCP (Model Context Protocol) server that provides AI agents with programmatic control over [AGI STK](https://www.agi.com/products/stk) (Systems Tool Kit) via the Connect TCP interface. Enables LLM-powered satellite mission analysis, conjunction assessment, and scenario automation.

### Features

- **39 MCP tools** covering the full STK Connect command library
- **Scenario management** — create, load, save, unload scenarios and set time periods
- **Object creation** — satellites, facilities, targets, sensors
- **Orbit definition** — TLE (SGP4), classical Keplerian elements, Cartesian state vectors, ephemeris files
- **Hybrid Connect + COM architecture** — uses COM (`pywin32`) to fix the `UseScenarioAnalysisTime` propagation issue that Connect alone cannot resolve
- **Conjunction Assessment (CAT/ACAT)** — basic close approach screening and advanced collision probability analysis with threat volumes
- **Access & AER analysis** — compute visibility windows and azimuth/elevation/range data
- **Report generation** — query or save STK reports (LLA state, Cartesian position, classical orbit, etc.)
- **Animation control** — start, pause, step, loop, real-time playback
- **Raw command passthrough** — send any of STK's 1100+ Connect commands directly

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

| Category | Tool | Description |
|---|---|---|
| **Connection** | `stk_connect` | Connect to STK (if not auto-connected at startup) |
| | `stk_disconnect` | Disconnect from STK |
| | `stk_status` | Check connection status and current scenario |
| **Scenario** | `stk_new_scenario` | Create a new scenario with optional time period |
| | `stk_load_scenario` | Load a `.sc` scenario file |
| | `stk_save_scenario` | Save the current scenario |
| | `stk_unload_scenario` | Close the current scenario |
| | `stk_set_time_period` | Set the analytical time window |
| **Objects** | `stk_add_satellite` | Add a satellite to the scenario |
| | `stk_add_facility` | Add a ground station with lat/lon/alt |
| | `stk_add_target` | Add a ground target |
| | `stk_add_sensor` | Attach a sensor cone to any object |
| | `stk_list_objects` | List all objects (optionally filtered by type) |
| | `stk_unload_object` | Remove an object from the scenario |
| **Orbits** | `stk_set_orbit_tle` | Set orbit from TLE (SGP4 propagator) |
| | `stk_set_orbit_classical` | Set orbit from Keplerian elements (HPOP) |
| | `stk_set_orbit_cartesian` | Set orbit from position/velocity vectors |
| | `stk_set_orbit_from_file` | Load orbit from an ephemeris file (`.e`) |
| | `stk_propagate` | Propagate orbit (with COM `UseScenarioAnalysisTime` fix) |
| **Conjunction** | `stk_cat_setup` | Configure basic CAT parameters |
| | `stk_cat_compute` | Run basic close approach computation |
| | `stk_acat_setup` | Configure Advanced CAT (time, threshold, step size) |
| | `stk_acat_add_primary` | Add primary (protected) object to ACAT |
| | `stk_acat_add_secondary` | Add secondary (threat) object to ACAT |
| | `stk_acat_add_secondary_from_database` | Bulk-load secondaries from database file |
| | `stk_acat_set_prefilters` | Set pre-computation filters (apogee/perigee, orbit path) |
| | `stk_acat_compute` | Run Advanced CAT computation |
| | `stk_acat_events` | Retrieve conjunction events (TCA, range, probability) |
| | `stk_acat_probability` | Compute Pc for a specific pair at a given TCA |
| | `stk_acat_set_threat_volume` | Configure threat volume ellipsoid dimensions |
| | `stk_conjunction_assessment` | End-to-end conjunction assessment workflow |
| **Access** | `stk_compute_access` | Compute access intervals between two objects |
| | `stk_all_access` | Compute access from one object to all others |
| | `stk_get_aer` | Get Azimuth/Elevation/Range data |
| **Reports** | `stk_get_report` | Query report data via Connect socket |
| | `stk_save_report` | Generate and save a report to file |
| | `stk_list_report_styles` | List available report styles |
| **Animation** | `stk_animate` | Control animation (start/pause/reset/step/loop) |
| | `stk_get_animation_time` | Get current animation time |
| **Raw** | `stk_send_command` | Send any raw STK Connect command |

### Architecture

```
┌─────────────────────────────────────────────┐
│            MCP Client (LLM Agent)           │
│              stdio / SSE transport           │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│             stk-mcp Server (FastMCP)         │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │ scenario │  │  orbit   │  │   cat     │ │
│  │  tools   │  │  tools   │  │  tools    │ │
│  └──────────┘  └──────────┘  └───────────┘ │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │ objects  │  │  access  │  │ reports   │ │
│  │  tools   │  │  tools   │  │  tools    │ │
│  └──────────┘  └──────────┘  └───────────┘ │
│  ┌──────────┐  ┌──────────┐                 │
│  │animation │  │   raw    │                 │
│  │  tools   │  │  tools   │                 │
│  └──────────┘  └──────────┘                 │
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
│       ├── scenario.py         # Scenario CRUD
│       ├── orbit.py            # TLE/Classical/Cartesian orbits
│       ├── objects.py          # Satellites, facilities, sensors
│       ├── cat.py              # CAT & Advanced CAT
│       ├── access.py           # Access intervals & AER
│       ├── reports.py          # STK reports
│       ├── animation.py        # Animation control
│       └── raw.py              # Raw command passthrough
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

- **39 个 MCP 工具**，覆盖 STK Connect 命令库的主要功能
- **场景管理** — 创建、加载、保存、卸载场景，设置分析时间窗口
- **对象创建** — 卫星、地面站、目标点、传感器
- **轨道定义** — TLE（SGP4 传播器）、经典轨道根数（Keplerian）、笛卡尔状态向量、星历文件
- **Connect + COM 混合架构** — 通过 COM（`pywin32`）修复 Connect 无法解决的 `UseScenarioAnalysisTime` 传播窗口问题
- **碰撞预警（CAT/ACAT）** — 基础近距离筛查和高级碰撞概率分析（含威胁体椭球配置）
- **可见性与 AER 分析** — 计算可见时间窗口和方位角/仰角/距离数据
- **报告生成** — 查询或保存 STK 报告（LLA 状态、笛卡尔坐标、经典轨道根数等）
- **动画控制** — 播放、暂停、单步、循环、实时模式
- **原始命令透传** — 直接发送 STK 的 1100+ Connect 命令中的任意一个

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

| 类别 | 工具名 | 说明 |
|---|---|---|
| **连接** | `stk_connect` | 连接 STK（启动时未自动连接时使用） |
| | `stk_disconnect` | 断开 STK 连接 |
| | `stk_status` | 检查连接状态和当前场景 |
| **场景** | `stk_new_scenario` | 创建新场景（可指定时间窗口） |
| | `stk_load_scenario` | 加载 `.sc` 场景文件 |
| | `stk_save_scenario` | 保存当前场景 |
| | `stk_unload_scenario` | 关闭当前场景 |
| | `stk_set_time_period` | 设置分析时间窗口 |
| **对象** | `stk_add_satellite` | 添加卫星 |
| | `stk_add_facility` | 添加地面站（经纬度/海拔） |
| | `stk_add_target` | 添加地面目标 |
| | `stk_add_sensor` | 为对象挂载锥形传感器 |
| | `stk_list_objects` | 列出所有对象（可按类型过滤） |
| | `stk_unload_object` | 从场景中移除对象 |
| **轨道** | `stk_set_orbit_tle` | 通过 TLE 设置轨道（SGP4 传播器） |
| | `stk_set_orbit_classical` | 通过经典轨道根数设置轨道（HPOP） |
| | `stk_set_orbit_cartesian` | 通过位置/速度向量设置轨道 |
| | `stk_set_orbit_from_file` | 从星历文件加载轨道（`.e`） |
| | `stk_propagate` | 传播轨道（含 COM `UseScenarioAnalysisTime` 修复） |
| **碰撞预警** | `stk_cat_setup` | 配置基础 CAT 参数 |
| | `stk_cat_compute` | 运行基础近距离分析 |
| | `stk_acat_setup` | 配置高级 CAT（时间、阈值、步长） |
| | `stk_acat_add_primary` | 添加主星（被保护对象） |
| | `stk_acat_add_secondary` | 添加次星（威胁对象） |
| | `stk_acat_add_secondary_from_database` | 从数据库文件批量加载次星 |
| | `stk_acat_set_prefilters` | 设置预过滤（近地点/远地点、轨道路径） |
| | `stk_acat_compute` | 运行高级 CAT 计算 |
| | `stk_acat_events` | 获取碰撞事件（TCA、距离、概率） |
| | `stk_acat_probability` | 计算指定对在给定 TCA 的碰撞概率 Pc |
| | `stk_acat_set_threat_volume` | 配置威胁体椭球尺寸 |
| | `stk_conjunction_assessment` | 端到端碰撞评估工作流 |
| **可见性** | `stk_compute_access` | 计算两个对象之间的可见时间窗口 |
| | `stk_all_access` | 计算一个对象对所有其他对象的可见性 |
| | `stk_get_aer` | 获取方位角/仰角/距离数据 |
| **报告** | `stk_get_report` | 通过 Connect 查询报告数据 |
| | `stk_save_report` | 生成并保存报告到文件 |
| | `stk_list_report_styles` | 列出可用报告样式 |
| **动画** | `stk_animate` | 控制动画（播放/暂停/重置/单步/循环） |
| | `stk_get_animation_time` | 获取当前动画时间 |
| **原始命令** | `stk_send_command` | 发送任意 STK Connect 原始命令 |

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
