"""fb-20260915-143332-00bb + fb-20260915-104637-1004.

Host-safe: peer-gated teleport precheck and object_id teardown copy.
No WinDLL, DayZ, Diag, AddonBuilder, or Steam.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from dayz_mcp import server
from dayz_mcp.server import ServerConfig, build_app


TOOLS_DIR = Path(__file__).resolve().parents[1]
SERVER_PY = TOOLS_DIR / "dayz_mcp" / "server.py"
COMMAND = "player_teleport"
ON_FOOT = {"ok": 1, "seated": 0, "is_authority_owner": 0}
SEATED_CLIENT = {"ok": 1, "seated": 1, "is_owner": 1, "is_authority_owner": 0}


def _content_json(content: object) -> dict:
    if isinstance(content, tuple):
        _blocks, structured = content
        if isinstance(structured, dict):
            return structured
        content = _blocks
    parsed = json.loads(content[0].text)  # type: ignore[index,union-attr]
    if not isinstance(parsed, dict):
        raise AssertionError("expected dict")
    return parsed


def _tool_description(app, name: str) -> str:
    tool = app._tool_manager.get_tool(name)
    return tool.description or ""


class ClientPeerProbeablePredicateTest(unittest.TestCase):
    def test_missing_and_unread_are_not_probeable(self) -> None:
        self.assertFalse(server._client_peer_probeable(None))
        self.assertFalse(server._client_peer_probeable({}))
        self.assertFalse(server._client_peer_probeable({"client_peer": {}}))
        self.assertFalse(
            server._client_peer_probeable({"client_peer": {"last_poll_age_s": None}})
        )

    def test_stale_or_unbound_client_is_not_probeable(self) -> None:
        self.assertFalse(
            server._client_peer_probeable({"client_peer": {"last_poll_age_s": 20.0}})
        )
        self.assertFalse(
            server._client_peer_probeable(
                {"client_peer": {"binding_state": "LEGACY_UNBOUND", "last_poll_age_s": 0.1}}
            )
        )
        self.assertFalse(
            server._client_peer_probeable(
                {
                    "client_peer": {
                        "binding_state": "BOUND",
                        "bound_last_poll_age_s": None,
                        "last_poll_age_s": 0.1,
                    }
                }
            )
        )

    def test_probing_client_is_probeable(self) -> None:
        self.assertTrue(
            server._client_peer_probeable({"client_peer": {"last_poll_age_s": 0.1}})
        )
        self.assertTrue(
            server._client_peer_probeable(
                {
                    "client_peer": {
                        "binding_state": "BOUND",
                        "bound_last_poll_age_s": 0.2,
                    }
                }
            )
        )


class Fb00bbTeleportPrecheckTest(unittest.IsolatedAsyncioTestCase):
    async def _build(self, status: object):
        app, runtime = build_app(
            ServerConfig(key="test-key", port=0, log_sink=lambda _message: None)
        )
        runtime.bridge_status_payload = AsyncMock(return_value=status)
        return app, runtime

    async def test_00bb_no_client_does_not_name_vehicle_telemetry(self) -> None:
        app, runtime = await self._build({"client_peer": {"last_poll_age_s": None}})
        with patch.object(
            runtime,
            "call_bridge",
            new=AsyncMock(return_value={"ok": 1, "pos_real": [1.0, 2.0, 3.0]}),
        ) as call:
            await app.call_tool(
                COMMAND,
                {
                    "pos": [1.0, 0.0, 3.0],
                    "skip_clearance_check": True,
                    "timeout_s": 1.0,
                },
            )
        self.assertEqual([item.args[0] for item in call.await_args_list], [COMMAND])
        self.assertEqual(call.await_args_list[0].args[2], "server")

    async def test_00bb_live_client_still_refuses_seated_occupant(self) -> None:
        app, runtime = await self._build({"client_peer": {"last_poll_age_s": 0.1}})
        with patch.object(
            runtime, "call_bridge", new=AsyncMock(return_value=SEATED_CLIENT)
        ) as call:
            result = _content_json(
                await app.call_tool(
                    COMMAND,
                    {
                        "pos": [1.0, 0.0, 3.0],
                        "skip_clearance_check": True,
                        "timeout_s": 1.0,
                    },
                )
            )
        self.assertEqual(result.get("error"), "occupant_client_seated")
        self.assertEqual([item.args[0] for item in call.await_args_list], ["vehicle_telemetry"])

    async def test_00bb_live_on_foot_still_teleports(self) -> None:
        app, runtime = await self._build({"client_peer": {"last_poll_age_s": 0.1}})
        with patch.object(
            runtime,
            "call_bridge",
            new=AsyncMock(side_effect=[ON_FOOT, {"ok": 1, "pos_real": [1.0, 2.0, 3.0]}]),
        ) as call:
            await app.call_tool(
                COMMAND,
                {
                    "pos": [1.0, 0.0, 3.0],
                    "skip_clearance_check": True,
                    "timeout_s": 1.0,
                },
            )
        self.assertEqual(
            [item.args[0] for item in call.await_args_list],
            ["vehicle_telemetry", COMMAND],
        )


class Fb1004TeardownCopyTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.app, _runtime = build_app(
            ServerConfig(key="test-key", port=0, log_sink=lambda _message: None)
        )

    def test_1004_object_delete_names_session_id_and_seated_care(self) -> None:
        description = _tool_description(self.app, "object_delete")
        self.assertIn("does not survive the run", description)
        self.assertIn("no pos+type delete", description)
        self.assertIn("vehicle_get_in_client", description)
        self.assertIn("needs care", description)
        self.assertIn("object_id", description)

    def test_1004_player_teleport_and_get_in_warn_stale_object_id(self) -> None:
        teleport = _tool_description(self.app, "player_teleport")
        get_in = _tool_description(self.app, "vehicle_get_in_client")
        for description in (teleport, get_in):
            with self.subTest(description=description[:40]):
                self.assertIn("object_delete", description)
                self.assertIn("does not survive the run", description)
                self.assertIn("needs care", description)

    def test_1004_does_not_invent_pos_type_delete_api(self) -> None:
        source = SERVER_PY.read_text(encoding="utf-8")
        start = source.index("async def object_delete(")
        end = source.index("async def notify_players(", start)
        body = source[start:end]
        self.assertIn("object_id", body)
        self.assertNotIn("expected_type", body)
        self.assertNotIn("pos:", body)

    async def test_1004_object_delete_does_not_refuse_seated_occupant(self) -> None:
        # Sanctioned teardown is delete-while-seated (ejects). A refuse guard
        # would remove the only get-out. Copy warns; behaviour stays open.
        app, runtime = build_app(
            ServerConfig(key="test-key", port=0, log_sink=lambda _message: None)
        )
        runtime.bridge_status_payload = AsyncMock(
            return_value={"client_peer": {"last_poll_age_s": 0.1}}
        )
        with patch.object(
            runtime,
            "call_bridge",
            new=AsyncMock(return_value={"ok": 1, "deleted": 1}),
        ) as call:
            result = _content_json(
                await app.call_tool("object_delete", {"object_id": 7, "timeout_s": 1.0})
            )
        self.assertEqual(result.get("deleted"), 1)
        self.assertEqual([item.args[0] for item in call.await_args_list], ["object_delete"])


if __name__ == "__main__":
    unittest.main()
