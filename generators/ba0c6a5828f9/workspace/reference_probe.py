"""Independent geometry helpers for ba0c6a5828f9 reviewer tests.

This module is supplementary authoring evidence.  The selected Racket program
remains label authority; these functions deliberately do not import helpers from
the production generator under review.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
from typing import Sequence

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "ba0c6a5828f9"
ROOT = find_root(__file__)
Grid = list[list[int]]


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or ROOT / "generators" / TASK_ID / "generator.py")
    spec = importlib.util.spec_from_file_location("reviewed_ba0c6a5828f9", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    return _canonical_pairs(TASK_ID, root=ROOT)


def pivot(grid: Sequence[Sequence[int]]) -> tuple[int, int]:
    hits = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if len(hits) != 1:
        raise ValueError(f"expected one pivot, found {len(hits)}")
    return hits[0]


def markers(grid: Sequence[Sequence[int]]) -> list[tuple[int, int]]:
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]


def orbit_all(point: tuple[int, int], center: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    r, c = point
    pr, pc = center
    dr, dc = r - pr, c - pc
    return (
        (pr + dr, pc + dc),
        (pr + dc, pc - dr),
        (pr - dr, pc - dc),
        (pr - dc, pc + dr),
    )


def intended_output(grid: Sequence[Sequence[int]], *, center: tuple[int, int] | None = None,
                    require_full_orbit: bool = False) -> Grid:
    """Independent mirror of the written rule and two named shortcuts."""
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    center = pivot(grid) if center is None else center
    for point in markers(grid):
        orbit = orbit_all(point, center)
        if require_full_orbit and any(not (0 <= r < h and 0 <= c < w) for r, c in orbit):
            continue
        for r, c in orbit:
            if 0 <= r < h and 0 <= c < w:
                out[r][c] = 1
    return out


def geometric_center_rival(grid: Sequence[Sequence[int]]) -> Grid:
    return intended_output(grid, center=(len(grid) // 2, len(grid[0]) // 2))


def full_orbits_only_rival(grid: Sequence[Sequence[int]]) -> Grid:
    return intended_output(grid, require_full_orbit=True)


def has_clipped_marker(grid: Sequence[Sequence[int]]) -> bool:
    h, w = len(grid), len(grid[0])
    center = pivot(grid)
    return any(
        any(not (0 <= r < h and 0 <= c < w) for r, c in orbit_all(point, center))
        for point in markers(grid)
    )


def observed_profile(grid: Sequence[Sequence[int]]) -> str | None:
    h, w = len(grid), len(grid[0])
    center = pivot(grid)
    off_center = center != (h // 2, w // 2)
    clipped = has_clipped_marker(grid)
    if off_center and clipped:
        return "mixed"
    if off_center:
        return "off_center"
    if clipped:
        return "clipped"
    if h == w and h in (7, 9) and 2 <= len(markers(grid)) <= 3:
        return "canonical"
    return None
