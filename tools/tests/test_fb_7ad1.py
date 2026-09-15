"""vehicle_release Abort must dump remaining samples before clearing the trace.

fb-20260915-014739-7ad1: release before stop used to wipe the buffer with no
JSONL. File-only: reads Enforce and tool descriptions; does not import the
Windows-only server stack.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from tests._addon_paths import addon_root


TOOLS_DIR = Path(__file__).resolve().parents[1]
CAR_SCRIPT = addon_root() / "scripts" / "4_World" / "MCP_CarScript.c"
CLIENT_BRIDGE = addon_root() / "scripts" / "5_Mission" / "MCPClientBridge.c"
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


class TraceAbortAutodumpContractTest(unittest.TestCase):
    def test_abort_dumps_before_clear(self) -> None:
        abort = _method_body(
            CAR_SCRIPT.read_text(encoding="utf-8"),
            "static void Abort(string reason)",
        )
        self.assertIn("Dump(s_TraceId)", abort)
        self.assertLess(abort.index("Dump("), abort.index("ClearState("))
        self.assertIn("s_Count > 0", abort)

    def test_release_and_shutdown_still_abort(self) -> None:
        bridge = CLIENT_BRIDGE.read_text(encoding="utf-8")
        release = _method_body(bridge, "protected bool DispatchVehicleRelease(")
        shutdown = _method_body(bridge, "void Shutdown()")
        self.assertIn('MCPVehicleTrace.Abort("vehicle_release");', release)
        self.assertIn('MCPVehicleTrace.Abort("shutdown");', shutdown)

    def test_tool_descriptions_require_stop_then_release(self) -> None:
        text = SERVER_PY.read_text(encoding="utf-8")
        self.assertIn("Call mode=stop before ", text)
        self.assertIn("vehicle_release; release Abort autodumps", text)
        self.assertIn("Call vehicle_trace mode=stop before ", text)


if __name__ == "__main__":
    unittest.main()
