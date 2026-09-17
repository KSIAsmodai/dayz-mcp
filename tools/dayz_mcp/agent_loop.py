"""Small-model loop helpers: next_step may only name public MCP tools.

Flash-Next / ~8B callers copy tool names from error text. Naming an internal
method (lifecycle_status) or a tool that is not in the exposed registry
dead-ends the loop. This module is the single allowlist those recipes use.
"""

from __future__ import annotations

# Tools that exist on the standard public catalog and are safe to name in
# error recipes. Keep this list a subset of build_app() registrations.
PUBLIC_NEXT_TOOLS = frozenset(
    {
        "bridge_status",
        "dayz_knowledge_find",
        "dayz_knowledge_prepare",
        "dayz_knowledge_show",
        "dayz_knowledge_status",
        "dayz_test_close",
        "dayz_test_run",
        "dayz_test_stop",
        "object_inspect",
        "pipeline_feedback",
        "pipeline_inbox",
        "query_player_state",
        "session_acquire_wait",
        "session_heartbeat",
        "session_release",
        "session_status",
        "wait_for",
    }
)


def next_step(tool: str) -> str | None:
    """Return tool if it is safe to name; otherwise None."""
    if tool in PUBLIC_NEXT_TOOLS:
        return tool
    return None


def with_next_step(message: str, tool: str) -> str:
    """Append next_step=<public tool> or leave the message unchanged."""
    name = next_step(tool)
    if name is None:
        return message
    token = f"next_step={name}"
    if token in message:
        return message
    return f"{message}; {token}"
