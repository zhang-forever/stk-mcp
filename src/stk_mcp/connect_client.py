"""
STK Connect TCP Client.

Implements the STK Connect socket protocol:
1. Send command string + '\\n'
2. With ACK on: read ACK (3 chars "ACK\\n") or NAK (4 chars "NAK\\n")
3. For return-data commands: read 40-byte header "COMMANDNAME  NUMBYTES\\n"
4. Single-line: read NUMBYTES chars of data
5. Multi-line: first read gives row count, then loop reading header+data per row
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

logger = logging.getLogger("stk_mcp.connect")

# Commands that return data and their read method:
# 1 = single-line, 2 = multi-line
# Source: STK Connect Java StkCon.java returnDataHash
RETURN_DATA_COMMANDS: dict[str, int] = {
    "3DGETVIEWPOINT": 1,
    "ACATEVENTS_RM": 2,
    "ACATPROBABILITY_R": 1,
    "ACCESS": 1,
    "ACCESSINFO_R": 1,
    "ADF_RM": 2,
    "AER": 1,
    "ALLACCESS": 2,
    "ALLINSTANCENAMES": 1,
    "ANIMFRAMERATE": 1,
    "ANTENNA_RM": 2,
    "ASYNCALLOWED_R": 1,
    "ATTCOV_RM": 2,
    "ATMOSPHERE_RM": 2,
    "AUTHOR_RM": 2,
    "AVIATOR_RM": 2,
    "CALCULATIONTOOL_R": 1,
    "CALCULATIONTOOL_RM": 2,
    "CAT_RM": 2,
    "CENTRALBODY": 1,
    "CENTRALBODY_R": 1,
    "CENTRALBODYNAMES": 1,
    "CHAINS_R": 1,
    "CHAINS_RM": 2,
    "CHAINALLACCESS": 2,
    "CHAINGETACCESSES": 2,
    "CHAINGETINTERVALS": 2,
    "CHAINGETSTRANDS": 2,
    "CHECKISAPPBUSY": 1,
    "CHECKSCENARIO": 1,
    "CLOSEAPPROACH": 2,
    "COMMQUERY": 1,
    "COMMSYSTEM_RM": 2,
    "COMPONENTBROWSER_RM": 2,
    "COMPUTECRDN": 1,
    "CONEXPORTCONFIG_R": 1,
    "CONVERT": 1,
    "CONVERTCOORD": 1,
    "CONVERTDATE": 1,
    "CONVERTUNIT": 1,
    "COV_R": 1,
    "COV_RM": 2,
    "DECKACCESS": 2,
    "DISPERSIONELLIPSE_R": 1,
    "DISQUERY": 1,
    "DOESOBJEXIST": 1,
    "EXPORTCONFIG_R": 1,
    "ENVIRONMENT_RM": 2,
    "FIELDOFVIEW_RM": 2,
    "GETACCESSES": 2,
    "GETANIMTIME": 1,
    "GETANIMATIONDATA": 1,
    "GETATTITUDE": 2,
    "GETATTITUDETARG": 1,
    "GETBOUNDARY": 2,
    "GETCONVERSION": 1,
    "GETDB": 1,
    "GETDEFAULTDIR": 1,
    "GETDESCRIPTION": 1,
    "GETDIRECTORY": 1,
    "GETDSPFLAG": 1,
    "GETDSPINTERVALS": 1,
    "GETDSPTIMES": 1,
    "GETEPOCH": 1,
    "GETFULLREPORT": 2,
    "GETIPCVERSION": 1,
    "GETLASTCOMMAND": 2,
    "GETLICENSES": 2,
    "GETLINE": 2,
    "GETMAPSTYLES_R": 1,
    "GETMARKERLIST": 2,
    "GETMESSAGELOGFILE": 1,
    "GETNUMNOTES": 1,
    "GETPROPNAME": 2,
    "GETPROPERTIES": 1,
    "GETREPORT": 2,
    "GETRPTSUMMARY": 2,
    "GETSCENPATH": 1,
    "GETSTKHOMEDIR": 1,
    "GETSTKVERSION": 1,
    "GETTIMEPERIOD": 1,
    "GETUSERDIR": 1,
    "GRAPHICS_R": 1,
    "GRIDINSPECTOR": 1,
    "GROUNDELLIPSE_R": 1,
    "KEYVALUEMETADATA_RM": 2,
    "LICENSE_RM": 2,
    "LIFETIME": 1,
    "LISTOPERATOR": 1,
    "LISTSUBOBJECTS": 1,
    "MAPANNOTATION_RM": 2,
    "MAPID_R": 1,
    "MATLAB_R": 1,
    "MEASURESURFACEDISTANCE": 1,
    "MISSIONMODELER_RM": 2,
    "ONEPOINTACCESS": 2,
    "PARALLEL_RM": 2,
    "PERCENTCOMPLETE_R": 1,
    "POSITION": 1,
    "POSITION_RM": 2,
    "QUICKREPORT_RM": 2,
    "RADAR_RM": 2,
    "RADARCLUTTER_RM": 2,
    "RANGE_RM": 2,
    "RCS_R": 1,
    "RCS_RM": 2,
    "RECEIVER_RM": 2,
    "RECORDMOVIE2D_R": 1,
    "REPORT_RM": 2,
    "SCHED": 2,
    "SDF_RM": 2,
    "SEDS_RM": 2,
    "SENSORQUERY": 1,
    "SHOWNAMES": 1,
    "SHOWUNITS": 1,
    "SOFTVTR2D_R": 1,
    "SPATIALTOOL_R": 1,
    "SPATIALTOOL_RM": 2,
    "STARDATA_RM": 2,
    "STOPWATCHGET": 1,
    "TERRAIN_RM": 2,
    "TERRAINSERVER_RM": 2,
    "TE_TRACKCOMPARISONCALCULATOR_RM": 2,
    "TE_TRACKTRACEABILITY_RM": 2,
    "TIMETOOL_R": 1,
    "TIMETOOL_RM": 2,
    "TRANSMITTER_RM": 2,
    "UNITS_GET": 1,
    "UNITS_CONVERT": 1,
    "VECTORTOOL_R": 1,
    "VECTORTOOL_RM": 2,
    "VIEWER_RM": 2,
    "VISIBILITY_RM": 2,
    "VO_R": 1,
    "VO_RM": 2,
    "VOLUMEGEOMETRY_R": 1,
    "VOLUMEGEOMETRY_RM": 2,
    "VOLUMETRIC_RM": 2,
    "WINDOW2D_R": 1,
    "WINDOW3D_R": 1,
    "ZOOM_R": 1,
}

HEADER_LENGTH = 40  # STK return header is always 40 bytes


class StkConnectClient:
    """Async TCP client for STK Connect protocol."""

    def __init__(self, host: str = "localhost", port: int = 5001):
        self.host = host
        self.port = port
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._lock = asyncio.Lock()
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        """Open TCP connection and enable ACK mode."""
        self._reader, self._writer = await asyncio.open_connection(
            self.host, self.port
        )
        self._connected = True
        logger.info("Connected to STK at %s:%d", self.host, self.port)

        # Enable ACK (required for reliable command-response)
        await self._send_raw("ConControl / AckOn")
        # Read ACK response (no ACK for the AckOn command itself in some versions)
        try:
            await self._read_ack(timeout=5.0)
        except Exception:
            # Some STK versions don't ACK the AckOn command itself
            pass

    async def disconnect(self) -> None:
        """Close TCP connection gracefully."""
        if not self._connected:
            return
        try:
            await self._send_raw("ConControl / AckOff")
            await asyncio.sleep(0.1)
            await self._send_raw("ConControl / Disconnect")
        except Exception:
            pass
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass
        self._connected = False
        logger.info("Disconnected from STK")

    async def send_command(
        self, command: str, timeout: float = 120.0
    ) -> dict:
        """
        Send a Connect command and return the result.

        Returns:
            {
                "ack": "ACK" | "NAK",
                "data": list[str] | None,  # returned data lines (if any)
                "raw": str,                # raw response text
            }
        """
        async with self._lock:
            if not self._connected:
                raise ConnectionError("Not connected to STK")

            # Send the command
            await self._send_raw(command)

            # Read ACK/NAK
            ack = await self._read_ack(timeout=timeout)

            result = {"ack": ack, "data": None, "raw": ""}

            if ack == "ACK":
                # Check if this command returns data
                cmd_name = command.strip().split()[0].upper()
                ret_method = RETURN_DATA_COMMANDS.get(cmd_name)

                if ret_method == 1:
                    # Single-line return
                    data = await self._read_single_line(timeout=timeout)
                    result["data"] = data
                    result["raw"] = "\n".join(data) if data else ""
                elif ret_method == 2:
                    # Multi-line return
                    data = await self._read_multi_line(timeout=timeout)
                    result["data"] = data
                    result["raw"] = "\n".join(data) if data else ""

            return result

    async def _send_raw(self, command: str) -> None:
        """Send raw command bytes."""
        if not self._writer:
            raise ConnectionError("Writer not initialized")
        self._writer.write((command + "\n").encode("utf-8"))
        await self._writer.drain()

    async def _read_ack(self, timeout: float = 10.0) -> str:
        """Read ACK or NAK response."""
        if not self._reader:
            raise ConnectionError("Reader not initialized")

        # Read first byte to determine ACK vs NAK
        first_byte = await asyncio.wait_for(
            self._reader.read(1), timeout=timeout
        )
        if not first_byte:
            raise ConnectionError("Connection closed by STK")

        first_char = first_byte.decode("utf-8")

        if first_char == "N":
            # NAK: read remaining 3 chars ("AK\n")
            rest = await asyncio.wait_for(
                self._reader.read(3), timeout=timeout
            )
            return "NAK"
        else:
            # ACK: read remaining 2 chars ("CK\n") or ("CK\r\n")
            rest = await asyncio.wait_for(
                self._reader.read(2), timeout=timeout
            )
            return "ACK"

    async def _read_header(
        self, timeout: float = 30.0
    ) -> tuple[str, int]:
        """Read a 40-byte return header. Returns (command_name, byte_count)."""
        if not self._reader:
            raise ConnectionError("Reader not initialized")

        raw = await asyncio.wait_for(
            self._reader.readexactly(HEADER_LENGTH), timeout=timeout
        )
        header_text = raw.decode("utf-8").strip()

        # Parse: "COMMANDNAME    NUMBYTES"
        parts = header_text.split()
        if len(parts) >= 2:
            cmd_name = parts[0]
            try:
                num_bytes = int(parts[1])
            except ValueError:
                num_bytes = 0
            return cmd_name, num_bytes
        elif len(parts) == 1:
            return parts[0], 0
        else:
            return "", 0

    async def _read_single_line(
        self, timeout: float = 30.0
    ) -> list[str]:
        """Read single-line return data."""
        cmd_name, num_bytes = await self._read_header(timeout=timeout)

        if num_bytes <= 0:
            return []

        raw = await asyncio.wait_for(
            self._reader.readexactly(num_bytes), timeout=timeout
        )
        text = raw.decode("utf-8").strip()
        return [text] if text else []

    async def _read_multi_line(
        self, timeout: float = 120.0
    ) -> list[str]:
        """Read multi-line return data."""
        # First header gives the row count
        _cmd_name, num_bytes = await self._read_header(timeout=timeout)

        if num_bytes <= 0:
            return []

        # Read the number of rows
        raw_count = await asyncio.wait_for(
            self._reader.readexactly(num_bytes), timeout=timeout
        )
        try:
            num_rows = int(raw_count.decode("utf-8").strip())
        except ValueError:
            # If parsing fails, the first read might be actual data
            return [raw_count.decode("utf-8").strip()]

        lines: list[str] = []
        for _ in range(num_rows):
            _cmd, nbytes = await self._read_header(timeout=timeout)
            if nbytes > 0:
                raw = await asyncio.wait_for(
                    self._reader.readexactly(nbytes), timeout=timeout
                )
                line = raw.decode("utf-8").strip()
                if line:
                    lines.append(line)

        return lines
