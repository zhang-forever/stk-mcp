"""Input validation for STK Connect commands.

STK Connect is a line-oriented protocol: one command per line, parameters
separated by spaces.  Tool arguments come from an LLM (via MCP) and are
interpolated into those command strings, so any embedded ``\\r``, ``\\n`` or
NUL byte would let a caller append a second, unintended command.  These
helpers reject such input at the boundary instead of relying on every call
site to remember.
"""

from __future__ import annotations

import os
import re

#: Longest command we are willing to hand to STK.  Connect itself has no
#: documented limit; this is a sanity bound that keeps a runaway model reply
#: from flooding the socket.
MAX_COMMAND_LENGTH = 8192

#: Object/chain/scenario names become a single Connect token.  Allow letters,
#: digits, underscore, dash, dot and a leading ``*`` (STK's "current object"
#: prefix), and nothing else.
_NAME_RE = re.compile(r"^\*?[A-Za-z0-9_\-.]{1,128}$")

#: Object paths look like ``*/Satellite/Sat1`` or ``Satellite/Sat1``.
_PATH_RE = re.compile(r"^(\*|[A-Za-z0-9_\-.]+)(/[A-Za-z0-9_\-.]+){1,8}$")

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


class CommandValidationError(ValueError):
    """Raised when tool input cannot be safely placed in a Connect command."""


def _require_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise CommandValidationError(f"{field} must be a string, got {type(value).__name__}")
    return value


def validate_command(command: object) -> str:
    """Validate a complete Connect command line before it is sent.

    Returns the command unchanged so it can be used inline.  Rejects control
    characters (including newlines), NUL bytes, empty commands and overlong
    payloads.
    """
    cmd = _require_str(command, "command")
    if not cmd.strip():
        raise CommandValidationError("command must not be empty")
    if _CONTROL_CHARS.search(cmd):
        raise CommandValidationError("command must not contain control characters or newlines")
    if len(cmd) > MAX_COMMAND_LENGTH:
        raise CommandValidationError(f"command exceeds {MAX_COMMAND_LENGTH} characters")
    return cmd


def validate_name(value: object, field: str = "name") -> str:
    """Validate a single Connect token (object name, chain name, scenario name)."""
    name = _require_str(value, field)
    if not _NAME_RE.match(name):
        raise CommandValidationError(
            f"{field} {name!r} must be 1-128 characters of letters, digits, "
            "_ - . and may start with *"
        )
    return name


def validate_path(value: object, field: str = "path") -> str:
    """Validate a Connect object path such as ``*/Satellite/Sat1``."""
    path = _require_str(value, field)
    if not _PATH_RE.match(path):
        raise CommandValidationError(
            f"{field} {path!r} must look like */Class/Instance (at most 8 segments)"
        )
    if any(segment in {".", ".."} for segment in path.split("/")):
        raise CommandValidationError(f"{field} {path!r} must not contain . or .. segments")
    return path


def validate_number(value: object, field: str = "number") -> int | float:
    """Return *value* if it is a finite number, else raise."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CommandValidationError(f"{field} must be a number, got {type(value).__name__}")
    if value != value or value in (float("inf"), float("-inf")):  # NaN / inf
        raise CommandValidationError(f"{field} must be a finite number")
    return value


def raw_command_allowed() -> bool:
    """Whether the ``stk_util(send_command=...)`` escape hatch is enabled.

    A single Connect command can still delete scenarios, overwrite files or
    change global preferences, so the passthrough is opt-in: set
    ``STK_MCP_ALLOW_RAW_COMMAND=1`` to enable it.
    """
    return os.environ.get("STK_MCP_ALLOW_RAW_COMMAND", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def validate_raw_command(command: object) -> str:
    """Validate a caller-supplied raw Connect command, honoring the opt-in gate."""
    if not raw_command_allowed():
        raise CommandValidationError(
            "raw command passthrough is disabled; set STK_MCP_ALLOW_RAW_COMMAND=1 "
            "to enable stk_util(action='send_command')"
        )
    return validate_command(command)
