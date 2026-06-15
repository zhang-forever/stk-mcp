"""STK state management and lifespan factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import AsyncIterator, Any, Optional

from stk_mcp.connect_client import StkConnectClient

logger = logging.getLogger("stk_mcp.logic")


@dataclass
class StkState:
    """Holds the STK connection state, accessible from all MCP tools."""

    client: StkConnectClient
    host: str = "localhost"
    port: int = 5001
    com_root: Any = field(default=None)
    com_app: Any = field(default=None)

    @property
    def connected(self) -> bool:
        return self.client.connected

    @property
    def com_available(self) -> bool:
        return self.com_root is not None


def _init_com() -> tuple[Any, Any]:
    """Try to connect to STK via COM. Returns (com_app, com_root) or (None, None)."""
    try:
        import win32com.client
        for prog_id in ["STK12.Application", "STK11.Application", "STK.Application"]:
            try:
                app = win32com.client.GetActiveObject(prog_id)
                root = app.Personality2
                logger.info("STK COM connected via %s", prog_id)
                return app, root
            except Exception:
                continue
        logger.warning("STK COM: no active STK instance found")
    except ImportError:
        logger.warning("pywin32 not installed — COM features disabled")
    return None, None


def create_stk_lifespan(host: str = "localhost", port: int = 5001):
    """Create an async lifespan context manager for the MCP server."""

    @asynccontextmanager
    async def stk_lifespan(server) -> AsyncIterator[StkState]:
        client = StkConnectClient(host=host, port=port)
        try:
            await client.connect()
            logger.info("STK Connect ready at %s:%d", host, port)
        except Exception as e:
            logger.warning(
                "Could not connect to STK at %s:%d — %s. "
                "Tools will attempt to connect on first use.",
                host,
                port,
                e,
            )

        # Try COM connection
        com_app, com_root = _init_com()

        state = StkState(
            client=client, host=host, port=port,
            com_app=com_app, com_root=com_root,
        )
        try:
            yield state
        finally:
            await client.disconnect()

    return stk_lifespan
