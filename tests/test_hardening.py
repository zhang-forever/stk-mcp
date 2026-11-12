"""Regression tests for input validation and checked command dispatch."""

import asyncio
from types import SimpleNamespace

import pytest

from stk_mcp.app import _env_int
from stk_mcp.connect_client import StkConnectClient
from stk_mcp.tools._common import StkCommandError, send_checked
from stk_mcp.tools.objects import stk_objects
from stk_mcp.tools.util import stk_util
from stk_mcp.validation import CommandValidationError, validate_command


class FakeClient:
    def __init__(self, ack="ACK"):
        self.ack = ack
        self.commands = []

    async def send_command(self, command):
        self.commands.append(command)
        return {"ack": self.ack, "data": None, "raw": ""}


def context(client):
    return SimpleNamespace(
        request_context=SimpleNamespace(lifespan_context=SimpleNamespace(client=client))
    )


@pytest.mark.asyncio
async def test_send_checked_returns_ack_result():
    result = await send_checked(FakeClient(), "New / */Satellite Test")
    assert result["ack"] == "ACK"


@pytest.mark.asyncio
async def test_send_checked_raises_on_nak():
    with pytest.raises(StkCommandError):
        await send_checked(FakeClient(ack="NAK"), "New / */Satellite Test")


def test_validate_command_rejects_newlines():
    with pytest.raises(CommandValidationError):
        validate_command("New / */Satellite A\nQuit")


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


class UnitClient:
    def __init__(self, data="1000"):
        self.commands = []
        self.data = data

    async def send_command(self, command):
        self.commands.append(command)
        return {"ack": "ACK", "data": [self.data], "raw": self.data}


@pytest.mark.asyncio
async def test_convert_unit_uses_units_convert():
    client = UnitClient()
    result = await stk_util(context(client), "convert_unit", from_unit="km", to_unit="m", value=1.0)
    assert client.commands[-1] == 'Units_Convert * Unit Distance "km" "m" "1.0"'
    assert "1000" in result


@pytest.mark.asyncio
async def test_convert_unit_rejects_mixed_dimensions():
    client = UnitClient()
    result = await stk_util(
        context(client), "convert_unit", from_unit="km", to_unit="sec", value=1.0
    )
    assert "different dimensions" in result
    assert client.commands == []


@pytest.mark.asyncio
async def test_convert_unit_falls_back_for_unknown_units():
    client = UnitClient()
    await stk_util(context(client), "convert_unit", from_unit="smoot", to_unit="m", value=1.0)
    assert client.commands[-1] == "ConvertUnit smoot m 1.0"


@pytest.mark.asyncio
async def test_convert_unit_uses_doppler_velocity_dimension():
    client = UnitClient()
    await stk_util(context(client), "convert_unit", from_unit="m/s", to_unit="mph", value=1.0)
    assert client.commands[-1] == 'Units_Convert * Unit DopplerVelocity "m/s" "mph" "1.0"'


@pytest.mark.asyncio
async def test_convert_unit_canonicalizes_temperature_aliases():
    client = UnitClient()
    await stk_util(context(client), "convert_unit", from_unit="c", to_unit="f", value=0.0)
    assert client.commands[-1] == 'Units_Convert * Unit Temperature "degC" "degF" "0.0"'
