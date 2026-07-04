"""Offline protocol tests for StkConnectClient against a mock STK server.

Runs without a live STK instance. Validates the ACK/NACK handshake and
single-line data framing captured from real STK v11.6.0.

Run standalone (no pytest required):
    python tests/test_connect_protocol.py

Or under pytest if installed:
    pytest tests/test_connect_protocol.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Allow running from repo root without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from stk_mcp.connect_client import StkConnectClient  # noqa: E402
from mock_stk_server import start_mock_server  # noqa: E402


async def _with_client(coro):
    server, host, port = await start_mock_server()
    client = StkConnectClient(host, port)
    try:
        await asyncio.wait_for(client.connect(), timeout=5)
        return await coro(client)
    finally:
        await client.disconnect()
        server.close()
        await server.wait_closed()


async def _check_version(client: StkConnectClient) -> None:
    r = await asyncio.wait_for(client.send_command("GetSTKVersion /"), timeout=5)
    assert r["ack"] == "ACK", r
    assert r["raw"] == "STK v11.6.0", r


async def _check_scenario(client: StkConnectClient) -> None:
    r = await asyncio.wait_for(client.send_command("CheckScenario /"), timeout=5)
    assert r["ack"] == "ACK", r
    assert r["raw"] == "0", r


async def _check_nack(client: StkConnectClient) -> None:
    # Missing "/" scope — STK (and the mock) reject with NACK.
    r = await asyncio.wait_for(client.send_command("GetSTKVersion"), timeout=5)
    assert r["ack"] == "NAK", r
    assert r["data"] is None, r


def test_version_single_line():
    asyncio.run(_with_client(_check_version))


def test_scenario_single_line():
    asyncio.run(_with_client(_check_scenario))


def test_missing_scope_returns_nack():
    asyncio.run(_with_client(_check_nack))


if __name__ == "__main__":
    tests = [
        ("version single-line return", test_version_single_line),
        ("scenario single-line return", test_scenario_single_line),
        ("missing-scope NACK handling", test_missing_scope_returns_nack),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS: {name}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL: {name} -> {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
