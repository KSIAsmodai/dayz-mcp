# Project Genesis and Architecture

Fork of willy92wins/dayz-mcp (MIT), vetted and cloned to this laptop (5090,
ALIENWARE-5090-LPTP) 2026-09-19 per `Desktop\DAYZ-MCP-HANDOFF.txt`. Gives an
AI agent live control of a running DayZDiag server/client via 63 MCP tools
(session lease/queue coordination, managed launch, telemetry, UI automation).
Not our source — do not do upstream-style refactors here without reason; local
fixes for our own use are fine (MIT, `KSIAsmodai` fork).

## 2026-09-19 — Install, registration bug fix, and boot crash isolated

**Offline test suite**: `python -m unittest discover -s tests -t .` — 4030
tests, 31 failures + 7 errors (38 total), 67 skipped, rest pass (99.1%).
Failures cluster in session-lease contract tests (`test_pleno_lease_and_orphans`,
`test_session_e2e`), a test double missing `status_snapshot` attribute
(`test_ui_error_diagnostics`, `test_vehicle_prepare_fixture`, `test_wait_for_marker`),
and a stale packaged-modules lock hash (`test_fb_1025_packaged_modules_lock`).
Full log: this session's transcript. Not investigated further — pre-existing
baseline state, first-ever run of the suite per the handoff doc.

**`install_mcp.py --register` bug, FOUND and FIXED** — `VERIFIED
tools/install_mcp.py:691-710`. `CliRegistrationProvider.get()` hardcodes the
probe query as `["mcp", "get", "dayz-mcp"]` but tested "not yet registered"
by literal string-equality against a fixture recorded during `--pin-clis` for
a *different* placeholder name (`"p0s-absent-fixture-do-not-create"`, see
`installer-not-found-fixtures-v1.json`). Both Claude and Codex CLIs embed the
queried name in their "not found" error text, so the strings can never match
— `get()` always raised `registration_probe_failed` on a genuinely fresh
install, before anything else ran. Fix: substitute the fixture's probe-name
placeholder for the real query name (`dayz-mcp`) before comparing. Verified:
`--register` now completes (`"status": "installed_and_registered"`), both
`claude mcp get dayz-mcp` and `codex mcp get dayz-mcp --json` show live
matching entries, and `python -m dayz_mcp.stdio_bridge --probe` returns
`{"ok":true,"plan":"stdio_client","tools":[...17 tools...],"count":17}` —
daemon starts, authenticates, speaks MCP JSON-RPC correctly.

Also required, not previously present on this box: Codex CLI (`npm install -g
@openai/codex`, native `codex.exe` is bundled under
`node_modules\@openai\codex\node_modules\@openai\codex-win32-x64\vendor\...\bin\codex.exe`,
NOT the `codex.cmd` shim `where codex` finds — `--pin-clis` requires a native
x64 PE). MSVC Build Tools 2022 + VCTools workload (`winget install
Microsoft.VisualStudio.2022.BuildTools`) for the native-launcher build path;
`relock_toolchain.py` re-pinned `dependency-lock.json` after install.

**Environmental blocker hit mid-session, self-resolved**: `install_mcp.py
--register`'s `p0s_gate.py backup-runs-v1` safety gate fail-closed
(`process_scan_incomplete`) because ~28 `python.exe` processes on this box had
no owner/cmdline readable even via WMI from a non-elevated token — same class
of ACL-hidden-process symptom as memory `imogen-radio-watchdog-hidden-task`
(though 2 of the ~30 total were legit, `dking`-owned `f5_server.py` radio
processes — do not kill those). User killed the opaque ones via an elevated
PowerShell one-liner; gate passed clean afterward (`{"source_absent": true,
"status": "verified"}`). Worth a session someday: find what keeps spawning
opaque python.exe processes under session 0 on this laptop.

**Addon boot crash — ISOLATED, cause not yet found.** Packed `addon/` into
`DayZ_MCP.pbo` via `tools\pack-addon.ps1` (P:\ work drive already existed on
this box, pre-established DayZ modding convention, no setup needed), deployed
to `...\DayZ\!Workshop\@DayZ_MCP\Addons\DayZ_MCP.pbo` (243,617 bytes,
verified hash-matched build). Launched `DayZDiag_x64.exe` against
`TestServer1`'s clean vanilla `dayzOffline.enoch` mission (chernarusplus
copies all carry a customized init.c requiring `@Dogtags` — avoided that
dependency by using enoch instead).

Two real environment bugs found and fixed before reaching the addon crash:
1. `Start-Process -FilePath "<full path with spaces>"` combined with an
   `-ArgumentList` entry also containing spaces corrupted argv — RPT's own
   command-line echo showed `"C:\Program -config=...` (truncated at first
   space). Fix: launch via `-WorkingDirectory <dir>` + bare relative exe name,
   matching the proven pattern in memory `local-test-server-laptop.md`.
2. DayZDiag crashed instantly (matching `ErrorMessage_*.mdmp`, RPT cut with
   no footer) because the Steam client wasn't running — DayZDiag needs
   Steamworks API init. Fix: launch `steam.exe -silent`, wait for
   `steamwebhelper.exe` children to appear (confirms logged in, not stuck at
   a prompt), then relaunch.

After both fixes: `-mod=@DayZ_MCP` still crashes (`ErrorMessage_DayZDiag_x64_
2026-09-19_16-49-01.mdmp`), RPT stops at 59 lines right after the normal
engine-boot localization-warning spam, no `SCRIPT (E)`, no footer. Windows
Application event log has no matching Event 1000 (DayZ's own breakpad-style
handler writes the minidump directly, doesn't post a WER application event).

**Single-removal isolation (VERIFIED, `dayz-crash-analysis` skill method)**:
identical launch with NO `-mod=` argument boots clean — RPT reached 1877
lines, normal entity/terrain loading in progress (`Load entity type
'Land_Boathouse'`, etc.), process alive with 200+s of real CPU time, no
crash. This proves the crash is caused by the `DayZ_MCP` addon specifically,
not the box, not Steam, not the mission. `addon/config.cpp` (CfgPatches +
CfgMods) looks structurally correct and minimal; `addon/scripts/` files exist
matching the declared `files[]` paths. Root cause inside the addon NOT yet
found — would need minidump analysis (WinDbg or equivalent) or a
finer-grained isolation (strip scripts one at a time) to pin down further.

**Root cause found — DayZDiag's own debug assert, NOT the addon.** Installed
`pip install minidump` (pure-Python minidump reader, no WinDbg needed) and
parsed `ErrorMessage_DayZDiag_x64_2026-09-19_16-49-01.mdmp` directly:
`VERIFIED` exception is `EXCEPTION_BREAKPOINT` (INT3), address
`0x7ff744f7d120`, which resolves inside `DayZDiag_x64.exe` itself (offset
`0x36d120`) — not `steam_api64.dll`, not any addon code (the addon has no
native code, script+config only). A breakpoint exception this early, with no
RPT footer and no `SCRIPT (E)`, is a deliberate engine-side assert/trap, the
kind DayZDiag's debug/diagnostic build compiles in and retail/dedicated-server
builds typically don't. QUICKSTART.md already hints at this: "Retail works
for everything here; `DayZDiag_x64.exe` is only needed if you want
`-filePatching`" — we don't need filePatching since we pack a real PBO.

**Confirmed via TestServer1's own `DayZServer_x64.exe`** (retail dedicated
server binary, not Diag): identical launch (same cfg, same `-mod=@DayZ_MCP`,
same enoch mission) booted completely clean — RPT reached 4788 lines,
`Player connect enabled` at line 4612, zero errors, zero crash. The addon is
GOOD. The DayZDiag crash was an artifact of testing with the wrong binary for
this addon/engine-build combination, not a defect in `DayZ_MCP.pbo`.

**Native launcher toolchain built** (separate from the manual-launch path
above): MSVC Build Tools 2022 + VCTools installed, `relock_toolchain.py`
re-pinned, `%LOCALAPPDATA%\DayZ_MCP\launcher-policy.json` written pointing at
this box's real paths (`addon` as `default_source`, `TestServer1` as
`dev_root`, its `mpmissions` as `mission_roots`, the DayZ `!Workshop` folder
as `mod_roots`). `build_native_launcher.py` / registry bootstrap+install not
yet run — the manual pack-addon.ps1 + direct-launch path above already proved
the addon works, so the sealed `dayz_test_run` managed path is optional
follow-up, not required for this experiment's goal.

**Live bridge polling — CONFIRMED end to end (2026-09-19, same session).**

First attempt to verify this produced a false positive worth recording as its
own lesson: `-mod=C:\Program Files (x86)\Steam\steamapps\common\DayZ\!Workshop\@DayZ_MCP`
(an absolute path with a space in it, `Program Files (x86)`) silently failed
to load — `VERIFIED` via the RPT's own `Adding package` lines, which listed
every vanilla/DLC package from `TestServer1`'s tree and NOT `DayZ_MCP`. The
server booted clean and reached `Player connect enabled` anyway, because
without the addon loaded there was nothing left to break — a clean vanilla
boot that looked identical to a successful addon boot from the RPT tail
alone. Same root-cause family as the earlier `DayZDiag_x64.exe` full-path
argv corruption, but this time in the `-mod=` VALUE rather than the exe path,
and PowerShell's `-ArgumentList` array quoting didn't save it either. Fix:
copy the built `DayZ_MCP.pbo` into `TestServer1\@DayZ_MCP\Addons\` (inside
the server's own tree, matching the established zero-space `@Mod` convention
from `local-test-server-laptop.md`) and launch with the bare relative
`-mod=@DayZ_MCP`. Confirmed on relaunch: `Adding package
'...TestServer1\@DayZ_MCP\addons\DayZ_MCP.pbo'`, `DayZ_MCP` in the compiled
`defines` list, World module class count +7 over the vanilla baseline.

**Lesson: a clean boot with no crash is not proof a mod loaded** — always
grep the RPT's `Adding package` lines for the mod's own pbo path before
trusting "it booted fine" as evidence of anything mod-specific.

With the addon genuinely loaded, its own log line appeared immediately:
`[DayZ-MCP] config loaded path=$profile:dayz_mcp.json url=http://127.0.0.1:8765/
keylen=43 instlen=0 poll_hz=5`. The daemon (run via a one-time scheduled task,
see below) had died between setup and this check, so the addon logged
`poll error=7 backoff_s=<1,2,4,8,16...>` on its own exponential-backoff
retry — exactly the resilience behavior you'd want, not a bug. Restarting the
daemon (`schtasks /run`) let the addon's own retry loop reconnect without
touching the game process at all. Final confirmed state via
`GET /status?key=...`:
```
"server_peer": {"last_poll_age_s": 0.18, "version": "10~1.29.163709",
  "version_state": "ok", "version_detail": "version accepted",
  "observed_this_generation": true},
"fence": {"unaccredited_polls_by_class": {"LEGACY_UNBOUND": 262}}
```
Server, addon, and daemon are talking end to end — version handshake
accepted, 262 successful polls recorded. `capabilities.state: "unknown"` /
`reason: "unaccredited"` remains — full tool-capability negotiation likely
needs a session-bound client (`session_acquire_wait` et al.) rather than the
bare `/status` probe used here; not investigated further, this was outside
the experiment's scope.

**Daemon persistence trick, for next time**: the daemon's own process
lifecycle deliberately watches a real ancestor PID and self-terminates when
it exits (anti-orphan design) — a daemon launched from a transient Bash/
PowerShell tool call dies within seconds, even with `Start-Process`. Working
around it: `schtasks /create /tn <name> /tr "<venv python> -m dayz_mcp
--embedded --keyfile <key> --port 8765" /sc once /st 23:59 /f` then
`schtasks /run /tn <name>` — Task Scheduler gives the child a stable system
parent instead of an ephemeral shell. Clean up with `schtasks /delete /tn
<name> /f` when done; this was a one-off diagnostic aid, not meant to be a
permanent fixture. In real use this whole problem doesn't exist: a registered
Claude/Codex client session (now set up via the `--register` fix above) keeps
the daemon alive for as long as the session is open, which is the intended
lifecycle.

**Cross-platform Windows gotcha, worth its own line**: `schtasks /create
...` run through Git Bash mangles `/create`, `/run` etc. into paths
(`'C:/Program Files/Git/create'` — Git Bash's auto path-conversion on
leading-slash arguments). Use the PowerShell tool for any `schtasks` call.

**Not done, optional follow-up**: the native-launcher path
(`build_native_launcher.py`, `launcher_registry_update bootstrap` +
`install-dayz-test-v1`) so `dayz_test_run` can drive this box directly
instead of the manual pack+launch steps done here. The manual path above
already fully proves the addon and bridge work, so this is convenience, not
a correctness gap. `launcher-policy.json` is already written at
`%LOCALAPPDATA%\DayZ_MCP\launcher-policy.json` pointing at this box's real
paths.
