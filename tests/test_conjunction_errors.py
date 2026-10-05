"""Offline tool tests; no live STK or COM automation is used."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from stk_mcp.tools.cat import stk_conjunction


def _context(client):
    return SimpleNamespace(request_context=SimpleNamespace(
        lifespan_context=SimpleNamespace(client=client)
    ))


@pytest.mark.parametrize("params", [{}, {
    "dimension_type": "Fixed", "tangential_km": 3,
    "cross_track_km": 2, "normal_km": 1, "hard_body_radius_m": 10,
}])
@pytest.mark.asyncio
async def test_unsupported_threat_volume_never_mutates_stk(params):
    client = SimpleNamespace(send_command=AsyncMock())
    result = await stk_conjunction(_context(client), "acat_set_threat_volume", **params)
    assert "Unsupported action" in result
    assert "no STK settings were changed" in result
    client.send_command.assert_not_awaited()


@pytest.mark.parametrize("ack,expected", [
    ("NAK", "Event retrieval failed"),
    ("ACK", "No conjunction events found"),
])
@pytest.mark.asyncio
async def test_assess_distinguishes_failed_event_query_from_no_events(ack, expected):
    async def send(command):
        if command.startswith("ACATEvents_RM"):
            return {"ack": ack, "data": None, "raw": ""}
        if command == "Units_Get * Connect":
            return {"ack": "ACK", "data": ["Distance Meters; Time Seconds;"], "raw": ""}
        if command.startswith("Units_Convert"):
            return {"ack": "ACK", "data": ["5000"], "raw": "5000"}
        if command.startswith("DoesObjExist"):
            return {"ack": "ACK", "data": ["1"], "raw": "1"}
        return {"ack": "ACK", "data": None, "raw": ""}
    client = SimpleNamespace(send_command=AsyncMock(side_effect=send))
    result = await stk_conjunction(_context(client), "assess",
                                   primary_satellite="Primary", secondary_satellite="Secondary")
    assert expected in result
    if ack == "NAK":
        assert "No conjunction events found" not in result
