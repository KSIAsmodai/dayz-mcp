"""Pre-run desktop unlock + brightness gate (fb-20260918-134756-05a0 / c0e5)."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock
from unittest.mock import AsyncMock, patch

from PIL import Image

import mcp_capture
from dayz_mcp import dayz_test_tool
from dayz_mcp import server
from dayz_mcp import steam_preflight
from tests.test_dayz_test_tool import (
    RUN_ID,
    _Bundle,
    _Opened,
    _Runtime,
    _policy,
    _sealed,
    _terminal,
)


def _bright(**_kwargs: object) -> dict[str, object]:
    return {"ok": True, "mean_brightness": 80.0, "nonblack_ratio": 0.9}


def _black(**_kwargs: object) -> dict[str, object]:
    return {"ok": True, "mean_brightness": 0.0, "nonblack_ratio": 0.0}


def _ok_desktop() -> mcp_capture.PrerunDesktopResult:
    return mcp_capture.PrerunDesktopResult(
        error_code=None,
        desktop="unlocked",
        mean_brightness=80.0,
        nonblack_ratio=0.9,
        waited_s=0.01,
        remediation="",
    )


def _locked_desktop() -> mcp_capture.PrerunDesktopResult:
    return mcp_capture.PrerunDesktopResult(
        error_code=mcp_capture.SESSION_LOCKED,
        desktop="locked",
        mean_brightness=None,
        nonblack_ratio=None,
        waited_s=30.0,
        remediation=mcp_capture.REMEDIATION_SESSION_LOCKED,
    )


class PrerunDesktopGateTest(unittest.TestCase):
    def test_unlocked_and_bright_passes_without_sleep(self) -> None:
        sleeps: list[float] = []
        result = mcp_capture.run_prerun_desktop_gate(
            timeout_s=30,
            probe_desktop=lambda: "unlocked",
            probe_brightness=_bright,
            sleeper=sleeps.append,
            clock=lambda: 0.0,
        )
        self.assertIsNone(result.error_code)
        self.assertEqual(result.desktop, "unlocked")
        self.assertEqual(result.mean_brightness, 80.0)
        self.assertEqual(sleeps, [])

    def test_locked_waits_then_aborts_session_locked(self) -> None:
        now = {"t": 0.0}

        def clock() -> float:
            return now["t"]

        def sleeper(delta: float) -> None:
            now["t"] = now["t"] + delta

        brightness = mock.Mock(side_effect=_bright)
        result = mcp_capture.run_prerun_desktop_gate(
            timeout_s=30,
            poll_s=10,
            probe_desktop=lambda: "locked",
            probe_brightness=brightness,
            sleeper=sleeper,
            clock=clock,
        )
        self.assertEqual(result.error_code, "session_locked")
        self.assertIn("Unlock", result.remediation)
        self.assertIn("frame_client_all_black", result.remediation)
        self.assertGreaterEqual(result.waited_s, 30.0)
        brightness.assert_not_called()

    def test_black_waits_then_aborts_desktop_all_black(self) -> None:
        now = {"t": 0.0}

        def clock() -> float:
            return now["t"]

        def sleeper(delta: float) -> None:
            now["t"] = now["t"] + delta

        result = mcp_capture.run_prerun_desktop_gate(
            timeout_s=30,
            poll_s=10,
            probe_desktop=lambda: "unlocked",
            probe_brightness=_black,
            sleeper=sleeper,
            clock=clock,
        )
        self.assertEqual(result.error_code, "desktop_all_black")
        self.assertIn("all-black", result.remediation)
        self.assertIn("frame_client_all_black", result.remediation)
        self.assertEqual(result.mean_brightness, 0.0)
        self.assertGreaterEqual(result.waited_s, 30.0)

    def test_locked_then_unlocks_and_bright_passes(self) -> None:
        now = {"t": 0.0}
        desktops = ["locked", "locked", "unlocked"]

        def clock() -> float:
            return now["t"]

        def sleeper(delta: float) -> None:
            now["t"] = now["t"] + delta

        result = mcp_capture.run_prerun_desktop_gate(
            timeout_s=30,
            poll_s=5,
            probe_desktop=lambda: desktops.pop(0) if desktops else "unlocked",
            probe_brightness=_bright,
            sleeper=sleeper,
            clock=clock,
        )
        self.assertIsNone(result.error_code)
        self.assertEqual(result.desktop, "unlocked")

    def test_black_then_bright_passes(self) -> None:
        now = {"t": 0.0}
        probes = [_black, _bright]

        def clock() -> float:
            return now["t"]

        def sleeper(delta: float) -> None:
            now["t"] = now["t"] + delta

        result = mcp_capture.run_prerun_desktop_gate(
            timeout_s=30,
            poll_s=5,
            probe_desktop=lambda: "unlocked",
            probe_brightness=lambda **_kwargs: probes.pop(0)(),
            sleeper=sleeper,
            clock=clock,
        )
        self.assertIsNone(result.error_code)
        self.assertEqual(result.mean_brightness, 80.0)

    def test_unsupported_probe_does_not_block(self) -> None:
        sleeps: list[float] = []
        result = mcp_capture.run_prerun_desktop_gate(
            probe_desktop=lambda: "unknown",
            probe_brightness=lambda **_kwargs: {
                "ok": False,
                "error": "desktop_probe_unsupported",
            },
            sleeper=sleeps.append,
            clock=lambda: 0.0,
        )
        self.assertIsNone(result.error_code)
        self.assertEqual(sleeps, [])

    def test_probe_failed_does_not_block(self) -> None:
        result = mcp_capture.run_prerun_desktop_gate(
            probe_desktop=lambda: "unlocked",
            probe_brightness=lambda **_kwargs: {
                "ok": False,
                "error": "desktop_probe_failed",
            },
            sleeper=lambda _delta: None,
            clock=lambda: 0.0,
        )
        self.assertIsNone(result.error_code)

    def test_wait_false_aborts_immediately_when_locked(self) -> None:
        sleeps: list[float] = []
        result = mcp_capture.run_prerun_desktop_gate(
            wait=False,
            probe_desktop=lambda: "locked",
            probe_brightness=_bright,
            sleeper=sleeps.append,
            clock=lambda: 0.0,
        )
        self.assertEqual(result.error_code, "session_locked")
        self.assertEqual(sleeps, [])

    def test_brightness_timeout_aborts_with_token(self) -> None:
        now = {"t": 0.0}

        def clock() -> float:
            return now["t"]

        def sleeper(delta: float) -> None:
            now["t"] = now["t"] + delta

        result = mcp_capture.run_prerun_desktop_gate(
            timeout_s=30,
            poll_s=10,
            probe_desktop=lambda: "unlocked",
            probe_brightness=lambda **_kwargs: {
                "ok": False,
                "error": "desktop_probe_timeout",
            },
            sleeper=sleeper,
            clock=clock,
        )
        self.assertEqual(result.error_code, "desktop_probe_timeout")
        self.assertIn("did not finish", result.remediation)
        self.assertGreaterEqual(result.waited_s, 30.0)

    def test_probe_desktop_brightness_off_windows_is_unsupported(self) -> None:
        with mock.patch.object(mcp_capture.sys, "platform", "linux"):
            result = mcp_capture.probe_desktop_brightness()
        self.assertEqual(
            {"ok": False, "error": "desktop_probe_unsupported"}, result
        )

    def test_probe_desktop_brightness_reads_imagegrab(self) -> None:
        image = Image.new("RGB", (64, 64), (80, 80, 80))
        with mock.patch.object(mcp_capture.sys, "platform", "win32"):
            with mock.patch("PIL.ImageGrab.grab", return_value=image):
                result = mcp_capture.probe_desktop_brightness()
        self.assertTrue(result.get("ok"))
        self.assertGreater(float(result["mean_brightness"]), 1.0)
        self.assertGreater(float(result["nonblack_ratio"]), 0.01)

    def test_probe_desktop_brightness_timeout_token(self) -> None:
        def hang(*_args: object, **_kwargs: object) -> Image.Image:
            raise mcp_capture.FuturesTimeout()

        with mock.patch.object(mcp_capture.sys, "platform", "win32"):
            with mock.patch(
                "mcp_capture.ThreadPoolExecutor"
            ) as pool_cls:
                pool = pool_cls.return_value.__enter__.return_value
                pool.submit.return_value.result.side_effect = hang
                result = mcp_capture.probe_desktop_brightness(timeout_s=0.05)
        self.assertEqual(result, {"ok": False, "error": "desktop_probe_timeout"})


class PrerunDesktopDayzTestRunTest(unittest.IsolatedAsyncioTestCase):
    async def test_locked_desktop_refuses_before_launch(self) -> None:
        policy = _policy()
        launch = AsyncMock()
        with patch.object(
            dayz_test_tool, "open_approved_launcher", return_value=_Opened()
        ), patch.object(
            dayz_test_tool.secure_launcher,
            "load_verified_bundle",
            return_value=_Bundle(_sealed(policy)),
        ), patch.object(
            dayz_test_tool.secure_launcher,
            "execute_secure_launcher_request",
            new=launch,
        ), patch.object(
            dayz_test_tool, "evaluate_prerun_desktop", return_value=_locked_desktop()
        ):
            result = await dayz_test_tool.execute_dayz_test_run(
                _Runtime(),
                project="ExampleMod",
                mode="all",
                extra_mods=["@DayZ_MCP"],
            )

        launch.assert_not_awaited()
        self.assertEqual(result["status"], "failed")
        self.assertIsNone(result["run_id"])
        self.assertEqual(result["phase"], "validating")
        self.assertEqual(result["error_code"], "session_locked")
        self.assertIn("Unlock", str(result["remediation"]))

    async def test_locked_desktop_refuses_preflight_before_launch(self) -> None:
        policy = _policy()
        launch = AsyncMock()
        with patch.object(
            dayz_test_tool, "open_approved_launcher", return_value=_Opened()
        ), patch.object(
            dayz_test_tool.secure_launcher,
            "load_verified_bundle",
            return_value=_Bundle(_sealed(policy)),
        ), patch.object(
            dayz_test_tool.secure_launcher,
            "execute_secure_launcher_request",
            new=launch,
        ), patch.object(
            dayz_test_tool, "evaluate_prerun_desktop", return_value=_locked_desktop()
        ):
            result = await dayz_test_tool.execute_dayz_test_run(
                _Runtime(),
                project="ExampleMod",
                mode="all",
                preflight=True,
                extra_mods=["@DayZ_MCP"],
            )

        launch.assert_not_awaited()
        self.assertEqual(result["error_code"], "session_locked")
        self.assertEqual(result.get("preflight_skipped_checks"), ["steam_session"])

    async def test_server_mode_does_not_consult_desktop_gate(self) -> None:
        policy = _policy()

        async def launch(_raw_request: bytes, **kwargs: object) -> int:
            await kwargs["execution_started_cb"]()
            kwargs["output_sink"](
                "stdout",
                _terminal(
                    {
                        "cleanup_degraded": False,
                        "error_code": None,
                        "exit_code": 0,
                        "ok": True,
                        "run_id": RUN_ID,
                    }
                ),
            )
            return 0

        desktop = mock.Mock(return_value=_locked_desktop())
        with patch.object(
            dayz_test_tool, "open_approved_launcher", return_value=_Opened()
        ), patch.object(
            dayz_test_tool.secure_launcher,
            "load_verified_bundle",
            return_value=_Bundle(_sealed(policy)),
        ), patch.object(
            dayz_test_tool.secure_launcher,
            "execute_secure_launcher_request",
            side_effect=launch,
        ), patch.object(
            dayz_test_tool, "evaluate_prerun_desktop", desktop
        ):
            result = await dayz_test_tool.execute_dayz_test_run(
                _Runtime(),
                project="ExampleMod",
                mode="server",
                extra_mods=["@DayZ_MCP"],
            )

        desktop.assert_not_called()
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(result["run_id"], RUN_ID)

    async def test_bright_desktop_reaches_launcher(self) -> None:
        policy = _policy()

        async def launch(_raw_request: bytes, **kwargs: object) -> int:
            await kwargs["execution_started_cb"]()
            kwargs["output_sink"](
                "stdout",
                _terminal(
                    {
                        "cleanup_degraded": False,
                        "error_code": None,
                        "exit_code": 0,
                        "ok": True,
                        "run_id": RUN_ID,
                    }
                ),
            )
            return 0

        with patch.object(
            dayz_test_tool, "open_approved_launcher", return_value=_Opened()
        ), patch.object(
            dayz_test_tool.secure_launcher,
            "load_verified_bundle",
            return_value=_Bundle(_sealed(policy)),
        ), patch.object(
            dayz_test_tool.secure_launcher,
            "execute_secure_launcher_request",
            side_effect=launch,
        ), patch.object(
            dayz_test_tool, "evaluate_prerun_desktop", return_value=_ok_desktop()
        ), patch.object(
            dayz_test_tool,
            "evaluate_steam_session",
            return_value=steam_preflight.SteamSessionResult(
                error_code=None,
                steam_registered_pid=1,
                steam_live_pids=(1,),
                remediation="ok",
            ),
        ):
            result = await dayz_test_tool.execute_dayz_test_run(
                _Runtime(),
                project="ExampleMod",
                mode="all",
                extra_mods=["@DayZ_MCP"],
            )

        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(result["run_id"], RUN_ID)


class PrerunDesktopDescriptionTest(unittest.TestCase):
    def test_readme_names_capture_tandem_step_zero(self) -> None:
        readme = Path(server.__file__).resolve().parents[1] / "README-mcp.md"
        text = readme.read_text(encoding="utf-8")
        self.assertIn("### Capture tandems (step 0)", text)
        self.assertIn("session_locked", text)
        self.assertIn("desktop_all_black", text)
        self.assertIn("frame_client_all_black", text)

    def test_capture_screenshot_description_names_the_prerun_gate(self) -> None:
        text = Path(server.__file__).read_text(encoding="utf-8")
        start = text.index("Capture a screenshot from the DayZDiag window.")
        end = text.index("async def capture_screenshot")
        description = text[start:end]
        self.assertIn("dayz_test_run waits up to 30 s", description)
        self.assertIn("desktop_all_black", description)
        self.assertIn("frame_client_all_black", description)


if __name__ == "__main__":
    unittest.main()
