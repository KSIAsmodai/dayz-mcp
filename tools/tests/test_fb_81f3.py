"""player_teleport must refuse a client-owned seated occupant.

fb-20260915-014733-81f3: teleporting a vehicle_get_in_client occupant desyncs
client and server. File-only: predicate + Enforce/description contracts; does
not import the Windows-only server stack.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from dayz_mcp.occupant_seat import occupant_client_seated
from tests._addon_paths import addon_root


TOOLS_DIR = Path(__file__).resolve().parents[1]
BRIDGE = addon_root() / "scripts" / "5_Mission" / "MCPBridge.c"
SERVER_PY = TOOLS_DIR / "dayz_mcp" / "server.py"


def _method_body(source: str, signature: str) -> str:
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[brace + 1 : index]
    raise AssertionError(f"unterminated method: {signature}")


class OccupantClientSeatedPredicateTest(unittest.TestCase):
    def test_on_foot_and_unread_are_not_seated(self) -> None:
        self.assertFalse(
            occupant_client_seated({"ok": 1, "seated": 0, "is_authority_owner": 0})
        )
        self.assertFalse(occupant_client_seated(None))
        self.assertFalse(occupant_client_seated({"ok": 0}))

    def test_client_owned_seat_is_rejected(self) -> None:
        self.assertTrue(
            occupant_client_seated(
                {"seated": 1, "is_owner": 1, "is_authority_owner": 0}
            )
        )
        self.assertTrue(occupant_client_seated({"seated": True}))

    def test_authority_owned_seat_is_not_rejected(self) -> None:
        self.assertFalse(
            occupant_client_seated({"seated": 1, "is_authority_owner": 1})
        )


class OccupantClientSeatedSourceContractTest(unittest.TestCase):
    def test_enforce_rejects_before_set_transform(self) -> None:
        body = _method_body(
            BRIDGE.read_text(encoding="utf-8"),
            "protected bool DispatchPlayerTeleport(",
        )
        self.assertIn('result.error = "occupant_client_seated"', body)
        self.assertIn("IsAuthorityOwner()", body)
        self.assertIn("IsInTransport()", body)
        self.assertIn("GetParent()", body)
        self.assertLess(
            body.index('result.error = "occupant_client_seated"'),
            body.index("veh.SetTransform(mat)"),
        )
        self.assertIn("veh.SetTransform(mat)", body)

    def test_descriptions_name_refusal_and_one_car_limit(self) -> None:
        text = SERVER_PY.read_text(encoding="utf-8")
        self.assertIn("occupant_client_seated", text)
        self.assertIn("One car per run", text)
        self.assertIn("no get-out", text)
        self.assertIn("does not survive the run", text)
        self.assertIn("from dayz_mcp.occupant_seat import occupant_client_seated", text)


if __name__ == "__main__":
    unittest.main()
