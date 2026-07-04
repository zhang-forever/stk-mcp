"""Mock STK Connect TCP server for offline protocol testing.

Reproduces the exact wire format captured from live STK v11.6.0:
  - ACK  = b"ACK"   (3 bytes, no newline)
  - NACK = b"NACK"  (4 bytes)
  - single-line return: ACK + 40-byte header + "\\n" + data
        header = "<COMMANDNAME>" left-justified, padded to 40 chars,
        where the trailing field is the data byte count.

Only a small, deterministic command set is implemented — enough to
exercise every branch of StkConnectClient without a running STK.
"""

from __future__ import annotations

import asyncio

HEADER_LENGTH = 40


def _make_single_line(command_name: str, data: str) -> bytes:
    """Build ACK + 40-byte header + data, matching live STK v11.6.0 framing.

    Captured wire format (GetSTKVersion /):
        b"ACK" + b"GETSTKVERSION 11" + spaces + b"\\n" + b"STK v11.6.0"
    The 40-byte header includes a trailing newline as its final byte:
    39 bytes of "COMMANDNAME <num_bytes>" padding + "\\n" == 40 bytes total.
    Data follows immediately with no extra separator.
    """
    payload = data.encode("utf-8")
    header_text = f"{command_name} {len(payload)}"
    # Pad to 39 chars, then append "\n" to reach exactly 40 bytes.
    header = header_text.ljust(HEADER_LENGTH - 1)[: HEADER_LENGTH - 1] + "\n"
    return b"ACK" + header.encode("utf-8") + payload


# Deterministic responses keyed by the exact command string sent.
# Values are either raw bytes (sent verbatim) or a callable returning bytes.
_RESPONSES: dict[str, bytes] = {
    "ConControl / AckOn": b"ACK",
    "ConControl / AckOff": b"ACK",
    "GetSTKVersion /": _make_single_line("GETSTKVERSION", "STK v11.6.0"),
    "CheckScenario /": _make_single_line("CHECKSCENARIO", "0"),
    # Commands that STK rejects without proper scope return NACK:
    "GetSTKVersion": b"NACK",
    "CheckScenario": b"NACK",
}


async def _handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while True:
            line = await reader.readline()
            if not line:
                break
            cmd = line.decode("utf-8").rstrip("\r\n")
            if cmd == "ConControl / Disconnect":
                break
            resp = _RESPONSES.get(cmd, b"NACK")
            writer.write(resp)
            await writer.drain()
    except (asyncio.CancelledError, ConnectionResetError):
        pass
    finally:
        writer.close()


async def start_mock_server(host: str = "127.0.0.1", port: int = 0):
    """Start the mock server. Returns (server, host, actual_port)."""
    server = await asyncio.start_server(_handle, host, port)
    actual_port = server.sockets[0].getsockname()[1]
    return server, host, actual_port
