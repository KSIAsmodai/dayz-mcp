"""Host-safe peer liveness predicates.

`_peer_is_live` / `_client_peer_probeable` used to live in server.py. They are
pure status-shape checks and must stay importable without the Windows stack
(fb-20260915-143332-00bb).
"""

from __future__ import annotations

# A peer with last_poll_age_s >= this value is not live (game polls ~0.2s).
PEER_STALE_S = 15.0


def peer_is_live(peer: object) -> bool:
    if not isinstance(peer, dict):
        return False
    bind = peer.get("binding_state")
    if bind == "LEGACY_UNBOUND":
        return False
    if bind in {None, ""}:
        age = peer.get("last_poll_age_s")
    elif bind != "BOUND":
        return False
    else:
        age = peer.get("bound_last_poll_age_s")
    return isinstance(age, (int, float)) and not isinstance(age, bool) and age < PEER_STALE_S


def client_peer_probeable(status: object) -> bool:
    """True when the client peer is live enough for a client precheck.

    Same liveness rule as `peer_is_live`. A missing or stale client must not
    enqueue `vehicle_telemetry` (that timeout names the precheck verb, not
    the caller). fb-20260915-143332-00bb.
    """
    if not isinstance(status, dict):
        return False
    return peer_is_live(status.get("client_peer"))
