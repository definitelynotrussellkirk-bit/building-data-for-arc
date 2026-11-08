"""Generator for arc_puzzle_bank_third21:M16.

Canonical rule: sort the nonzero objects by Manhattan distance between each
bounding-box center and the full-grid center, then by object size and reading
order; recolor the first object to 8.  Normal draws make the three Manhattan
scores distinct so the lesson teaches the distance rule rather than its
fallback tie-break.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a16e387b682a"
VERSION = "3.0.0"  # Canonical Manhattan geometry, honest axes, strict checker.
TASK_ID = "a16e387b682a"
RULE_HASH = "f329ca8c8480"

SUMMARY = (
    "A 0-background grid contains exactly three separated solid 2x2 objects "
    "in distinct non-cyan colors. Compute Manhattan distance from each "
    "object's bounding-box center to the full-grid center, choose the unique "
    "closest object, and recolor all four of its cells to color 8."
)

INVARIANTS = [
    "background is 0 and input color 8 is absent",
    "exactly three solid 2x2 4-connected objects in distinct colors",
    "objects are separated by at least one background cell in all directions",
    "the three canonical Manhattan center-distance scores are distinct",
]

DEGENERATE_TEXTURES = ("no_blobs", "single_blob", "tied_distances")

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 9..13", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "difficulty-aware 9..13", "valid": "8..14"},
    "target_rank": {
        "type": "int",
        "default": "sample_index cycle 0..2",
        "valid": "0..2",
        "description": "reading-order rank of the unique closest object",
    },
}


def _canonical_score(h: int, w: int, top: int, left: int) -> int:
    """Canonical doubled-coordinate Manhattan score for a 2x2 bbox."""
    return abs((2 * top + 1) - (h - 1)) + abs((2 * left + 1) - (w - 1))


def _separated(a: tuple[int, int], b: tuple[int, int]) -> bool:
    """Whether two 2x2 top-left anchors have a full one-cell moat."""
    return abs(a[0] - b[0]) > 2 or abs(a[1] - b[1]) > 2


def _draw_dimension(ctx, label: str, default_bounds: tuple[int, int], overrides) -> int:
    # Explicit overrides must survive the complete declared boundary range in
    # every difficulty band; ordinary draws retain band-specific curricula.
    bounds = (8, 14) if overrides.get(label) is not None else default_bounds
    return ctx.draw_int(label, *bounds)


def _choose_layout(rng, h: int, w: int, target_rank: int) -> list[tuple[int, int]]:
    """Choose three anchors with distinct scores and requested target rank."""
    positions = [(r, c) for r in range(h - 1) for c in range(w - 1)]
    rng.shuffle(positions)

    for target in positions:
        target_score = _canonical_score(h, w, *target)
        before = [
            p
            for p in positions
            if p < target
            and _canonical_score(h, w, *p) > target_score
            and _separated(p, target)
        ]
        after = [
            p
            for p in positions
            if p > target
            and _canonical_score(h, w, *p) > target_score
            and _separated(p, target)
        ]
        rng.shuffle(before)
        rng.shuffle(after)

        if target_rank == 0:
            pair_source = combinations(after, 2)
        elif target_rank == 2:
            pair_source = combinations(before, 2)
        else:
            pair_source = ((a, b) for a in before for b in after)

        for first, second in pair_source:
            first_score = _canonical_score(h, w, *first)
            second_score = _canonical_score(h, w, *second)
            if first_score == second_score or not _separated(first, second):
                continue
            anchors = sorted((target, first, second))
            if anchors.index(target) == target_rank:
                return anchors

    raise ValueError(
        f"no valid three-object layout for {h}x{w} with target_rank={target_rank}"
    )


def _components(grid) -> list[dict]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[dict] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            for rr, cc in queue:
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            out.append(
                {
                    "color": color,
                    "cells": set(cells),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return out


def _analysis(grid) -> tuple[list[dict], list[int]]:
    h, w = len(grid), len(grid[0])
    parts = sorted(_components(grid), key=lambda obj: obj["bbox"][:2])
    scores = [
        abs((obj["bbox"][0] + obj["bbox"][2]) - (h - 1))
        + abs((obj["bbox"][1] + obj["bbox"][3]) - (w - 1))
        for obj in parts
    ]
    return parts, scores


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or ambiguous lessons for the canonical rule."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["empty or non-grid input"]
    h, w = len(grid), len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["ragged grid"]

    errs: list[str] = []
    flat = [value for row in grid for value in row]
    if any(not isinstance(value, int) or isinstance(value, bool) for value in flat):
        errs.append("grid contains a non-integer color")
        return errs
    if any(value < 0 or value > 9 for value in flat):
        errs.append("grid contains a color outside 0..9")
    if 8 in flat:
        errs.append("input already contains output color 8")

    parts, scores = _analysis(grid)
    if len(parts) != 3:
        errs.append(f"expected exactly 3 nonzero objects, found {len(parts)}")
        return errs

    colors = [obj["color"] for obj in parts]
    if len(set(colors)) != 3:
        errs.append(f"object colors are not distinct: {colors}")

    for index, obj in enumerate(parts):
        r1, c1, r2, c2 = obj["bbox"]
        expected = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
        if (r2 - r1 + 1, c2 - c1 + 1) != (2, 2) or obj["cells"] != expected:
            errs.append(f"object {index} is not a solid 2x2 block")

    for first, second in combinations(parts, 2):
        if any(
            max(abs(r1 - r2), abs(c1 - c2)) <= 1
            for r1, c1 in first["cells"]
            for r2, c2 in second["cells"]
        ):
            errs.append("distinct objects touch or lack a one-cell moat")
            break

    if len(set(scores)) != 3:
        errs.append(f"canonical Manhattan scores are not distinct: {scores}")
    return errs


def observe_overrides(grid) -> dict[str, int]:
    """Recover exact semantic axes from a valid returned input grid."""
    parts, scores = _analysis(grid)
    if len(parts) != 3 or not scores:
        raise ValueError("target_rank is undefined outside the valid three-object grammar")
    winner = min(range(3), key=lambda index: (scores[index], 4, *parts[index]["bbox"][:2]))
    return {"target_rank": winner}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    effective_overrides = dict(overrides)
    if effective_overrides.get("target_rank") is None:
        # Downstream lessons consume consecutive sample indices. Cycling the
        # target's reading-order rank guarantees that every three-demo window
        # rebuts a fixed-position shortcut without sacrificing replayability.
        effective_overrides["target_rank"] = sample_index % 3
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture)
    if texture is not None:
        raise ValueError(f"unknown texture override: {texture!r}")

    if difficulty == "easy":
        h_bounds, w_bounds = (9, 10), (9, 10)
    elif difficulty == "hard":
        h_bounds, w_bounds = (12, 14), (12, 14)
    else:
        h_bounds, w_bounds = (10, 12), (10, 12)

    h = _draw_dimension(ctx, "grid_h", h_bounds, overrides)
    w = _draw_dimension(ctx, "grid_w", w_bounds, overrides)
    target_rank = ctx.draw_int("target_rank", 0, 2)
    colors = ctx.draw_distinct_colors("blob_colors", n=3, exclude=(0, 8))
    anchors = _choose_layout(ctx.draw_rng("layout"), h, w, target_rank)

    grid = full_grid(h, w, 0)
    for color, (top, left) in zip(colors, anchors):
        for r in range(top, top + 2):
            for c in range(left, left + 2):
                grid[r][c] = color
    return grid


def _draw_from_degenerate(name: str):
    grid = full_grid(10, 10, 0)
    if name == "no_blobs":
        return grid
    if name == "single_blob":
        for r in range(4, 6):
            for c in range(4, 6):
                grid[r][c] = 4
        return grid
    if name == "tied_distances":
        # The first two objects have the same canonical minimum score.
        for color, top, left in ((4, 3, 2), (6, 3, 6), (2, 7, 4)):
            for r in range(top, top + 2):
                for c in range(left, left + 2):
                    grid[r][c] = color
        return grid
    raise ValueError(f"unknown degenerate texture: {name!r}")
