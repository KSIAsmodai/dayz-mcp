"""capture grab must not inherit a poisoned Git Bash PSModulePath.

fb-20260915-011312-ba70: launching mcp-grab.ps1 with the parent
PSModulePath makes Windows PowerShell fail to find its cmdlets.
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import mcp_capture


_SANE_ERRORS = (
    "no_window",
    "session_locked",
    "capture_timeout",
    "capture_backend_failed",
    "capture_backend_failed:command_not_found",
    "capture_backend_failed: missing_png",
    "capture_backend_failed: no_json",
)


def _write_powershell_stub(directory: Path) -> Path:
    if os.name == "nt":
        script = directory / "powershell.cmd"
        script.write_text(
            "@echo off\r\n"
            "if defined PSModulePath (\r\n"
            "  echo {\"ok\":false,\"error\":\"psmodulepath_leaked\"}\r\n"
            "  exit /b 1\r\n"
            ")\r\n"
            "echo {\"ok\":false,\"error\":\"no_window\"}\r\n",
            encoding="utf-8",
        )
        return script
    script = directory / "powershell"
    script.write_text(
        "#!/bin/sh\n"
        "if [ -n \"${PSModulePath+x}\" ]; then\n"
        "  printf '%s\\n' '{\"ok\":false,\"error\":\"psmodulepath_leaked\"}'\n"
        "  exit 1\n"
        "fi\n"
        "printf '%s\\n' '{\"ok\":false,\"error\":\"no_window\"}'\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script


class GrabPsModulePathTest(unittest.TestCase):
    def test_grab_env_drops_psmodulepath(self) -> None:
        poisoned = {"PATH": "/bin", "PSModulePath": "/git/poisoned/Modules", "HOME": "/tmp"}
        env = mcp_capture._grab_subprocess_env(poisoned)
        self.assertNotIn("PSModulePath", env)
        self.assertEqual(env["PATH"], "/bin")
        self.assertEqual(env["HOME"], "/tmp")

    def test_grab_env_drops_any_psmodulepath_casing(self) -> None:
        env = mcp_capture._grab_subprocess_env({"psmodulepath": "unix-poison", "Keep": "1"})
        self.assertNotIn("psmodulepath", env)
        self.assertEqual(env["Keep"], "1")

    def test_missing_powershell_is_command_not_found(self) -> None:
        with mock.patch.object(mcp_capture, "probe_input_desktop", return_value="unlocked"):
            with mock.patch.object(mcp_capture.os.path, "exists", return_value=True):
                with mock.patch.object(
                    mcp_capture.subprocess,
                    "run",
                    side_effect=FileNotFoundError("powershell"),
                ):
                    result = mcp_capture._run_window_capture(
                        "frame.png", "DayZDiag_x64", 8.0
                    )
        self.assertEqual(
            {"ok": False, "error": "capture_backend_failed:command_not_found"},
            result,
        )

    def test_launch_grab_with_poisoned_psmodulepath(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _write_powershell_stub(Path(tmp))
            poisoned_path = tmp + os.pathsep + os.environ.get("PATH", "")
            with mock.patch.object(mcp_capture, "probe_input_desktop", return_value="unlocked"):
                with mock.patch.object(mcp_capture.os.path, "exists", return_value=True):
                    with mock.patch.dict(
                        os.environ,
                        {
                            "PATH": poisoned_path,
                            "PSModulePath": "/git/bash/poisoned/Modules",
                        },
                        clear=False,
                    ):
                        result = mcp_capture._run_window_capture(
                            os.path.join(tmp, "frame.png"), "DayZDiag_x64", 8.0
                        )

        self.assertIsInstance(result, dict)
        error = str(result.get("error") or "")
        self.assertNotIn("psmodulepath_leaked", error)
        self.assertNotIn("/git/bash/poisoned", error)
        if result.get("ok") is True:
            return
        self.assertTrue(
            error in _SANE_ERRORS or error.startswith("capture_backend_failed"),
            error,
        )
        self.assertEqual(error, "no_window")

    def test_run_passes_env_without_psmodulepath(self) -> None:
        run = mock.Mock()
        run.return_value = mock.Mock(stdout='{"ok":false,"error":"no_window"}\n', stderr="")
        with mock.patch.object(mcp_capture, "probe_input_desktop", return_value="unlocked"):
            with mock.patch.object(mcp_capture.os.path, "exists", return_value=True):
                with mock.patch.dict(os.environ, {"PSModulePath": "/poisoned"}, clear=False):
                    with mock.patch.object(mcp_capture.subprocess, "run", run):
                        mcp_capture._run_window_capture("frame.png", "DayZDiag_x64", 8.0)
        kwargs = run.call_args.kwargs
        self.assertIn("env", kwargs)
        self.assertNotIn("PSModulePath", kwargs["env"])
        self.assertTrue(
            all(key.casefold() != "psmodulepath" for key in kwargs["env"])
        )


class GrabPoisonedPayloadRoundTripTest(unittest.TestCase):
    def test_stub_payload_is_json(self) -> None:
        # Guard the stub contract the launch test depends on.
        payload = json.loads('{"ok":false,"error":"no_window"}')
        self.assertIs(payload["ok"], False)
        self.assertEqual(payload["error"], "no_window")


if __name__ == "__main__":
    unittest.main()
