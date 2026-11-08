"""Generator for arc_puzzle_bank_21_set16_bundle:easy_p05.

Rule: fill a zero cell only when its immediate vertical neighbours are the
same nonzero color.

The pair schedule is lesson-aware.  Even sample indices add horizontal and
mismatched vertical counterexamples; odd sample indices add a longer vertical
span and an already-filled vertical triple.  Because ``run_one`` uses
sequential sample indices, every three-demonstration episode contains all four
shortcut-rebutting counterexample types.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "441d3a994cf6"
VERSION = "2.0.0"  # add a lesson-aware counterexample curriculum and honest axes
TASK_ID = "441d3a994cf6"
RULE_HASH = "beb0f3a5a810"
SUMMARY = (
    "Fill only zero cells whose immediate vertical neighbours are equal and "
    "nonzero; nearby horizontal, mismatched, longer-gap, and filled motifs are "
    "negative evidence."
)

INVARIANTS = [
    "background is 0",
    "each returned grid contains one to four matching vertical one-cell gaps",
    "every nonzero cell belongs to exactly one isolated positive or scheduled counterexample motif",
    "even and odd sample indices alternate complementary counterexample pairs",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 8..14",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 8..14",
        "valid": "8..14",
    },
    "gap_count": {
        "type": "int",
        "default": "difficulty-aware 1..4",
        "valid": "1..4",
    },
}

_TARGET = "target"
_HORIZONTAL = "horizontal_same"
_MISMATCH = "vertical_mismatch"
_LONG = "vertical_long_gap"
_FILLED = "vertical_filled_midpoint"


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return a deterministic, non-degenerate teaching input."""
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 8, 14)
    w = ctx.draw_int_diff("grid_w", 8, 14)
    gap_count = ctx.draw_int_diff("gap_count", 1, 4)
    rng = ctx.draw_rng("layout")

    distractors = (
        (_HORIZONTAL, _MISMATCH)
        if sample_index % 2 == 0
        else (_LONG, _FILLED)
    )
    motif_kinds = [*distractors, *([_TARGET] * gap_count)]

    for _ in range(256):
        placements = _place_motifs(motif_kinds, h, w, rng)
        if placements is None:
            continue
        grid = _paint_motifs(h, w, placements, rng)
        analysis = _analyze_grid(grid)
        expected = Counter({_TARGET: gap_count, distractors[0]: 1, distractors[1]: 1})
        if analysis["counts"] == expected and not _structure_errors(grid, analysis):
            return grid

    raise ValueError(
        "unable to place the requested isolated motifs without introducing "
        "an unintended vertical gap"
    )


def observe_overrides(grid) -> dict[str, int]:
    """Recover exact semantic-axis values from a returned grid."""
    return {"gap_count": _analyze_grid(grid)["counts"][_TARGET]}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed lessons while accepting every canonical input."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and nonempty"]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be ARC colors 0..9"]

    analysis = _analyze_grid(grid)
    errors = _structure_errors(grid, analysis)

    requested = None
    if isinstance(meta, dict):
        requested = meta.get("gap_count")
        if requested is None and isinstance(meta.get("overrides"), dict):
            requested = meta["overrides"].get("gap_count")
    if requested is not None and analysis["counts"][_TARGET] != int(requested):
        errors.append(
            f"gap_count requested {int(requested)}, observed "
            f"{analysis['counts'][_TARGET]}"
        )
    return errors


def _structure_errors(grid, analysis) -> list[str]:
    counts: Counter[str] = analysis["counts"]
    errors: list[str] = []
    target_count = counts[_TARGET]
    if not 1 <= target_count <= 4:
        errors.append(f"expected 1..4 fillable vertical gaps, got {target_count}")

    ambiguous = analysis["ambiguous_cells"]
    uncovered = analysis["uncovered_cells"]
    if ambiguous:
        errors.append(f"motif cells participate in multiple relations: {ambiguous[:6]}")
    if uncovered:
        errors.append(f"nonzero cells outside the lesson grammar: {uncovered[:6]}")

    distractor_counts = Counter(
        {kind: counts[kind] for kind in (_HORIZONTAL, _MISMATCH, _LONG, _FILLED)}
    )
    pure_canonical = not any(distractor_counts.values())
    scheduled_even = distractor_counts == Counter({_HORIZONTAL: 1, _MISMATCH: 1})
    scheduled_odd = distractor_counts == Counter({_LONG: 1, _FILLED: 1})
    if not (pure_canonical or scheduled_even or scheduled_odd):
        errors.append(
            "counterexamples must be absent (canonical form) or exactly one "
            "scheduled complementary pair"
        )
    return errors


def _place_motifs(kinds: list[str], h: int, w: int, rng):
    candidate_cache = {kind: _candidate_paths(kind, h, w) for kind in set(kinds)}
    # Harder footprints first; target copies fill the remaining isolated slots.
    priority = {_LONG: 0, _HORIZONTAL: 1, _FILLED: 2, _MISMATCH: 3, _TARGET: 4}
    ordered = sorted(enumerate(kinds), key=lambda item: (priority[item[1]], item[0]))

    for _ in range(64):
        blocked: set[tuple[int, int]] = set()
        chosen: dict[int, tuple[tuple[int, int], ...]] = {}
        failed = False
        for original_index, kind in ordered:
            candidates = list(candidate_cache[kind])
            rng.shuffle(candidates)
            path = next((candidate for candidate in candidates if not (set(candidate) & blocked)), None)
            if path is None:
                failed = True
                break
            chosen[original_index] = path
            blocked.update(_halo(path, h, w))
        if not failed:
            return [(kind, chosen[index]) for index, kind in enumerate(kinds)]
    return None


def _candidate_paths(kind: str, h: int, w: int) -> list[tuple[tuple[int, int], ...]]:
    if kind == _HORIZONTAL:
        return [
            tuple((r, c + dc) for dc in range(3))
            for r in range(h)
            for c in range(w - 2)
        ]
    length = 4 if kind == _LONG else 3
    return [
        tuple((r + dr, c) for dr in range(length))
        for r in range(h - length + 1)
        for c in range(w)
    ]


def _halo(path: Iterable[tuple[int, int]], h: int, w: int) -> set[tuple[int, int]]:
    return {
        (rr, cc)
        for r, c in path
        for rr in range(max(0, r - 1), min(h, r + 2))
        for cc in range(max(0, c - 1), min(w, c + 2))
    }


def _paint_motifs(h, w, placements, rng):
    grid = full_grid(h, w, 0)
    palette = list(range(1, 10))
    rng.shuffle(palette)
    target_index = 0
    for kind, path in placements:
        if kind == _TARGET:
            color = palette[target_index % 3]
            target_index += 1
            _set_many(grid, (path[0], path[-1]), (color, color))
        elif kind == _HORIZONTAL:
            _set_many(grid, (path[0], path[-1]), (palette[0], palette[0]))
        elif kind == _MISMATCH:
            _set_many(grid, (path[0], path[-1]), (palette[1], palette[2]))
        elif kind == _LONG:
            _set_many(grid, (path[0], path[-1]), (palette[0], palette[0]))
        elif kind == _FILLED:
            _set_many(grid, path, (palette[1],) * len(path))
        else:  # defensive: kinds are internal constants
            raise ValueError(f"unknown motif kind: {kind}")
    return grid


def _set_many(grid, cells, colors) -> None:
    for (r, c), color in zip(cells, colors):
        grid[r][c] = color


def _analyze_grid(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    motifs: list[tuple[str, tuple[tuple[int, int], ...]]] = []

    for r in range(1, h - 1):
        for c in range(w):
            above, here, below = grid[r - 1][c], grid[r][c], grid[r + 1][c]
            if here == 0 and above != 0 and above == below:
                motifs.append((_TARGET, ((r - 1, c), (r + 1, c))))
            elif here == 0 and above != 0 and below != 0 and above != below:
                motifs.append((_MISMATCH, ((r - 1, c), (r + 1, c))))

    for r in range(h):
        for c in range(1, w - 1):
            left, here, right = grid[r][c - 1], grid[r][c], grid[r][c + 1]
            if here == 0 and left != 0 and left == right:
                motifs.append((_HORIZONTAL, ((r, c - 1), (r, c + 1))))

    for r in range(h - 3):
        for c in range(w):
            endpoint = grid[r][c]
            if (
                endpoint != 0
                and grid[r + 1][c] == 0
                and grid[r + 2][c] == 0
                and grid[r + 3][c] == endpoint
            ):
                motifs.append((_LONG, ((r, c), (r + 3, c))))

    for r in range(h - 2):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or grid[r + 1][c] != color or grid[r + 2][c] != color:
                continue
            above_same = r > 0 and grid[r - 1][c] == color
            below_same = r + 3 < h and grid[r + 3][c] == color
            if not above_same and not below_same:
                motifs.append((_FILLED, ((r, c), (r + 1, c), (r + 2, c))))

    memberships: Counter[tuple[int, int]] = Counter()
    for _, cells in motifs:
        memberships.update(cells)
    nonzero = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    return {
        "counts": Counter(kind for kind, _ in motifs),
        "motifs": motifs,
        "ambiguous_cells": sorted(cell for cell, count in memberships.items() if count != 1),
        "uncovered_cells": sorted(nonzero - set(memberships)),
    }
