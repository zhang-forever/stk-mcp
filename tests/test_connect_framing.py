"""Offline regression tests for fragmented and failed Connect responses."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mock_stk_server import _make_single_line, start_mock_server
from stk_mcp.connect_client import StkConnectClient


def _client():
    client = StkConnectClient()
    client._reader = asyncio.StreamReader()
    client._writer = Mock()
    client._writer.drain = AsyncMock()
    client._connected = True
    return client


async def _feed(reader, payload, *, eof=False):
    # A byte at a time, on separate event-loop turns: read(n) may return
    # fewer bytes than requested even though the peer is still connected.
    for byte in payload:
        reader.feed_data(bytes([byte]))
        await asyncio.sleep(0.001)
    if eof:
        reader.feed_eof()


def _frame(command, payload):
    return _make_single_line(command, payload)[3:]


@pytest.mark.asyncio
async def test_fragmented_ack_header_payload_and_consecutive_nack():
    client = _client()
    reader = client._reader
    payload = (
        _make_single_line("GETSTKVERSION", "STK v11.6.0")
        + b"NACK"
        + _make_single_line("CHECKSCENARIO", "0")
    )
    feeder = asyncio.create_task(_feed(reader, payload))
    try:
        result = await client.send_command("GetSTKVersion /", timeout=1)
        assert result["raw"] == "STK v11.6.0"
        assert (await client.send_command("GetSTKVersion", timeout=1))["ack"] == "NAK"
        assert (await client.send_command("CheckScenario /", timeout=1))["raw"] == "0"
        assert client.connected
    finally:
        await feeder
        client._abort_connection()


@pytest.mark.asyncio
async def test_fragmented_multiline_response():
    client = _client()
    payload = b"ACK" + _frame("ACATEVENTS_RM", "2")
    payload += _frame("ACATEVENTS_RM", "first") + _frame("ACATEVENTS_RM", "second")
    feeder = asyncio.create_task(_feed(client._reader, payload))
    try:
        result = await client.send_command("ACATEvents_RM */AdvCAT/Test", timeout=1)
        assert result["data"] == ["first", "second"]
    finally:
        await feeder
        client._abort_connection()


@pytest.mark.parametrize("payload,command", [
    (b"BAD", "New / */Satellite Test"),
    (b"ABC", "New / */Satellite Test"),
    (b"NOPE", "New / */Satellite Test"),
    (b"ACK" + b"GETSTKVERSION".ljust(40), "GetSTKVersion /"),
    (b"ACK" + b"GETSTKVERSION invalid".ljust(40), "GetSTKVersion /"),
    (b"ACK" + b"GETSTKVERSION -1".ljust(40), "GetSTKVersion /"),
    (b"ACK" + _frame("ACATEVENTS_RM", "bad"), "ACATEvents_RM */AdvCAT/Test"),
    (b"ACK" + _frame("ACATEVENTS_RM", "-1"), "ACATEvents_RM */AdvCAT/Test"),
])
@pytest.mark.asyncio
async def test_malformed_response_invalidates_connection(payload, command):
    client = _client()
    writer = client._writer
    client._reader.feed_data(payload)
    with pytest.raises(ValueError):
        await client.send_command(command, timeout=1)
    assert not client.connected
    writer.close.assert_called_once()
    with pytest.raises(ConnectionError, match="Not connected"):
        await client.send_command("CheckScenario /")


@pytest.mark.parametrize("payload", [b"", b"A", b"AC", b"N", b"NAC", b"ACKshort", _make_single_line("GETSTKVERSION", "version")[:-1]])
@pytest.mark.asyncio
async def test_eof_invalidates_connection(payload):
    client = _client()
    writer = client._writer
    client._reader.feed_data(payload)
    client._reader.feed_eof()
    with pytest.raises(asyncio.IncompleteReadError):
        await client.send_command("GetSTKVersion /", timeout=1)
    assert not client.connected
    writer.close.assert_called_once()


@pytest.mark.parametrize("payload", [b"", b"A", b"NAC", b"ACKshort", _make_single_line("GETSTKVERSION", "version")[:-1]])
@pytest.mark.asyncio
async def test_timeout_invalidates_connection(payload):
    client = _client()
    writer = client._writer
    client._reader.feed_data(payload)
    with pytest.raises(asyncio.TimeoutError):
        await client.send_command("GetSTKVersion /", timeout=0.01)
    assert not client.connected
    writer.close.assert_called_once()


@pytest.mark.asyncio
async def test_cancelled_command_invalidates_connection():
    client = _client()
    writer = client._writer
    task = asyncio.create_task(client.send_command("GetSTKVersion /"))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert not client.connected
    writer.close.assert_called_once()


@pytest.mark.asyncio
async def test_reconnect_after_failed_response():
    client = _client()
    client._reader.feed_data(b"BAD")
    with pytest.raises(ValueError):
        await client.send_command("GetSTKVersion /")
    server, client.host, client.port = await start_mock_server()
    try:
        await client.connect()
        assert (await client.send_command("GetSTKVersion /"))["raw"] == "STK v11.6.0"
    finally:
        await client.disconnect()
        server.close()
        await server.wait_closed()


@pytest.mark.parametrize("payload", [b"NACK", b"BAD", b"AC"])
@pytest.mark.asyncio
async def test_failed_ack_handshake_does_not_leave_connected_client(payload):
    client = _client()
    reader, writer = client._reader, client._writer
    reader.feed_data(payload)
    reader.feed_eof()
    with patch("asyncio.open_connection", AsyncMock(return_value=(reader, writer))):
        with pytest.raises((ConnectionError, ValueError, asyncio.IncompleteReadError)):
            await client.connect()
    assert not client.connected
    writer.close.assert_called_once()


@pytest.mark.asyncio
async def test_absent_optional_ack_is_allowed_but_partial_ack_is_not():
    client = _client()
    assert await client._read_ack(timeout=0.01, allow_missing=True) is None
    client._reader.feed_data(b"A")
    with pytest.raises(asyncio.TimeoutError):
        await client._read_ack(timeout=0.01, allow_missing=True)
    client._abort_connection()


@pytest.mark.asyncio
async def test_empty_command_does_not_write_or_disconnect():
    client = _client()
    with pytest.raises(ValueError, match="empty"):
        await client.send_command("  ")
    client._writer.write.assert_not_called()
    assert client.connected
    client._abort_connection()
