"""Offline CAT regressions using documented command/response shapes, not live STK."""

import math
import re
import shlex
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from stk_mcp.app import mcp
from stk_mcp.tools.cat import stk_conjunction
from stk_mcp.tools.orbit import _propagate_satellite


def response(data=None, ack="ACK"):
    return {"ack": ack, "data": data, "raw": "\n".join(data or [])}


class RecordingClient:
    def __init__(self, *, failure=None, missing=(), units="Meters", conversion=None):
        self.commands = []
        self.failure = failure
        self.missing = missing
        self.units = units
        self.conversion = conversion

    async def send_command(self, command):
        self.commands.append(command)
        if self.failure and re.search(self.failure, command):
            return response(ack="NAK")
        if command == "Units_Get * Connect":
            return response([f"Distance {self.units}; Time Seconds; Date GregorianUTC; Latitude Degrees; Longitude Degrees;"])
        if command.startswith("Units_Convert "):
            tokens = shlex.split(command)
            assert tokens[:5] == ["Units_Convert", "*", "Unit", "Distance", "km"]
            assert tokens[5] == self.units
            if self.conversion is not None:
                return response(self.conversion)
            factor = {"Meters": 1000, "Kilometers": 1, "Feet": 3280.839895}[self.units]
            return response([str(float(tokens[6]) * factor)])
        if command.startswith("DoesObjExist"):
            assert command.startswith("DoesObjExist / ")
            return response(["0" if command.split()[-1] in self.missing else "1"])
        return response()


def context(client):
    return SimpleNamespace(request_context=SimpleNamespace(
        lifespan_context=SimpleNamespace(client=client, com_available=False)
    ))


CAT_PARAMS = dict(satellite_name="Sat", database_path="catalog.tle",
                  filter_apogee_perigee=20, filter_orbit_path=10,
                  add_threats=True, max_threats=25)
SETUP_PARAMS = dict(acat_name="Test", start_time="1 Jan 2026 00:00:00",
                    stop_time="2 Jan 2026 00:00:00", threshold=5)
PREFILTER_PARAMS = dict(out_of_date="On", apogee_perigee=20,
                       orbit_path=10, time_filter="Off")
ASSESS_PARAMS = dict(primary_satellite="Primary", secondary_satellite="Secondary",
                     start_time="1 Jan 2026 00:00:00", stop_time="2 Jan 2026 00:00:00",
                     tle_primary_line1="primary line 1", tle_primary_line2="primary line 2",
                     tle_secondary_line1="secondary line 1", tle_secondary_line2="secondary line 2")


@pytest.mark.parametrize("failure", [r" Range ", r" Database ", r" Filter ApogeePerigee ",
                                      r" Filter OrbitPath ", r" AddThreats "])
@pytest.mark.asyncio
async def test_cat_setup_stops_at_first_rejected_setting(failure):
    client = RecordingClient(failure=failure)
    result = await stk_conjunction(context(client), "cat_setup", **CAT_PARAMS)
    assert "operation failed" in result
    assert "CAT configured" not in result
    assert "Earlier changes may remain" in result
    assert re.search(failure, client.commands[-1])


@pytest.mark.parametrize("failure", [r"DoesObjExist", r"New /", r" TimePeriod ", r" Threshold "])
@pytest.mark.asyncio
async def test_acat_setup_stops_at_first_rejected_setting(failure):
    client = RecordingClient(failure=failure, missing={"*/AdvCAT/Test"})
    result = await stk_conjunction(context(client), "acat_setup", **SETUP_PARAMS)
    assert "operation failed" in result
    assert "setup complete" not in result and "ACAT configured" not in result
    assert re.search(failure, client.commands[-1])


@pytest.mark.parametrize("failure", [r" PreFilters OutOfDate ", r" PreFilters ApogeePerigee ",
                                      r" PreFilters OrbitPath ", r" PreFilters Time "])
@pytest.mark.asyncio
async def test_prefilters_stop_at_first_rejected_setting(failure):
    client = RecordingClient(failure=failure)
    result = await stk_conjunction(context(client), "acat_set_prefilters", **PREFILTER_PARAMS)
    assert "operation failed" in result
    assert not result.startswith("Prefilters:")
    assert re.search(failure, client.commands[-1])


@pytest.mark.parametrize("failure", [
    r"DoesObjExist / \*/Satellite/Primary", r"DoesObjExist / \*/Satellite/Secondary",
    r"New / \*/Satellite Secondary", r"SetState \*/Satellite/Primary",
    r"Propagate \*/Satellite/Primary", r"SetState \*/Satellite/Secondary",
    r"Propagate \*/Satellite/Secondary", r"New / \*/AdvCAT",
    r" TimePeriod ", r" Threshold ", r" Primary Add ", r" Secondary Add ", r" Compute$",
])
@pytest.mark.asyncio
async def test_assess_stops_on_each_failed_prerequisite(failure):
    client = RecordingClient(failure=failure, missing={"*/Satellite/Secondary"})
    result = await stk_conjunction(context(client), "assess", **ASSESS_PARAMS)
    assert "operation failed" in result
    assert "No conjunction events found" not in result
    assert "Computation completed" not in result
    assert re.search(failure, client.commands[-1])
    assert not any(command.startswith("ACATEvents_RM") for command in client.commands)


@pytest.mark.parametrize("exists", [True, False])
@pytest.mark.asyncio
async def test_acat_setup_uses_numeric_existence_response(exists):
    client = RecordingClient(missing=set() if exists else {"*/AdvCAT/Test"})
    result = await stk_conjunction(context(client), "acat_setup", acat_name="Test")
    assert "failed" not in result
    assert client.commands == ["DoesObjExist / */AdvCAT/Test"] + ([] if exists else ["New / */AdvCAT Test"])


@pytest.mark.parametrize("data", [None, [], ["Yes"], ["No"], ["01"], ["0", "1"], ["unexpected"]])
@pytest.mark.asyncio
async def test_invalid_existence_response_never_creates_objects(data):
    client = SimpleNamespace(send_command=AsyncMock(return_value=response(data)))
    result = await stk_conjunction(context(client), "acat_setup")
    assert "Invalid DoesObjExist" in result
    client.send_command.assert_awaited_once_with("DoesObjExist / */AdvCAT/AdvCAT")


@pytest.mark.parametrize("action,params", [
    ("cat_setup", CAT_PARAMS), ("cat_compute", {"satellite_name": "Sat"}),
    ("acat_setup", SETUP_PARAMS), ("acat_set_prefilters", PREFILTER_PARAMS),
    ("assess", ASSESS_PARAMS),
])
@pytest.mark.parametrize("failure", ["^Units_Get", "^Units_Convert"])
@pytest.mark.asyncio
async def test_unit_lookup_or_conversion_rejection_stops_before_mutation(action, params, failure):
    client = RecordingClient(failure=failure)
    result = await stk_conjunction(context(client), action, **params)
    assert "operation failed" in result
    assert all(c.startswith("Units_") for c in client.commands)
    assert re.search(failure, client.commands[-1])


@pytest.mark.parametrize("data", [None, [], [""], ["Time Seconds;"],
                                   ["Distance Meters; Distance Kilometers;"],
                                   ['Distance Bad"Unit;'], ["Distance;"]])
@pytest.mark.asyncio
async def test_malformed_unit_response_stops_before_mutation(data):
    client = SimpleNamespace(send_command=AsyncMock(return_value=response(data)))
    result = await stk_conjunction(context(client), "assess", **ASSESS_PARAMS)
    assert "Unable to determine Connect distance units" in result
    client.send_command.assert_awaited_once_with("Units_Get * Connect")


@pytest.mark.parametrize("data", [[], ["invalid"], ["nan"], ["inf"], ["-1"], ["0"], ["1", "2"]])
@pytest.mark.asyncio
async def test_malformed_conversions_stop_before_mutation(data):
    client = RecordingClient(conversion=data)
    result = await stk_conjunction(context(client), "assess", **ASSESS_PARAMS)
    assert "Invalid distance conversion" in result
    assert len(client.commands) == 2


@pytest.mark.parametrize("unit,factor", [("Meters", 1000), ("Kilometers", 1), ("Feet", 3280.839895)])
@pytest.mark.asyncio
async def test_assess_converts_km_without_changing_session_units(unit, factor):
    client = RecordingClient(units=unit)
    result = await stk_conjunction(context(client), "assess", **ASSESS_PARAMS)
    assert "Computation completed" in result
    threshold_command = next(c for c in client.commands if " Threshold " in c)
    assert math.isclose(float(threshold_command.split()[-1]), 5 * factor)
    assert not any("Units_Set" in c or "SetUnits" in c for c in client.commands)


@pytest.mark.parametrize("action,params,expected", [
    ("cat_setup", CAT_PARAMS, ["Range 50000.0", "Filter ApogeePerigee 20000.0", "Filter OrbitPath 10000.0"]),
    ("cat_compute", {"satellite_name": "Sat"}, ["Range 50000.0"]),
    ("acat_setup", SETUP_PARAMS, ["Threshold 5000.0"]),
    ("acat_set_prefilters", PREFILTER_PARAMS, ["PreFilters ApogeePerigee 20000.0", "PreFilters OrbitPath 10000.0"]),
])
@pytest.mark.asyncio
async def test_numeric_distances_use_converted_values(action, params, expected):
    client = RecordingClient()
    result = await stk_conjunction(context(client), action, **params)
    assert "failed" not in result
    for suffix in expected:
        assert any(c.endswith(suffix) for c in client.commands)


@pytest.mark.parametrize("action,param", [("cat_setup", "range_threshold"),
    ("cat_setup", "filter_apogee_perigee"), ("cat_setup", "filter_orbit_path"),
    ("cat_compute", "range_threshold"), ("acat_setup", "threshold"),
    ("acat_set_prefilters", "apogee_perigee"), ("acat_set_prefilters", "orbit_path"),
    ("assess", "threshold_km")])
@pytest.mark.parametrize("value", [-1, math.nan, math.inf])
@pytest.mark.asyncio
async def test_invalid_numeric_distance_never_sends_commands(action, param, value):
    client = RecordingClient()
    params = dict(satellite_name="Sat", primary_satellite="Primary", secondary_satellite="Secondary")
    params[param] = value
    result = await stk_conjunction(context(client), action, **params)
    assert "positive" in result or "finite and nonnegative" in result
    assert not client.commands


@pytest.mark.parametrize("action,params", [
    ("acat_setup", {"start_time": "start"}), ("assess", {"stop_time": "stop"}),
    ("assess", {"tle_primary_line1": "line 1"}), ("assess", {"tle_secondary_line2": "line 2"}),
])
@pytest.mark.asyncio
async def test_incomplete_pairs_rejected_before_commands(action, params):
    client = RecordingClient()
    result = await stk_conjunction(context(client), action, **params)
    assert "together" in result
    assert not client.commands


@pytest.mark.asyncio
async def test_single_sample_step_is_explicitly_unsupported_without_mutation():
    client = RecordingClient()
    result = await stk_conjunction(context(client), "acat_setup", sample_step_size=60)
    assert "Unsupported sample_step_size" in result
    assert not client.commands


@pytest.mark.asyncio
async def test_missing_secondary_requires_orbit_before_creation():
    client = RecordingClient(missing={"*/Satellite/Secondary"})
    result = await stk_conjunction(context(client), "assess", primary_satellite="Primary", secondary_satellite="Secondary")
    assert "provide both secondary TLE lines" in result
    assert not any(c.startswith("New ") for c in client.commands)


@pytest.mark.asyncio
async def test_repeated_assessments_use_distinct_objects_without_clearing_existing_data():
    client = RecordingClient()
    for _ in range(2):
        result = await stk_conjunction(context(client), "assess", **ASSESS_PARAMS)
        assert "Assessment object: ConjunctionAssessment_" in result
    creations = [c for c in client.commands if c.startswith("New / */AdvCAT")]
    assert len(creations) == len(set(creations)) == 2
    assert all(command.endswith(" NoDefault") for command in creations)
    assert all(" Ignore" not in c and "RemoveAll" not in c and "Unload" not in c for c in client.commands)


@pytest.mark.parametrize("ack,expected", [("ACK", "propagated"), ("NAK", "Failed to propagate")])
@pytest.mark.asyncio
async def test_orbit_propagation_preserves_string_contract(ack, expected):
    client = SimpleNamespace(send_command=AsyncMock(return_value=response(ack=ack)))
    result = await _propagate_satellite(context(client), "Satellite")
    assert expected in result
    client.send_command.assert_awaited_once_with("Propagate */Satellite/Satellite")


@pytest.mark.asyncio
async def test_failure_wrapper_preserves_registered_mcp_schema():
    tool = next(tool for tool in await mcp.list_tools() if tool.name == "stk_conjunction")
    properties = tool.inputSchema["properties"]
    assert "ctx" not in properties
    assert "action" in properties and "threshold_km" in properties
    assert "args" not in properties and "kwargs" not in properties


@pytest.mark.asyncio
async def test_noop_prefilters_do_not_query_or_mutate_stk():
    client = RecordingClient()
    assert await stk_conjunction(context(client), "acat_set_prefilters") == "No filters changed"
    assert not client.commands


@pytest.mark.asyncio
async def test_missing_primary_stops_before_any_mutation():
    client = RecordingClient(missing={"*/Satellite/Primary"})
    result = await stk_conjunction(context(client), "assess", **ASSESS_PARAMS)
    assert "Primary satellite 'Primary' does not exist" in result
    assert all(c.startswith(("Units_", "DoesObjExist")) for c in client.commands)


@pytest.mark.parametrize("failure", ["Units_Get * Connect", "CAT */Satellite/Sat Range 50000.0"])
@pytest.mark.asyncio
async def test_transport_error_is_explicit_and_stops_setup(failure):
    client = RecordingClient()
    send = client.send_command

    async def failing_send(command):
        if command == failure:
            client.commands.append(command)
            raise ConnectionError("socket closed")
        return await send(command)

    client.send_command = failing_send
    result = await stk_conjunction(context(client), "cat_setup", **CAT_PARAMS)
    assert "operation failed" in result and "socket closed" in result
    assert client.commands[-1] == failure


@pytest.mark.asyncio
async def test_propagation_transport_error_stops_assessment():
    client = RecordingClient()
    send = client.send_command

    async def failing_send(command):
        if command.startswith("Propagate"):
            client.commands.append(command)
            raise ConnectionError("socket closed")
        return await send(command)

    client.send_command = failing_send
    result = await stk_conjunction(context(client), "assess", **ASSESS_PARAMS)
    assert "Failed to propagate Primary" in result and "socket closed" in result
    assert client.commands[-1] == "Propagate */Satellite/Primary"
    assert not any(c.startswith("New / */AdvCAT") for c in client.commands)
