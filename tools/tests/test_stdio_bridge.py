from __future__ import annotations

import json
import unittest

from dayz_mcp.stdio_bridge import (
    PLAN_B_ATTEMPTS,
    PLAN_B_BACKOFF_S,
    StdioBridgeError,
    is_host_startup_error,
    official_client_argv,
    probe_tools_list,
    retry_with_backoff,
    main,
)


class HostStartupErrorTest(unittest.TestCase):
    def test_markers(self) -> None:
        self.assertTrue(is_host_startup_error("McpStartupError: vsock connect failed"))
        self.assertTrue(is_host_startup_error("failed to start MCP over vsock"))
        self.assertFalse(is_host_startup_error("lease_required"))
        self.assertFalse(is_host_startup_error("daemon_unavailable"))


class OfficialClientArgvTest(unittest.TestCase):
    def test_installer_shape(self) -> None:
        argv = official_client_argv(
            python=r"C:\tools\.venv-mcp\Scripts\python.exe",
            keyfile=r"C:\tools\.dayz_mcp.key",
            port=8765,
        )
        self.assertEqual(argv[1:4], ["-m", "dayz_mcp", "--client"])
        self.assertIn("--keyfile", argv)
        self.assertIn("--port", argv)
        self.assertNotIn("--embedded", argv)


class RetryWithBackoffTest(unittest.TestCase):
    def test_recovers_after_host_startup_error(self) -> None:
        sleeps: list[float] = []
        calls = {"n": 0}

        def flaky() -> str:
            calls["n"] = calls["n"] + 1
            if calls["n"] < 3:
                raise ConnectionError("McpStartupError: vsock unavailable")
            return "bridge_status"

        result = retry_with_backoff(
            flaky,
            attempts=PLAN_B_ATTEMPTS,
            backoff_s=PLAN_B_BACKOFF_S,
            sleeper=sleeps.append,
        )
        self.assertEqual(result, "bridge_status")
        self.assertEqual(sleeps, [2.0, 4.0])

    def test_exhausted_budget_names_stdio_client(self) -> None:
        with self.assertRaises(StdioBridgeError) as raised:
            retry_with_backoff(
                lambda: (_ for _ in ()).throw(
                    RuntimeError("McpStartupError: vsock")
                ),
                attempts=2,
                backoff_s=0.0,
                sleeper=lambda _delay: None,
            )
        message = str(raised.exception)
        self.assertIn("after 2 attempts", message)
        self.assertIn("--client", message)
        self.assertIn("vsock is not the transport", message)

    def test_rejects_zero_attempts(self) -> None:
        with self.assertRaises(ValueError):
            retry_with_backoff(lambda: None, attempts=0)


class ProbeToolsListTest(unittest.TestCase):
    def test_uses_injected_lister(self) -> None:
        seen: list[list[str]] = []

        def fake_list(command: list[str]) -> list[str]:
            seen.append(command)
            return ["bridge_status", "session_status"]

        names = probe_tools_list(
            ["python", "-m", "dayz_mcp", "--client"],
            list_tools=fake_list,
            sleeper=lambda _delay: None,
        )
        self.assertEqual(names, ["bridge_status", "session_status"])
        self.assertEqual(seen[0][3], "--client")


class PrintCommandCliTest(unittest.TestCase):
    def test_default_prints_official_argv(self) -> None:
        from io import StringIO
        from unittest.mock import patch

        buf = StringIO()
        with patch("sys.stdout", buf):
            code = main(
                [
                    "--print-command",
                    "--python",
                    r"C:\venv\python.exe",
                    "--keyfile",
                    r"C:\tools\.dayz_mcp.key",
                    "--port",
                    "8765",
                ]
            )
        self.assertEqual(code, 0)
        payload = json.loads(buf.getvalue())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["plan"], "stdio_client")
        self.assertEqual(payload["argv"][3], "--client")
        self.assertEqual(payload["close_at"], "session_end")
        self.assertNotIn("embedded", " ".join(payload["argv"]))


if __name__ == "__main__":
    unittest.main()
