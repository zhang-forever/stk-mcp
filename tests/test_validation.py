"""Tests for input validation and the raw-command opt-in gate."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from stk_mcp.validation import (  # noqa: E402
    CommandValidationError,
    raw_command_allowed,
    validate_command,
    validate_name,
    validate_path,
    validate_raw_command,
)


@pytest.mark.parametrize(
    "command",
    [
        "Access */Satellite/A */Satellite/B",
        "GetAnimTime *",
        "New / */Satellite Sat1",
    ],
)
def test_validate_command_accepts_normal_commands(command: str) -> None:
    assert validate_command(command) == command


@pytest.mark.parametrize(
    "command",
    [
        "Access A\nDelete *",  # newline injection
        "Access A\r\nDelete *",  # CRLF injection
        "Access A\x00Delete *",  # NUL byte
        "Access A\tB",  # tab is a control character
        "",
        "   ",
    ],
)
def test_validate_command_rejects_control_characters(command: str) -> None:
    with pytest.raises(CommandValidationError):
        validate_command(command)


def test_validate_command_rejects_overlong_payload() -> None:
    with pytest.raises(CommandValidationError):
        validate_command("Access */Satellite/A " + "x" * 9000)


def test_validate_command_rejects_non_string() -> None:
    with pytest.raises(CommandValidationError):
        validate_command(123)  # type: ignore[arg-type]


@pytest.mark.parametrize("name", ["Sat1", "GPS-1", "sat_A.1", "*Sat1", "123"])
def test_validate_name_accepts_tokens(name: str) -> None:
    assert validate_name(name) == name


@pytest.mark.parametrize(
    "name",
    ["", "Sat 1", "Sat;Delete", "Sat/Child", "../etc/passwd", "a" * 200],
)
def test_validate_name_rejects_bad_tokens(name: str) -> None:
    with pytest.raises(CommandValidationError):
        validate_name(name)


@pytest.mark.parametrize(
    "path", ["*/Satellite/Sat1", "Satellite/Sat1", "*/Satellite/Sat1/Sensor/S1"]
)
def test_validate_path_accepts_object_paths(path: str) -> None:
    assert validate_path(path) == path


@pytest.mark.parametrize(
    "path", ["", "Satellite", "*/Satellite/Sat 1", "Satellite/../x", "a/" * 10]
)
def test_validate_path_rejects_bad_paths(path: str) -> None:
    with pytest.raises(CommandValidationError):
        validate_path(path)


def test_raw_command_gate_is_off_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("STK_MCP_ALLOW_RAW_COMMAND", raising=False)
    assert raw_command_allowed() is False
    with pytest.raises(CommandValidationError):
        validate_raw_command("Delete */Satellite/A")


@pytest.mark.parametrize("value", ["1", "true", "YES", "on"])
def test_raw_command_gate_accepts_truthy_values(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("STK_MCP_ALLOW_RAW_COMMAND", value)
    assert raw_command_allowed() is True
    assert validate_raw_command("GetAnimTime *") == "GetAnimTime *"


def test_raw_command_gate_still_blocks_injection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("STK_MCP_ALLOW_RAW_COMMAND", "1")
    with pytest.raises(CommandValidationError):
        validate_raw_command("GetAnimTime *\nDelete *")


def test_client_rejects_injected_command_before_sending() -> None:
    """The TCP client is the last line of defense; it must not write the socket."""
    from stk_mcp.connect_client import StkConnectClient

    client = StkConnectClient(host="127.0.0.1", port=5001)
    client._connected = True

    class _BoomWriter:
        def write(self, _data: bytes) -> None:  # pragma: no cover - asserted below
            raise AssertionError("socket write must not be reached")

        async def drain(self) -> None:  # pragma: no cover
            raise AssertionError("socket drain must not be reached")

    client._writer = _BoomWriter()  # type: ignore[assignment]
    client._reader = object()  # type: ignore[assignment]

    with pytest.raises(CommandValidationError):
        asyncio.run(client.send_command("Access A\nDelete */Satellite/B"))
