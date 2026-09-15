"""Shared AddonBuilder ``-packonly`` predicate.

AddonBuilder's binarize pass uses ``-addon=P:`` and dies if any ``config.cpp``
under ``P:\\`` fails to parse (fb-20260915-005408-bcd8). The worker, the
native launcher, and ``tools/pack-addon.ps1`` therefore pass ``-packonly``
when the source tree has no binarizable assets.
"""

from __future__ import annotations

from pathlib import Path

BINARIZABLE_SUFFIXES = frozenset({".p3d", ".paa", ".rvmat"})


def has_binarizable_assets(source: str | Path) -> bool:
    """True when ``source`` contains a ``.p3d``, ``.paa`` or ``.rvmat`` file."""
    return any(
        path.suffix.casefold() in BINARIZABLE_SUFFIXES
        for path in Path(source).rglob("*")
        if path.is_file()
    )


def should_pack_only(source: str | Path, *, pack_only: bool = False) -> bool:
    """Same rule as ``dayz_test_worker``: explicit flag or no binarizable assets."""
    return bool(pack_only) or not has_binarizable_assets(source)


def addon_builder_packonly_args(
    source: str | Path, *, pack_only: bool = False
) -> tuple[str, ...]:
    """Extra AddonBuilder flags so ``-packonly`` is passed when appropriate."""
    if should_pack_only(source, pack_only=pack_only):
        return ("-packonly",)
    return ()
