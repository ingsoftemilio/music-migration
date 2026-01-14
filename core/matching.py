from __future__ import annotations

from typing import Optional

from core.models import TrackRef


def pick_best_match_simple(
    source: TrackRef,
    candidates: list[TrackRef],
) -> tuple[Optional[TrackRef], list[TrackRef], Optional[str]]:
    """
    Very simple starter:
    - If exactly one candidate, pick it
    - If none, return reason
    - If many, return ambiguous
    """
    if not candidates:
        return None, [], "no_candidates"

    if len(candidates) == 1:
        return candidates[0], [], None

    # ambiguous for now (we’ll add fuzzy scoring next)
    return None, candidates[:5], "ambiguous"