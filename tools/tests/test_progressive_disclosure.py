"""Progressive tools/list disclosure (fb-20260917-092908-2ad1).

Initial client-mode catalog stays near 8.5 KB. world_*/vehicle_*/ui_* appear
only after a lease is held.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault(
    "LOCALAPPDATA", str(Path(tempfile.gettempdir()) / "dayz-mcp-localapp")
)
if sys.platform != "win32":
    import ctypes

    class _FakeWinDLL:
        def __init__(self, name: str, *args: object, **kwargs: object) -> None:
            self._name = name

        def __getattr__(self, name: str) -> MagicMock:
            return MagicMock(name=f"{self._name}.{name}")

    ctypes.WinDLL = _FakeWinDLL  # type: ignore[misc, assignment]
    sys.modules.setdefault(
        "msvcrt",
        types.SimpleNamespace(
            LK_NBLCK=1,
            LK_UNLCK=2,
            get_osfhandle=lambda fd: fd,
            locking=lambda *_a, **_k: None,
        ),
    )

from dayz_mcp.server import ServerConfig, build_app


LEASE_REVEAL_PREFIXES = ("world_", "vehicle_", "ui_")
INITIAL_CATALOG_MAX_BYTES = 12_000
INITIAL_CATALOG_TARGET_BYTES = 8_500


class _FakeClientRuntime:
    def __init__(self, config: ServerConfig, **_kwargs: object) -> None:
        self.config = config
        self.active_lease_token = None
        self._registered_tool_names = None


def _catalog_bytes(tools: list[object]) -> int:
    payload = [
        tool.model_dump(mode="json", by_alias=True, exclude_none=True)
        for tool in tools
    ]
    return len(
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )


def _names(tools: list[object]) -> set[str]:
    return {tool.name for tool in tools}


class ProgressiveDisclosureTest(unittest.IsolatedAsyncioTestCase):
    def _client_app(self):
        config = ServerConfig(
            mode="client",
            key="k",
            port=12345,
            log_sink=lambda _message: None,
        )
        with patch("dayz_mcp.server.ClientRuntime", _FakeClientRuntime):
            return build_app(config)

    async def test_embedded_catalog_keeps_world_vehicle_ui(self) -> None:
        app, _runtime = build_app(ServerConfig(log_sink=lambda _message: None))
        names = _names(await app.list_tools())
        self.assertIn("world_spawn", names)
        self.assertIn("vehicle_enter", names)
        self.assertIn("ui_click", names)

    async def test_client_initial_catalog_is_compact_and_hides_lease_tools(self) -> None:
        app, runtime = self._client_app()
        self.assertIsNone(runtime.active_lease_token)
        tools = await app.list_tools()
        names = _names(tools)
        size = _catalog_bytes(tools)

        self.assertGreaterEqual(size, 4_000)
        self.assertLessEqual(size, INITIAL_CATALOG_MAX_BYTES)
        self.assertLess(
            abs(size - INITIAL_CATALOG_TARGET_BYTES),
            4_000,
            f"initial tools/list was {size} bytes, expected ~{INITIAL_CATALOG_TARGET_BYTES}",
        )
        for name in names:
            self.assertFalse(
                name.startswith(LEASE_REVEAL_PREFIXES),
                f"{name} must stay hidden until lease",
            )
        self.assertIn("session_acquire_wait", names)
        self.assertIn("bridge_status", names)
        self.assertNotIn("world_spawn", names)
        self.assertNotIn("vehicle_control", names)
        self.assertNotIn("ui_dialog", names)

    async def test_client_catalog_reveals_world_vehicle_ui_after_lease(self) -> None:
        app, runtime = self._client_app()
        before = _names(await app.list_tools())
        runtime.active_lease_token = "lease-token-after-acquire"
        after = _names(await app.list_tools())

        self.assertNotIn("world_spawn", before)
        self.assertIn("world_spawn", after)
        self.assertIn("vehicle_enter", after)
        self.assertIn("ui_click", after)
        self.assertGreater(_catalog_bytes(await app.list_tools()), INITIAL_CATALOG_MAX_BYTES)


if __name__ == "__main__":
    unittest.main()
