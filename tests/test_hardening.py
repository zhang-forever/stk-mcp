"""Regression tests for input validation and checked command dispatch."""

import asyncio
from types import SimpleNamespace

import pytest

from stk_mcp.app import _env_int
from stk_mcp.connect_client import StkConnectClient
from stk_mcp.tools._common import StkCommandError, send_checked
from stk_mcp.tools.objects import stk_objects


class FakeClient:
    def __init__(self, ack="ACK"):
        self.ack = ack
        self.commands = []

    async def send_command(self, command):
        self.commands.append(command)
        return {"ack": self.ack, "data": None, "raw": ""}


def context(client):
    return SimpleNamespace(
        request_context=SimpleNamespace(
            lifespan_context=SimpleNamespace(client=client)
        )
    )


@pytest.mark.asyncio
async def test_send_checked_returns_ack_result():
    result = await send_checked(FakeClient(), "New / */Satellite Test")
    assert result["ack"] == "ACK"


@pytest.mark.asyncio
async def test_send_checked_raises_on_nak():
    with pytest.raises(StkCommandError):
        await send_checked(FakeClient(ack="NAK"), "New / */Satellite Test")


@pytest.mark.asyncio
async def test_send_command_rejects_newlines():
    client = StkConnectClient()
    with pytest.raises(ValueError, match="single line"):
        await client.send_command("New / */Satellite A\nQuit")


@pytest.mark.asyncio
async def test_read_ack_parses_fragmented_reply():
    reader = asyncio.StreamReader()
    reader.feed_data(b"A")
    await asyncio.sleep(0)
    reader.feed_data(b"CK")
    client = StkConnectClient()
    client._reader = reader
    assert await client._read_ack(timeout=1.0) == "ACK"


@pytest.mark.asyncio
async def test_read_ack_normalizes_nack():
    reader = asyncio.StreamReader()
    reader.feed_data(b"NACK")
    client = StkConnectClient()
    client._reader = reader
    assert await client._read_ack(timeout=1.0) == "NAK"


def test_env_int_falls_back(monkeypatch):
    monkeypatch.setenv("STK_TEST_PORT", "not-a-number")
    assert _env_int("STK_TEST_PORT", 5001) == 5001
    monkeypatch.setenv("STK_TEST_PORT", "70000")
    assert _env_int("STK_TEST_PORT", 5001) == 5001
    monkeypatch.setenv("STK_TEST_PORT", "5002")
    assert _env_int("STK_TEST_PORT", 5001) == 5002


class PositionFailingClient:
    async def send_command(self, command):
        if command.startswith("SetPosition"):
            return {"ack": "NAK", "data": None, "raw": ""}
        return {"ack": "ACK", "data": None, "raw": ""}


@pytest.mark.asyncio
async def test_add_facility_reports_position_failure():
    result = await stk_objects(
        context(PositionFailingClient()),
        "add_facility",
        name="GS1",
        latitude=0.0,
        longitude=0.0,
        altitude=0.0,
    )
    assert "position was not set" in result
