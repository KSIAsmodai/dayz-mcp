"""Official stdio --client plan B when the host MCP vsock channel is dead.

The agent host's mcp.list_tools can raise McpStartupError (vsock) for a whole
session. That is the host transport, not the DayZ daemon. Spawn the installer
--client process and speak MCP JSON-RPC on stdin/stdout. Do not start --embedded
on the shared port. Close the stdio process at session end.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

TOOLS_DIR = Path(__file__).resolve().parent.parent
DEFAULT_VENV_PYTHON = TOOLS_DIR / ".venv-mcp" / "Scripts" / "python.exe"
DEFAULT_KEYFILE = TOOLS_DIR / ".dayz_mcp.key"
DEFAULT_PORT = 8765
PLAN_B_ATTEMPTS = 3
PLAN_B_BACKOFF_S = 2.0
HOST_STARTUP_MARKERS = (
    "mcpstartuperror",
    "vsock",
    "failed to start mcp",
)

T = TypeVar("T")


class StdioBridgeError(RuntimeError):
    """tools/list failed after the plan-B retry budget."""


def is_host_startup_error(text: str) -> bool:
    lowered = text.casefold()
    return any(marker in lowered for marker in HOST_STARTUP_MARKERS)


def official_client_argv(
    *,
    python: str,
    keyfile: str,
    port: int = DEFAULT_PORT,
) -> list[str]:
    return [
        python,
        "-m",
        "dayz_mcp",
        "--client",
        "--keyfile",
        keyfile,
        "--port",
        str(port),
    ]


def retry_with_backoff(
    operation: Callable[[], T],
    *,
    attempts: int = PLAN_B_ATTEMPTS,
    backoff_s: float = PLAN_B_BACKOFF_S,
    sleeper: Callable[[float], None] = time.sleep,
) -> T:
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    last_error: BaseException | None = None
    for index in range(attempts):
        try:
            return operation()
        except Exception as error:
            last_error = error
            if index >= attempts - 1:
                break
            delay = backoff_s * float(index + 1)
            sleeper(delay)
    raise StdioBridgeError(
        "tools/list failed after "
        f"{attempts} attempts. Host mcp.list_tools/vsock is not the transport. "
        "Spawn the official stdio bridge: python -m dayz_mcp --client "
        "--keyfile <keyfile> --port 8765"
    ) from last_error


def list_tools_once(command: list[str], *, cwd: str | None = None) -> list[str]:
    import asyncio

    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    async def _run() -> list[str]:
        params = StdioServerParameters(
            command=command[0],
            args=list(command[1:]),
            cwd=cwd,
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listed = await session.list_tools()
        return [tool.name for tool in listed.tools]

    return asyncio.run(_run())


def probe_tools_list(
    command: list[str],
    *,
    cwd: str | None = None,
    attempts: int = PLAN_B_ATTEMPTS,
    backoff_s: float = PLAN_B_BACKOFF_S,
    list_tools: Callable[[list[str]], list[str]] | None = None,
    sleeper: Callable[[float], None] = time.sleep,
) -> list[str]:
    caller = list_tools or (lambda argv: list_tools_once(argv, cwd=cwd))
    return retry_with_backoff(
        lambda: caller(command),
        attempts=attempts,
        backoff_s=backoff_s,
        sleeper=sleeper,
    )


def _resolve_python(explicit: str | None) -> str:
    if explicit:
        return str(Path(explicit))
    return str(DEFAULT_VENV_PYTHON)


def _resolve_keyfile(explicit: str | None) -> str:
    if explicit:
        return str(Path(explicit))
    return str(DEFAULT_KEYFILE)


def _print_command_payload(argv: list[str]) -> dict[str, object]:
    return {
        "ok": True,
        "plan": "stdio_client",
        "cwd": str(TOOLS_DIR),
        "argv": argv,
        "attempts": PLAN_B_ATTEMPTS,
        "backoff_s": PLAN_B_BACKOFF_S,
        "close_at": "session_end",
        "note": (
            "Host mcp.list_tools McpStartupError/vsock is the host channel. "
            "Keep this --client process for the session; --probe only checks "
            "tools/list and then exits."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Print or probe the official DayZ-MCP stdio --client plan B "
            "when the host vsock channel raises McpStartupError."
        )
    )
    parser.add_argument("--python", help="Python used to spawn -m dayz_mcp")
    parser.add_argument("--keyfile", help="Installer keyfile path, not the key")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--print-command",
        action="store_true",
        help="Print the official --client argv and exit (default)",
    )
    parser.add_argument(
        "--probe",
        action="store_true",
        help="Retry tools/list on a short-lived --client spawn",
    )
    parser.add_argument("--attempts", type=int, default=PLAN_B_ATTEMPTS)
    parser.add_argument("--backoff-s", type=float, default=PLAN_B_BACKOFF_S)
    args = parser.parse_args(argv)
    command = official_client_argv(
        python=_resolve_python(args.python),
        keyfile=_resolve_keyfile(args.keyfile),
        port=args.port,
    )
    if args.probe:
        try:
            names = probe_tools_list(
                command,
                cwd=str(TOOLS_DIR),
                attempts=args.attempts,
                backoff_s=args.backoff_s,
            )
        except StdioBridgeError as error:
            sys.stdout.write(
                json.dumps(
                    {
                        "ok": False,
                        "error": str(error),
                        "argv": command,
                        "cwd": str(TOOLS_DIR),
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n"
            )
            return 1
        sys.stdout.write(
            json.dumps(
                {
                    "ok": True,
                    "plan": "stdio_client",
                    "tools": names,
                    "count": len(names),
                    "argv": command,
                    "cwd": str(TOOLS_DIR),
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n"
        )
        return 0
    sys.stdout.write(
        json.dumps(
            _print_command_payload(command),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
