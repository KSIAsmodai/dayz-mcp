"""Source contracts for manual-gearbox settle and nearest-vehicle get-in."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from tests._addon_paths import addon_root


MOD_SCRIPTS = addon_root() / "scripts"
CAR_SCRIPT = MOD_SCRIPTS / "4_World" / "MCP_CarScript.c"
CLIENT_BRIDGE = MOD_SCRIPTS / "5_Mission" / "MCPClientBridge.c"
SERVER_PY = Path(__file__).resolve().parents[1] / "dayz_mcp" / "server.py"
KNOWN_CLEAR_STATICS = {
    "s_Active",
    "s_Car",
    "s_TickEngineReady",
    "s_TickThrottleSet",
}


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


def _body_re(source: str, pattern: str) -> str:
    match = re.search(pattern, source)
    if not match:
        raise AssertionError(f"missing: {pattern}")
    brace = source.index("{", match.end())
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[brace + 1 : index]
    raise AssertionError(f"unterminated block: {pattern}")


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


class FbDeb907a1SourceContractTest(unittest.TestCase):
    def test_fb_deb9_07a1_shift_up_sits_behind_settle_interval_guard(self) -> None:
        source = CAR_SCRIPT.read_text(encoding="utf-8")
        drive = _method_body(source, "class MCPCarDrive")
        const_match = re.search(
            r"static\s+const\s+float\s+(\w+)\s*=\s*[0-9.]+\s*;", drive
        )
        self.assertIsNotNone(const_match)
        const_name = const_match.group(1)

        clear = _method_body(drive, "static void Clear()")
        extra = [
            name
            for name in re.findall(r"\b(s_\w+)\s*=", clear)
            if name not in KNOWN_CLEAR_STATICS
        ]
        self.assertEqual(len(extra), 1)
        stamp_name = extra[0]

        on_input = _method_body(source, "override void OnInput(float dt)")
        throttle_body = _body_re(on_input, r"if\s*\(\s*throttle\s*>\s*0\.1\s*\)")
        self.assertIn("ShiftUp", throttle_body)
        self.assertRegex(throttle_body, r"\bif\s*\(")
        self.assertLess(throttle_body.index("if"), throttle_body.index("ShiftUp"))
        self.assertIn("GetTickTime", throttle_body)
        self.assertIn(const_name, throttle_body)
        self.assertIn(stamp_name, throttle_body)
        self.assertRegex(_compact(throttle_body), r">=")
        inner = _body_re(throttle_body, r"if\s*\(")
        self.assertIn("ShiftUp", inner)
        self.assertIn(stamp_name, inner)
        self.assertNotIn("ShiftTo", throttle_body)
        self.assertIn("ShiftTo(CarGear.FIRST)", on_input)

    def test_fb_deb9_07a1_find_transport_near_client_picks_nearest_to_pos(self) -> None:
        source = CLIENT_BRIDGE.read_text(encoding="utf-8")
        finder = _method_body(
            source, "protected Transport FindTransportNearClient(vector pos)"
        )
        loop = _body_re(finder, r"while\s*\(\s*i\s*<\s*m_ReadyObjects\.Count\s*\(\s*\)\s*\)")
        self.assertIsNone(re.search(r"\breturn\b", loop))
        self.assertRegex(loop, r"=\s*vehicle\b")
        self.assertRegex(loop, r"Distance(?:Sq)?\s*\(")
        self.assertRegex(loop, r"<(?!=)")
        self.assertNotRegex(loop, r"<=")
        self.assertIn("GetPosition", finder)
        self.assertGreater(finder.rindex("return"), finder.rindex("while"))

    def test_fb_deb9_07a1_vehicle_get_in_client_description_names_nearest_to_pos(
        self,
    ) -> None:
        source = SERVER_PY.read_text(encoding="utf-8")
        func = re.search(r"async def vehicle_get_in_client\s*\(", source)
        self.assertIsNotNone(func)
        deco = source.rfind("@app.tool", 0, func.start())
        self.assertGreaterEqual(deco, 0)
        description = source[deco : func.start()]
        self.assertIn("Seat the connected", description)
        self.assertIn("nearby vehicle", description)
        self.assertIn("nearest to pos", description)
        self.assertIn("search radius", description)
        self.assertIn("does not place the player in the server crew", description)


if __name__ == "__main__":
    unittest.main()
