from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from dayz_mcp import runtime_state
from dayz_mcp.process_lifecycle import RunManifestStore
from dayz_mcp.runtime_state import (
    LifecycleRecoveryFaultStore,
    RuntimePaths,
    _atomic_write_text,
)
from tests.test_doctor import (
    CLAUDE_GOOD,
    CODEX_GOOD,
    DAEMON_GOOD,
    clean_status,
    daemon_argv,
    doctor as doctor_module,
)
from tests.test_fb_160e import _backup_dir, _hex_dirs, _limits, _seed


def _permission_error(winerror: int) -> PermissionError:
    error = PermissionError(13, "Access is denied")
    error.winerror = winerror
    return error


def _tmp_siblings(path: Path) -> list[Path]:
    return list(path.parent.glob(path.name + ".tmp.*"))


def _quarantine_dirs(paths: RuntimePaths) -> list[Path]:
    backups = paths.lifecycle_recovery_faults_dir / "backups"
    if not backups.is_dir():
        return []
    found: list[Path] = []
    for entry in backups.iterdir():
        if entry.name.startswith("quarantine-") and entry.is_dir():
            found.append(entry)
    return sorted(found, key=lambda item: item.name)


def _backups_snapshot(paths: RuntimePaths) -> tuple[tuple[str, ...], dict[str, bytes]]:
    backups = paths.lifecycle_recovery_faults_dir / "backups"
    names = tuple(sorted(entry.name for entry in backups.iterdir()))
    bodies: dict[str, bytes] = {}
    for entry in backups.iterdir():
        for child in entry.iterdir():
            bodies[f"{entry.name}/{child.name}"] = child.read_bytes()
    return names, bodies


def _load_quarantine_json(directory: Path) -> dict[str, object]:
    payload = json.loads(
        (directory / "quarantine.json").read_text(encoding="utf-8")
    )
    if not isinstance(payload, dict):
        raise AssertionError("quarantine.json is not an object")
    return payload


class _FakeMonotonic:
    def __init__(self, value: float = 100.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.value += float(seconds)


class Fb88efAtomicReplaceTest(unittest.TestCase):
    def test_fb_88ef_replace_succeeds_after_short_windows_reader(self) -> None:
        if os.name != "nt":
            self.skipTest("windows sharing")
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "target.json"
            path.write_bytes(b"old-bytes\n")
            handle = open(path, "rb")

            def release() -> None:
                time.sleep(0.05)
                handle.close()

            threading.Thread(target=release, daemon=True).start()
            try:
                _atomic_write_text(path, "new-bytes\n")
            finally:
                if not handle.closed:
                    handle.close()
            self.assertEqual(path.read_bytes(), b"new-bytes\n")
            self.assertEqual(_tmp_siblings(path), [])

    def test_fb_88ef_replace_raises_when_reader_outlives_deadline(self) -> None:
        if os.name != "nt":
            self.skipTest("windows sharing")
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "target.json"
            original = b"old-bytes\n"
            path.write_bytes(original)
            handle = open(path, "rb")
            try:
                with patch.object(runtime_state, "ATOMIC_REPLACE_RETRY_S", 0.05):
                    with self.assertRaises(PermissionError):
                        _atomic_write_text(path, "new-bytes\n")
            finally:
                handle.close()
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(_tmp_siblings(path), [])

    def test_fb_88ef_replace_retries_winerror_5_until_deadline(self) -> None:
        clock = _FakeMonotonic()
        calls = {"n": 0}

        def boom(_source: object, _target: object) -> None:
            calls["n"] += 1
            raise _permission_error(5)

        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "target.json"
            path.write_bytes(b"old-bytes\n")
            with patch.object(runtime_state.time, "monotonic", clock), patch.object(
                runtime_state.time, "sleep", clock.sleep
            ), patch.object(runtime_state.os, "replace", side_effect=boom):
                with self.assertRaises(PermissionError) as raised:
                    _atomic_write_text(path, "new-bytes\n")
            self.assertEqual(getattr(raised.exception, "winerror", None), 5)
            self.assertGreater(calls["n"], 1)
            self.assertGreaterEqual(clock.value, 100.0 + runtime_state.ATOMIC_REPLACE_RETRY_S)
            self.assertEqual(path.read_bytes(), b"old-bytes\n")
            self.assertEqual(_tmp_siblings(path), [])

    def test_fb_88ef_replace_oserror_without_winerror_is_single_attempt(self) -> None:
        calls = {"n": 0}

        def boom(_source: object, _target: object) -> None:
            calls["n"] += 1
            raise OSError("replace failed")

        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "target.json"
            path.write_bytes(b"old-bytes\n")
            with patch.object(runtime_state.os, "replace", side_effect=boom):
                with self.assertRaises(OSError):
                    _atomic_write_text(path, "new-bytes\n")
            self.assertEqual(calls["n"], 1)
            self.assertEqual(path.read_bytes(), b"old-bytes\n")
            self.assertEqual(_tmp_siblings(path), [])

    def test_fb_88ef_replace_permission_winerror_2_is_single_attempt(self) -> None:
        calls = {"n": 0}

        def boom(_source: object, _target: object) -> None:
            calls["n"] += 1
            raise _permission_error(2)

        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "target.json"
            path.write_bytes(b"old-bytes\n")
            with patch.object(runtime_state.os, "replace", side_effect=boom):
                with self.assertRaises(PermissionError):
                    _atomic_write_text(path, "new-bytes\n")
            self.assertEqual(calls["n"], 1)
            self.assertEqual(path.read_bytes(), b"old-bytes\n")
            self.assertEqual(_tmp_siblings(path), [])

    def test_fb_88ef_replace_target_changed_between_attempts(self) -> None:
        calls = {"n": 0}

        def boom(source: object, target: object) -> None:
            calls["n"] += 1
            Path(target).write_bytes(b"changed-by-racer\n")
            raise _permission_error(5)

        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "target.json"
            path.write_bytes(b"old-bytes\n")
            with patch.object(runtime_state.os, "replace", side_effect=boom):
                with self.assertRaisesRegex(RuntimeError, "^atomic_target_changed$"):
                    _atomic_write_text(path, "new-bytes\n")
            self.assertEqual(calls["n"], 1)
            self.assertEqual(path.read_bytes(), b"changed-by-racer\n")
            self.assertEqual(_tmp_siblings(path), [])

    def test_fb_r2_writer_committing_during_backoff_is_not_overwritten(self) -> None:
        if os.name != "nt":
            self.skipTest("windows sharing")
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "target.json"
            v0 = b"version-0\n"
            path.write_bytes(v0)
            v0_sha = runtime_state._sha256(v0)
            handle = open(path, "rb")
            slept = {"n": 0}

            def on_sleep(_seconds: float) -> None:
                slept["n"] += 1
                if slept["n"] != 1:
                    return
                handle.close()
                _atomic_write_text(
                    path, "writer-b\n", expected_sha256=v0_sha
                )

            try:
                with patch.object(runtime_state.time, "sleep", on_sleep):
                    try:
                        _atomic_write_text(
                            path, "writer-a\n", expected_sha256=v0_sha
                        )
                    except RuntimeError as exc:
                        if str(exc) != "atomic_target_changed":
                            self.fail(str(exc))
                    except Exception as exc:
                        self.fail(str(exc))
                    else:
                        self.fail("atomic_target_changed not raised")
            finally:
                if not handle.closed:
                    handle.close()
            self.assertEqual(path.read_bytes(), b"writer-b\n")
            self.assertEqual(_tmp_siblings(path), [])

    def test_fb_r2_interrupt_during_backoff_removes_the_temporary(self) -> None:
        def boom(_source: object, _target: object) -> None:
            raise _permission_error(5)

        def interrupt(_seconds: float) -> None:
            raise KeyboardInterrupt

        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "target.json"
            path.write_bytes(b"old-bytes\n")
            with patch.object(
                runtime_state.os, "replace", side_effect=boom
            ), patch.object(runtime_state.time, "sleep", interrupt):
                with self.assertRaises(KeyboardInterrupt):
                    _atomic_write_text(path, "new-bytes\n")
            self.assertEqual(path.read_bytes(), b"old-bytes\n")
            self.assertEqual(_tmp_siblings(path), [])


class Fb305aManifestBackupQuarantineTest(unittest.TestCase):
    def _store(self, temp_dir: str) -> tuple[RuntimePaths, LifecycleRecoveryFaultStore]:
        paths = RuntimePaths.from_env({"LOCALAPPDATA": temp_dir})
        store = LifecycleRecoveryFaultStore(
            paths, utc_now_fn=lambda: "2026-07-22T00:00:00Z"
        )
        return paths, store

    def _assert_quarantine(
        self,
        directory: Path,
        *,
        receipt_sha: str,
        reason: str,
        expected: bytes,
        observed: bytes,
    ) -> None:
        self.assertTrue(directory.name.startswith(f"quarantine-{receipt_sha}-"))
        self.assertFalse(LifecycleRecoveryFaultStore._valid_hex64(directory.name))
        payload = _load_quarantine_json(directory)
        self.assertEqual(
            set(payload),
            {
                "format_version",
                "reason",
                "receipt_sha256",
                "expected_byte_length",
                "observed_byte_length",
                "observed_sha256",
                "quarantined_at_utc",
            },
        )
        self.assertEqual(payload["format_version"], 1)
        self.assertEqual(payload["reason"], reason)
        self.assertEqual(payload["receipt_sha256"], receipt_sha)
        self.assertEqual(payload["expected_byte_length"], len(expected))
        self.assertEqual(payload["observed_byte_length"], len(observed))
        self.assertEqual(
            payload["observed_sha256"],
            hashlib.sha256(observed).hexdigest().upper(),
        )
        self.assertEqual(payload["quarantined_at_utc"], "2026-07-22T00:00:00Z")

    def test_fb_305a_incomplete_manifest_prefix_is_quarantined(self) -> None:
        raw = b'{"version":1,"runs":[]}\n'
        for observed in (b"", raw[:8]):
            with self.subTest(observed=observed):
                with TemporaryDirectory() as temp_dir:
                    paths, store = self._store(temp_dir)
                    receipt = store.create_manifest_backup(raw)
                    (_backup_dir(paths, receipt) / "manifest.bin").write_bytes(observed)
                    again = store.checkpoint_manifest(raw)
                    self.assertEqual(again, receipt)
                    self.assertEqual(store.read_manifest_backup(receipt), raw)
                    quarantines = _quarantine_dirs(paths)
                    self.assertEqual(len(quarantines), 1)
                    self._assert_quarantine(
                        quarantines[0],
                        receipt_sha=receipt,
                        reason="incomplete_manifest",
                        expected=raw,
                        observed=observed,
                    )

    def test_fb_305a_incomplete_receipt_prefix_is_quarantined(self) -> None:
        raw = b'{"version":1,"runs":[]}\n'
        with TemporaryDirectory() as seed_dir:
            seed_paths, seed_store = self._store(seed_dir)
            seed_receipt = seed_store.create_manifest_backup(raw)
            expected_receipt = (
                _backup_dir(seed_paths, seed_receipt) / "receipt.json"
            ).read_bytes()
        for observed in (b"", expected_receipt[:12]):
            with self.subTest(observed=observed):
                with TemporaryDirectory() as temp_dir:
                    paths, store = self._store(temp_dir)
                    receipt = store.create_manifest_backup(raw)
                    receipt_path = _backup_dir(paths, receipt) / "receipt.json"
                    self.assertEqual(receipt_path.read_bytes(), expected_receipt)
                    receipt_path.write_bytes(observed)
                    again = store.checkpoint_manifest(raw)
                    self.assertEqual(again, receipt)
                    self.assertEqual(store.read_manifest_backup(receipt), raw)
                    quarantines = _quarantine_dirs(paths)
                    self.assertEqual(len(quarantines), 1)
                    self._assert_quarantine(
                        quarantines[0],
                        receipt_sha=receipt,
                        reason="incomplete_receipt",
                        expected=expected_receipt,
                        observed=observed,
                    )

    def test_fb_305a_non_prefix_manifest_mismatch_still_raises(self) -> None:
        with TemporaryDirectory() as temp_dir:
            paths, store = self._store(temp_dir)
            raw = b'{"version":1,"runs":[]}\n'
            receipt = store.create_manifest_backup(raw)
            manifest_path = _backup_dir(paths, receipt) / "manifest.bin"
            for observed in (b"x" * len(raw), raw + b"extra"):
                with self.subTest(observed=observed):
                    manifest_path.write_bytes(observed)
                    with self.assertRaisesRegex(
                        ValueError, "^invalid_lifecycle_manifest_backup$"
                    ):
                        store.create_manifest_backup(raw)
                    self.assertEqual(_quarantine_dirs(paths), [])
                    self.assertEqual(manifest_path.read_bytes(), observed)

    def test_fb_305a_run_manifest_store_starts_over_incomplete_backup(self) -> None:
        with TemporaryDirectory() as temp_dir:
            paths, store = self._store(temp_dir)
            raw = b'{"version":1,"runs":[]}\n'
            receipt = store.create_manifest_backup(raw)
            (_backup_dir(paths, receipt) / "manifest.bin").write_bytes(b"")
            RunManifestStore(paths, checkpoint=store.checkpoint_manifest)
            self.assertEqual(store.read_manifest_backup(receipt), raw)
            self.assertEqual(len(_quarantine_dirs(paths)), 1)

    def test_fb_305a_prune_leaves_quarantine_and_reports_no_blocker(self) -> None:
        with TemporaryDirectory() as temp_dir:
            paths, store = self._store(temp_dir)
            raw = b'{"version":1,"runs":[]}\n'
            receipt = store.create_manifest_backup(raw)
            (_backup_dir(paths, receipt) / "manifest.bin").write_bytes(b"")
            store.checkpoint_manifest(raw)
            quarantines = _quarantine_dirs(paths)
            self.assertEqual(len(quarantines), 1)
            quarantine_json = (quarantines[0] / "quarantine.json").read_bytes()
            _seed(store, paths, 5, start=10)
            with _limits(1, 8):
                store._prune_manifest_backups(receipt)
            self.assertTrue(quarantines[0].is_dir())
            self.assertEqual(
                (quarantines[0] / "quarantine.json").read_bytes(), quarantine_json
            )
            status = store.manifest_backup_retention_status()
            self.assertIsNone(status["blocker"])
            self.assertIn(receipt, _hex_dirs(paths))

    def test_fb_305a_crash_after_rename_before_quarantine_json_repairs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            paths, store = self._store(temp_dir)
            raw = b'{"version":1,"runs":[]}\n'
            receipt = store.create_manifest_backup(raw)
            (_backup_dir(paths, receipt) / "manifest.bin").write_bytes(raw[:4])
            real_json = LifecycleRecoveryFaultStore._write_create_only_json

            def crash(self_store: object, path: Path, payload: dict[str, object]) -> str:
                if Path(path).name == "quarantine.json":
                    raise OSError("injected crash")
                return real_json(self_store, path, payload)

            with patch.object(
                LifecycleRecoveryFaultStore,
                "_write_create_only_json",
                crash,
            ):
                with self.assertRaises(OSError):
                    store.checkpoint_manifest(raw)
            self.assertFalse(_backup_dir(paths, receipt).exists())
            quarantines = _quarantine_dirs(paths)
            self.assertEqual(len(quarantines), 1)
            self.assertFalse((quarantines[0] / "quarantine.json").exists())
            store.checkpoint_manifest(raw)
            self.assertEqual(store.read_manifest_backup(receipt), raw)
            after_repair = _backups_snapshot(paths)
            store.checkpoint_manifest(raw)
            self.assertEqual(_backups_snapshot(paths), after_repair)

    def test_fb_305a_crash_while_recreating_repairs_and_converges(self) -> None:
        with TemporaryDirectory() as temp_dir:
            paths, store = self._store(temp_dir)
            raw = b'{"version":1,"runs":[]}\n'
            receipt = store.create_manifest_backup(raw)
            (_backup_dir(paths, receipt) / "manifest.bin").write_bytes(raw[:4])
            real_bytes = LifecycleRecoveryFaultStore._write_create_only_bytes

            def crash(*args: object) -> None:
                path = Path(str(args[-2]))
                payload = args[-1]
                if not isinstance(payload, bytes):
                    raise TypeError("expected bytes payload")
                if path.name != "manifest.bin":
                    real_bytes(path, payload)
                    return
                backups = path.parent.parent
                quarantined = any(
                    child.name.startswith("quarantine-") for child in backups.iterdir()
                )
                if quarantined:
                    real_bytes(path, payload[: max(1, len(payload) // 2)])
                    raise OSError("injected crash")
                real_bytes(path, payload)

            with patch.object(
                LifecycleRecoveryFaultStore,
                "_write_create_only_bytes",
                crash,
            ):
                with self.assertRaises(OSError):
                    store.checkpoint_manifest(raw)
            store.checkpoint_manifest(raw)
            self.assertEqual(store.read_manifest_backup(receipt), raw)
            self.assertGreaterEqual(len(_quarantine_dirs(paths)), 1)
            after_repair = _backups_snapshot(paths)
            store.checkpoint_manifest(raw)
            self.assertEqual(_backups_snapshot(paths), after_repair)

    def test_fb_r2_state_written_with_upper_case_hashes_still_loads(self) -> None:
        raw = b'{"version":1,"runs":[]}\n'

        def previous_sha256(value: bytes) -> str:
            return hashlib.sha256(value).hexdigest().upper()

        with TemporaryDirectory() as temp_dir:
            paths, store = self._store(temp_dir)
            with patch.object(runtime_state, "_sha256", previous_sha256):
                try:
                    receipt = store.checkpoint_manifest(raw)
                    armed = store.arm(
                        scope="manifest",
                        reason="manifest_corrupt",
                        manifest_sha256=runtime_state._sha256(raw),
                        backup_receipt_sha256=receipt,
                    )
                except Exception as exc:
                    self.fail(str(exc))
            fresh = LifecycleRecoveryFaultStore(
                paths, utc_now_fn=lambda: "2026-07-22T00:00:00Z"
            )
            try:
                active = fresh.load_active()
            except Exception as exc:
                self.fail(str(exc))
            try:
                loaded = fresh.load_manifest_checkpoint()
            except Exception as exc:
                self.fail(str(exc))
            if active is None:
                self.fail("load_active returned None")
            self.assertEqual(active["fault"], armed["fault"])
            self.assertEqual(active["event"], armed["event"])
            self.assertEqual(loaded, (raw, receipt))

    def test_fb_r2_quarantine_rename_retries_a_sharing_violation(self) -> None:
        if os.name != "nt":
            self.skipTest("windows sharing")
        raw = b'{"version":1,"runs":[]}\n'
        with TemporaryDirectory() as temp_dir:
            paths, store = self._store(temp_dir)
            receipt = store.create_manifest_backup(raw)
            manifest_path = _backup_dir(paths, receipt) / "manifest.bin"
            manifest_path.write_bytes(raw[:8])
            handle = open(manifest_path, "rb")

            def release() -> None:
                time.sleep(0.05)
                handle.close()

            threading.Thread(target=release, daemon=True).start()
            try:
                try:
                    again = store.checkpoint_manifest(raw)
                except Exception as exc:
                    self.fail(str(exc))
            finally:
                if not handle.closed:
                    handle.close()
            self.assertEqual(again, receipt)
            try:
                restored = store.read_manifest_backup(receipt)
            except Exception as exc:
                self.fail(str(exc))
            self.assertEqual(restored, raw)
            self.assertEqual(len(_quarantine_dirs(paths)), 1)

        with TemporaryDirectory() as temp_dir:
            paths, store = self._store(temp_dir)
            receipt = store.create_manifest_backup(raw)
            backup = _backup_dir(paths, receipt)
            manifest_path = backup / "manifest.bin"
            manifest_path.write_bytes(raw[:8])
            handle = open(manifest_path, "rb")
            try:
                with patch.object(runtime_state, "ATOMIC_REPLACE_RETRY_S", 0.05):
                    try:
                        store.checkpoint_manifest(raw)
                    except ValueError as exc:
                        if str(exc) != "invalid_lifecycle_manifest_backup":
                            self.fail(str(exc))
                    except Exception as exc:
                        self.fail(str(exc))
                    else:
                        self.fail("invalid_lifecycle_manifest_backup not raised")
                self.assertTrue(backup.is_dir())
                self.assertEqual(manifest_path.read_bytes(), raw[:8])
            finally:
                handle.close()


class Fb305aDoctorQuarantineTest(unittest.TestCase):
    def test_fb_305a_doctor_reports_manifest_backup_quarantined(self) -> None:
        self.assertIsNotNone(doctor_module, "dayz_mcp.doctor is not implemented")
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runtime = root / "runtime"
            runtime.mkdir()
            scan_root = root / "launchers"
            scan_root.mkdir()
            paths = RuntimePaths(
                runtime,
                runtime / "audit",
                runtime / "coordination.json",
                runtime / "runs.json",
            )
            store = LifecycleRecoveryFaultStore(
                paths, utc_now_fn=lambda: "2026-07-22T00:00:00Z"
            )
            raw = b'{"version":1,"runs":[]}\n'
            receipt = store.create_manifest_backup(raw)
            (_backup_dir(paths, receipt) / "manifest.bin").write_bytes(b"")
            store.checkpoint_manifest(raw)
            self.assertEqual(len(_quarantine_dirs(paths)), 1)

            def snapshot(_names: list[str]) -> dict[str, object]:
                return {"known": True, "processes": []}

            sources = doctor_module.DoctorSources(
                claude_config=lambda: (0, CLAUDE_GOOD),
                codex_config=lambda: (0, CODEX_GOOD),
                listener_pid=lambda port: 700 if port == 8765 else None,
                process_argv=lambda pid: (
                    daemon_argv(DAEMON_GOOD) if pid == 700 else None
                ),
                daemon_status=lambda port, keyfile: clean_status(),
                process_snapshot=snapshot,
                process_identity=lambda pid: {
                    "error": "process_not_found",
                    "exit_code": 4,
                },
                runtime_paths=paths,
                scan_roots=(scan_root,),
                expected_command="C:\\Python\\python.exe",
            )
            payload, exit_code = doctor_module.execute(sources)
            self.assertEqual(exit_code, 0)
            quarantined = [
                item
                for item in payload["findings"]
                if item["code"] == "MANIFEST_BACKUP_QUARANTINED"
            ]
            self.assertEqual(len(quarantined), 1)
            self.assertEqual(quarantined[0]["severity"], "WARN")
            self.assertEqual(quarantined[0]["count"], 1)
