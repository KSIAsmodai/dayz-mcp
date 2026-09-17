# fb-20260915-143332-00bb + fb-20260915-104637-1004 — file-only (PROPOSAL)

TOUCH who=Auditor what=propose DIFF/PR estado=proposed

- tickets: `fb-20260915-143332-00bb`, `fb-20260915-104637-1004`
- author: Auditor (Guillermo / dayz-mcp)
- status: **PROPOSED** pending Guillermo OK + Codex review
- branch: `auditor/file-only-00bb-1004`
- do not merge, do not resolve the inbox tickets, do not edit GATES.md / triage.jsonl / unrelated tickets (`e4be` / `8bc6` / `ba11`)

## Intent

1. **00bb** — `player_teleport` called client `vehicle_telemetry` before the occupant precheck without asking whether the client peer was probing. With no client the wait timed out and the error named `vehicle_telemetry`, not `player_teleport`.
2. **1004** — tool copy told agents to tear down `vehicle_get_in_client` with `object_delete`, but `object_delete` only accepts `object_id` and that id does not survive the run. Seated-transport delete needs a warning, not a new pos+type API.

## What changed

- `tools/dayz_mcp/server.py`
  - `_client_peer_probeable` / `_runtime_client_peer_probeable` reuse `_peer_is_live` (same rule as `_target_peer_down`).
  - `player_teleport` runs the `occupant_client_seated` telemetry precheck only when the client peer is probeable. Missing, stale, unbound, or unreadable status **fails open** to on-foot teleport. Enforce still refuses a client-seated occupant.
  - Tool descriptions on `vehicle_get_in_client`, `player_teleport`, and `object_delete` warn that `object_id` does not survive the run and that deleting a seated transport needs care. No pos+type delete API.
- Host-safe tests: `tools/tests/test_fb_00bb_1004.py` plus extensions in `test_player_teleport.py`, `test_precondition_docs.py`, `test_fb_81f3.py`, `test_wire_coercion_census.py`.

## What was not changed (1004 guard)

A refuse-while-seated `object_delete` guard is patternable (same telemetry precheck as teleport) but would remove the **sanctioned teardown**: delete-while-seated ejects (`docs/VEHICLE_TESTING.md`, `OK_FORCED_DELETE`). There is no get-out after `vehicle_get_in_client`. This PR keeps delete open and tightens copy. HANDOFF allowed description-only.

## How to verify

From `tools/`:

```text
python -m pytest tests/test_fb_00bb_1004.py tests/test_player_teleport.py tests/test_precondition_docs.py tests/test_fb_81f3.py tests/test_wire_coercion_census.py::WireCoercionTests::test_skip_clearance_one_bypasses_the_probe -q
```

No DayZ launch, Diag, AddonBuilder, or Steam.

## Residual risks

- Fail-open teleport when the client peer is down: a seated occupant is not seen in Python. Enforce still returns `occupant_client_seated`.
- `object_delete` still has no occupant guard and still cannot recover a fixture by pos+type after the run. A stale `object_id` deletes nothing (`deleted=0`) or the wrong object.
- `VEHICLE_TESTING.md` teardown story is unchanged (still delete-while-seated).
- Inbox tickets are not resolved here.

## Out of scope

- GATES.md, triage.jsonl, e4be / 8bc6 / ba11
- Enforce / PBO / in-game / Steam
- New delete verbs or arguments
