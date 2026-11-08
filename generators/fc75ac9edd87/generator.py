"""Generator for ARC task ``fc75ac9edd87``.

Two header rows form a query over the colored body objects:

* count color-1 cells in row 0: 1=left/right symmetry, 2=up/down
  symmetry, 3=both axes, 4=no axis symmetry;
* count color-2 cells in row 1: choose the first- or second-largest object
  among that symmetry class.

The selected object's bounding-box crop is returned as a cyan (8) mask.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fc75ac9edd87"
TASK_ID = GENERATOR_ID
RULE_HASH = "d042c4955bba"
VERSION = "4.0.0"  # restore code-4 branch; exact axes; semantic lesson contract

SUMMARY = (
    "Rows 0 and 1 encode a two-stage query. Count the color-1 cells in row 0 "
    "to select an exact symmetry class: 1=left/right only, 2=up/down only, "
    "3=both axes, and 4=no reflection symmetry. Count the color-2 cells in "
    "row 1 to select area rank 1 or 2. Filter the body objects to the requested "
    "class, sort them by decreasing area (top-left breaks ties), crop the "
    "ranked object to its bounding box, and recolor its occupied cells cyan (8)."
)

INVARIANTS = [
    "row 0 contains exactly 1..4 color-1 cells and no other nonzero color",
    "row 1 contains exactly 1..2 color-2 cells and no other nonzero color",
    "row 2 is an empty separator and every body color forms one 4-connected object",
    "the requested symmetry class has at least two objects with distinct areas",
    "at least one body object belongs to a different symmetry class",
    "the selected crop is nonrectangular, so its cyan mask contains both 0 and 8",
]

AXES = {
    "sym_code": {
        "type": "int",
        "default": "eight-step lesson schedule covering every code/rank pair",
        "valid": "1..4",
    },
    "rank": {
        "type": "int",
        "default": "eight-step lesson schedule covering every code/rank pair",
        "valid": "1..2",
    },
    "grid_h": {
        "type": "int",
        "default": "12-step schedule with canonical anchors and full 13..20 span",
        "valid": "13..20",
    },
    "grid_w": {
        "type": "int",
        "default": "12-step schedule with canonical anchors and full 16..24 span",
        "valid": "16..24",
    },
    "n_match": {
        "type": "int",
        "default": "12-step schedule",
        "valid": "2..3",
    },
    "n_distractor": {
        "type": "int",
        "default": "12-step schedule",
        "valid": "1..3",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
_ALLOWED_DIFFICULTIES = {None, "easy", "medium", "hard"}
_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))

# The first six dimension profiles are exact canonical dimensions. The tail
# spans every declared boundary while retaining the same two-header grammar.
_DIMENSION_SCHEDULE = (
    (13, 16), (14, 17), (14, 18),
    (13, 16), (14, 17), (14, 18),
    (15, 19), (16, 20), (17, 21),
    (18, 22), (19, 23), (20, 24),
)
_COUNT_SCHEDULE = (
    (3, 1), (2, 2), (3, 1), (2, 2), (3, 1), (2, 3),
    (3, 2), (2, 1), (3, 3), (2, 2), (3, 2), (2, 3),
)
_RANK_SCHEDULE = (1, 2, 1, 2, 2, 1, 2, 1)

# Exact-class, connected, nonrectangular polyominoes. Coordinates are normalized.
_ASYM_SHAPES = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 2)),
    ((0, 0), (0, 1), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (1, 1), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 3)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 4)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 3)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 1), (1, 4)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 3)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 4)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (2, 0)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 2), (1, 3)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (1, 4)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (2, 0)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 3), (2, 0)),
)
# 40 shapes

_ROW_SHAPES = (
    ((0, 0), (1, 0), (1, 1), (2, 0)),
    ((0, 1), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 0)),
    ((0, 2), (1, 0), (1, 1), (1, 2), (2, 2)),
    ((0, 0), (0, 1), (1, 0), (2, 0), (3, 0), (3, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (3, 0), (3, 1)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0)),
    ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (3, 0)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (3, 0), (4, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 2), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (2, 0), (3, 0), (4, 0), (4, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (3, 1), (4, 0), (4, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (3, 0), (3, 1), (3, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (2, 0), (2, 1), (2, 2), (2, 3)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (2, 0), (2, 1), (2, 2), (2, 3)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 2), (2, 0), (2, 1), (2, 2), (2, 3)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (3, 0), (4, 0), (4, 1), (4, 2)),
)
# 30 shapes

_COL_SHAPES = (
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 1), (1, 1), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (3, 1)),
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 4)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 1), (1, 3)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (3, 1), (4, 1)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 2), (1, 4)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 1), (1, 2), (1, 3)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (2, 2), (3, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3), (2, 0), (2, 3)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 2), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 3), (1, 4)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 2), (1, 4), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 4), (2, 0), (2, 4)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 1), (1, 2), (1, 3), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 1), (1, 3), (2, 1), (2, 3)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (2, 1), (2, 2), (2, 3)),
)
# 30 shapes

_BOTH_SHAPES = (
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
    ((0, 1), (1, 1), (2, 0), (2, 1), (2, 2), (3, 1), (4, 1)),
    ((0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (3, 0), (3, 1), (3, 2)),
    ((0, 0), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 3)),
    ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1), (2, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2), (3, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (3, 1), (4, 0), (4, 1), (4, 2)),
    ((0, 0), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 0), (2, 4)),
    ((0, 1), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 1), (2, 3)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (3, 0), (3, 1), (3, 2), (4, 1)),
    ((0, 2), (1, 2), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (3, 2), (4, 2)),
)
# 15 shapes


_SHAPES_BY_CLASS = {
    0: _ASYM_SHAPES,
    1: _ROW_SHAPES,
    2: _COL_SHAPES,
    3: _BOTH_SHAPES,
}

# Guaranteed larger wrong-class distractors. Matching banks top out at area 9.
_LARGE_BOTH = tuple(sorted(
    {(2, c) for c in range(5)}
    | {(r, 2) for r in range(5)}
    | {(1, 1), (1, 3), (3, 1), (3, 3)}
))  # area 13, class 3
_LARGE_ROW = (
    (0, 0), (0, 1), (0, 2),
    (1, 0), (1, 1), (1, 2), (1, 3),
    (2, 0), (2, 1), (2, 2),
)  # area 10, class 1


def _norm(cells) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _row_sym(cells) -> bool:
    cells = _norm(cells)
    height = max(r for r, _ in cells) + 1
    pool = set(cells)
    return all((height - 1 - r, c) in pool for r, c in cells)


def _col_sym(cells) -> bool:
    cells = _norm(cells)
    width = max(c for _, c in cells) + 1
    pool = set(cells)
    return all((r, width - 1 - c) in pool for r, c in cells)


def _sym_class(cells) -> int:
    row, col = _row_sym(cells), _col_sym(cells)
    return (1 if row else 0) + (2 if col else 0)


def _connected4(cells) -> bool:
    pool = set(cells)
    if not pool:
        return False
    seen = {next(iter(pool))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for dr, dc in _CARD:
            nxt = (row + dr, col + dc)
            if nxt in pool and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == pool


def _is_rectangular(cells) -> bool:
    cells = _norm(cells)
    height = max(r for r, _ in cells) + 1
    width = max(c for _, c in cells) + 1
    return len(cells) == height * width


def _variants(shape) -> tuple[tuple[tuple[int, int], ...], ...]:
    shape = _norm(shape)
    height = max(r for r, _ in shape) + 1
    width = max(c for _, c in shape) + 1
    variants = {
        _norm(shape),
        _norm((r, width - 1 - c) for r, c in shape),
        _norm((height - 1 - r, c) for r, c in shape),
        _norm((height - 1 - r, width - 1 - c) for r, c in shape),
    }
    return tuple(sorted(variants))


def _scheduled_int(ctx, label: str, lo: int, hi: int, desired: int) -> int:
    """Record a deterministic schedule through a full-domain public draw."""
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    options = list(range(lo, hi + 1))
    selected = ctx.draw_rng(label).randrange(len(options))
    wanted = options.index(int(desired))
    options[selected], options[wanted] = options[wanted], options[selected]
    return int(ctx.draw_choice(label, tuple(options)))


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    del seed, difficulty
    index = int(sample_index) % 8
    return f"code{index % 4 + 1}_rank{_RANK_SCHEDULE[index]}"


SCHEDULE_PROFILES = tuple(
    f"code{index % 4 + 1}_rank{_RANK_SCHEDULE[index]}" for index in range(8)
)


def _target_class(sym_code: int) -> int:
    return {1: 2, 2: 1, 3: 3, 4: 0}[int(sym_code)]


def _components(grid) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[dict[str, Any]] = []
    for start_r in range(2, height):
        for start_c in range(width):
            color = grid[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue
            cells: list[tuple[int, int]] = []
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in _CARD:
                    nr, nc = row + dr, col + dc
                    if (
                        2 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            norm = _norm(cells)
            found.append({
                "color": color,
                "cells": tuple(sorted(cells)),
                "norm": norm,
                "area": len(cells),
                "class": _sym_class(norm),
                "top": min(r for r, _ in cells),
                "left": min(c for _, c in cells),
            })
    return found


def _sorted(components) -> list[dict[str, Any]]:
    return sorted(components, key=lambda obj: (-obj["area"], obj["top"], obj["left"]))


def _mask(obj, *, fill_bbox: bool = False) -> list[list[int]]:
    cells = obj["norm"]
    height = max(r for r, _ in cells) + 1
    width = max(c for _, c in cells) + 1
    if fill_bbox:
        return full_grid(height, width, 8)
    out = full_grid(height, width, 0)
    for row, col in cells:
        out[row][col] = 8
    return out


def semantic_features(grid) -> dict[str, Any]:
    errors = self_check(grid)
    if errors:
        return {"errors": errors}
    sym_code = sum(value == 1 for value in grid[0])
    rank = sum(value == 2 for value in grid[1])
    target = _target_class(sym_code)
    components = _components(grid)
    matches = _sorted([obj for obj in components if obj["class"] == target])
    distractors = [obj for obj in components if obj["class"] != target]
    winner = matches[rank - 1]
    largest_body = _sorted(components)[0]
    return {
        "errors": [],
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette_size": len({value for row in grid for value in row}),
        "sym_code": sym_code,
        "rank": rank,
        "target_class": target,
        "n_match": len(matches),
        "n_distractor": len(distractors),
        "match_areas": tuple(obj["area"] for obj in matches),
        "distractor_areas": tuple(sorted((obj["area"] for obj in distractors), reverse=True)),
        "winner_area": winner["area"],
        "winner_class": winner["class"],
        "winner_rectangular": _is_rectangular(winner["norm"]),
        "largest_body_is_winner": largest_body["cells"] == winner["cells"],
        "larger_wrong_class_distractor": any(
            obj["area"] > winner["area"] for obj in distractors
        ),
    }


def observe_overrides(grid) -> dict[str, int]:
    facts = semantic_features(grid)
    if facts.get("errors"):
        raise ValueError("cannot observe malformed grid: " + "; ".join(facts["errors"]))
    return {
        axis: int(facts[axis])
        for axis in ("sym_code", "rank", "grid_h", "grid_w", "n_match", "n_distractor")
    }


def _pick_shapes(target: int, n_match: int, n_distractor: int, rng):
    matching_by_area: dict[int, list[tuple[tuple[int, int], ...]]] = {}
    for shape in _SHAPES_BY_CLASS[target]:
        matching_by_area.setdefault(len(shape), []).append(shape)
    areas = list(matching_by_area)
    rng.shuffle(areas)
    matching = [
        rng.choice(_variants(rng.choice(matching_by_area[area])))
        for area in areas[:n_match]
    ]

    if target == 3:
        forced_class, forced_shape = 1, _LARGE_ROW
    else:
        forced_class, forced_shape = 3, _LARGE_BOTH
    distractors: list[tuple[int, tuple[tuple[int, int], ...]]] = [
        (forced_class, rng.choice(_variants(forced_shape)))
    ]
    legal_classes = [value for value in range(4) if value != target]
    while len(distractors) < n_distractor:
        cls = rng.choice(legal_classes)
        shape = rng.choice(_SHAPES_BY_CLASS[cls])
        distractors.append((cls, rng.choice(_variants(shape))))
    return [(target, shape) for shape in matching] + distractors


def _slots(height: int, width: int) -> list[tuple[int, int, int, int]]:
    body_top = 3
    body_height = height - body_top
    row_edges = (body_top, body_top + body_height // 2, height)
    col_edges = (0, width // 3, (2 * width) // 3, width)
    return [
        (row_edges[r], row_edges[r + 1], col_edges[c], col_edges[c + 1])
        for r in range(2)
        for c in range(3)
    ]


def _place_in_slot(grid, shape, color: int, slot, rng, difficulty) -> None:
    top, bottom, left, right = slot
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    if shape_h > bottom - top or shape_w > right - left:
        raise AssertionError(f"shape {shape_h}x{shape_w} does not fit slot {slot}")
    if difficulty == "easy":
        row0 = top + (bottom - top - shape_h) // 2
        col0 = left + (right - left - shape_w) // 2
    else:
        row0 = rng.randint(top, bottom - shape_h)
        col0 = rng.randint(left, right - shape_w)
    for row, col in shape:
        grid[row0 + row][col0 + col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    query_index = int(sample_index) % 8
    sym_code = _scheduled_int(ctx, "sym_code", 1, 4, query_index % 4 + 1)
    rank = _scheduled_int(ctx, "rank", 1, 2, _RANK_SCHEDULE[query_index])

    profile_index = int(sample_index) % len(_DIMENSION_SCHEDULE)
    scheduled_h, scheduled_w = _DIMENSION_SCHEDULE[profile_index]
    scheduled_match, scheduled_distractor = _COUNT_SCHEDULE[profile_index]
    height = _scheduled_int(ctx, "grid_h", 13, 20, scheduled_h)
    width = _scheduled_int(ctx, "grid_w", 16, 24, scheduled_w)
    n_match = _scheduled_int(ctx, "n_match", 2, 3, scheduled_match)
    n_distractor = _scheduled_int(
        ctx, "n_distractor", 1, 3, scheduled_distractor
    )

    target = _target_class(sym_code)
    grid = full_grid(height, width, 0)
    header_rng = ctx.draw_rng("headers")
    for col in header_rng.sample(range(width), sym_code):
        grid[0][col] = 1
    for col in header_rng.sample(range(width), rank):
        grid[1][col] = 2

    layout_rng = ctx.draw_rng("layout")
    specs = _pick_shapes(target, n_match, n_distractor, layout_rng)
    layout_rng.shuffle(specs)
    slots = _slots(height, width)
    layout_rng.shuffle(slots)

    # Color 2 is deliberately reused in the body, as in every canonical input.
    # The empty separator row keeps it a separate object from the rank header.
    body_palette = [2] + layout_rng.sample([3, 4, 5, 6, 7, 9], len(specs) - 1)
    layout_rng.shuffle(body_palette)
    for (_cls, shape), color, slot in zip(specs, body_palette, slots):
        _place_in_slot(grid, shape, color, slot, layout_rng, difficulty)

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("generator constructed an invalid grid: " + "; ".join(errors))
    facts = semantic_features(grid)
    if not facts["larger_wrong_class_distractor"]:
        raise AssertionError("ordinary draw failed largest-object shortcut rebuttal")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        errors.append("all cells must be integer ARC colors 0..9")
    height = len(grid)
    if not 13 <= height <= 20:
        errors.append(f"grid_h must be in 13..20, got {height}")
    if not 16 <= width <= 24:
        errors.append(f"grid_w must be in 16..24, got {width}")
    if height < 3:
        return errors + ["grid needs two header rows and a separator row"]

    if any(value not in (0, 1) for value in grid[0]):
        errors.append("row 0 may contain only background 0 and class markers 1")
    if any(value not in (0, 2) for value in grid[1]):
        errors.append("row 1 may contain only background 0 and rank markers 2")
    if any(value != 0 for value in grid[2]):
        errors.append("row 2 must be an empty separator")
    sym_code = sum(value == 1 for value in grid[0])
    rank = sum(value == 2 for value in grid[1])
    if sym_code not in (1, 2, 3, 4):
        errors.append(f"row 0 must encode symmetry code 1..4, got {sym_code}")
    if rank not in (1, 2):
        errors.append(f"row 1 must encode rank 1..2, got {rank}")
    if errors:
        return errors

    components = _components(grid)
    if len(components) < 3:
        errors.append(f"body needs at least three objects, found {len(components)}")
    color_counts = Counter(obj["color"] for obj in components)
    repeated = sorted(color for color, count in color_counts.items() if count != 1)
    if repeated:
        errors.append(f"each body color must form exactly one object; repeated {repeated}")
    for obj in components:
        if obj["area"] < 3:
            errors.append(f"body object color {obj['color']} is too small (area {obj['area']})")
        if not _connected4(obj["norm"]):
            errors.append(f"body object color {obj['color']} is not 4-connected")

    target = _target_class(sym_code)
    matches = _sorted([obj for obj in components if obj["class"] == target])
    distractors = [obj for obj in components if obj["class"] != target]
    if len(matches) < rank:
        errors.append(f"rank {rank} needs at least {rank} matching objects, found {len(matches)}")
    if len(matches) < 2:
        errors.append(f"requested class needs at least two objects, found {len(matches)}")
    if not distractors:
        errors.append("body needs at least one wrong-class distractor")
    areas = [obj["area"] for obj in matches]
    if len(areas) != len(set(areas)):
        errors.append(f"matching-object areas must be distinct, got {areas}")
    if len(matches) >= rank and _is_rectangular(matches[rank - 1]["norm"]):
        errors.append("selected object must be nonrectangular")

    requested = {}
    if isinstance(meta, dict):
        candidate = meta.get("overrides", meta)
        if isinstance(candidate, dict):
            requested = {name: candidate[name] for name in AXES if name in candidate}
    if requested and not errors:
        observed = {
            "sym_code": sym_code,
            "rank": rank,
            "grid_h": height,
            "grid_w": width,
            "n_match": len(matches),
            "n_distractor": len(distractors),
        }
        for name, value in requested.items():
            if observed[name] != int(value):
                errors.append(f"{name} requested {value!r}, observed {observed[name]!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    facts = semantic_features(grid)
    if (facts["grid_h"], facts["grid_w"]) not in {(13, 16), (14, 17), (14, 18)}:
        reasons.append("dimensions are outside the three canonical profiles")
    if facts["palette_size"] != 6:
        reasons.append(f"canonical palette size is 6, got {facts['palette_size']}")
    if facts["n_match"] != 3 or facts["n_distractor"] != 1:
        reasons.append(
            "canonical body profile is three matching objects plus one distractor"
        )
    return reasons


MIN_STRICT_FRAC = 0.20
EXAMPLES_NEEDED = 4


def rule_mirror(grid) -> list[list[int]]:
    sym_code = sum(value == 1 for value in grid[0])
    rank = sum(value == 2 for value in grid[1])
    if sym_code not in (1, 2, 3, 4) or rank not in (1, 2):
        raise ValueError("invalid query headers")
    target = _target_class(sym_code)
    matches = _sorted([obj for obj in _components(grid) if obj["class"] == target])
    if len(matches) < rank:
        raise ValueError("not enough matching objects")
    return _mask(matches[rank - 1])


def _rival_select(
    grid,
    *,
    fixed_class: int | None = None,
    fixed_rank: int | None = None,
    all_objects: bool = False,
    smallest: bool = False,
    fill_bbox: bool = False,
) -> list[list[int]]:
    sym_code = sum(value == 1 for value in grid[0])
    rank = sum(value == 2 for value in grid[1])
    target = _target_class(sym_code) if fixed_class is None else fixed_class
    body_components = _components(grid)
    candidates = body_components if all_objects else [obj for obj in body_components if obj["class"] == target]
    candidates = _sorted(candidates)
    if smallest:
        candidates = list(reversed(candidates))
    chosen_rank = rank if fixed_rank is None else fixed_rank
    if chosen_rank < 1 or len(candidates) < chosen_rank:
        return [[0]]
    return _mask(candidates[chosen_rank - 1], fill_bbox=fill_bbox)


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_largest_body(grid):
    return _rival_select(grid, all_objects=True, fixed_rank=1)


def _rival_rank_all_objects(grid):
    return _rival_select(grid, all_objects=True)


def _rival_largest_matching(grid):
    return _rival_select(grid, fixed_rank=1)


def _rival_smallest_matching(grid):
    return _rival_select(grid, fixed_rank=1, smallest=True)


def _rival_fixed_row(grid):
    return _rival_select(grid, fixed_class=1)


def _rival_fixed_col(grid):
    return _rival_select(grid, fixed_class=2)


def _rival_fixed_both(grid):
    return _rival_select(grid, fixed_class=3)


def _rival_fixed_asym(grid):
    return _rival_select(grid, fixed_class=0)


def _rival_bbox_fill(grid):
    return _rival_select(grid, fill_bbox=True)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "identity_input": _rival_identity,
    "largest_body": _rival_largest_body,
    "rank_all_objects": _rival_rank_all_objects,
    "largest_matching": _rival_largest_matching,
    "smallest_matching": _rival_smallest_matching,
    "fixed_row_class": _rival_fixed_row,
    "fixed_col_class": _rival_fixed_col,
    "fixed_both_class": _rival_fixed_both,
    "fixed_asym_class": _rival_fixed_asym,
    "bbox_fill": _rival_bbox_fill,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _witness_code(code: int):
    return lambda grid: semantic_features(grid).get("sym_code") == code


def _witness_rank(rank: int):
    return lambda grid: semantic_features(grid).get("rank") == rank


SEMANTIC_WITNESSES = {
    "code_col_only": _witness_code(1),
    "code_row_only": _witness_code(2),
    "code_both": _witness_code(3),
    "code_asymmetric": _witness_code(4),
    "rank_largest": _witness_rank(1),
    "rank_second": _witness_rank(2),
    "at_least_three_matches": lambda grid: semantic_features(grid).get("n_match", 0) >= 3,
    "larger_wrong_class_distractor": lambda grid: bool(
        semantic_features(grid).get("larger_wrong_class_distractor")
    ),
    "nonrectangular_winner": lambda grid: (
        semantic_features(grid).get("winner_rectangular") is False
    ),
}

WITNESS_RIVALS = {
    "code_col_only": ["fixed_row_class"],
    "code_row_only": ["fixed_col_class"],
    "code_both": ["fixed_asym_class"],
    "code_asymmetric": ["fixed_both_class"],
    "rank_largest": ["smallest_matching"],
    "rank_second": ["largest_matching"],
    "at_least_three_matches": ["smallest_matching"],
    "larger_wrong_class_distractor": ["largest_body", "rank_all_objects"],
    "nonrectangular_winner": ["bbox_fill"],
}


def _pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair:
        return [f"{label} must contain an input grid"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label}: {message}" for message in errors]
    if "output" in pair and pair["output"] != rule_mirror(pair["input"]):
        return [f"{label} output disagrees with the symmetry-class/rank rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        reasons.extend(_pair_errors(pair, f"demo {index}"))
    reasons.extend(_pair_errors(query, "query"))
    if reasons:
        return reasons

    codes = {sum(value == 1 for value in pair["input"][0]) for pair in demos}
    ranks = {sum(value == 2 for value in pair["input"][1]) for pair in demos}
    if codes != {1, 2, 3, 4}:
        reasons.append(f"demonstrations do not cover all four class codes: {sorted(codes)}")
    if ranks != {1, 2}:
        reasons.append(f"demonstrations do not cover both ranks: {sorted(ranks)}")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named competitor {name!r} survives every demonstration")
    return reasons


def mutation_fixtures():
    base = generate(91, 0, difficulty="medium")
    fixtures = []

    missing_class = [row[:] for row in base]
    missing_class[0] = [0] * len(missing_class[0])
    fixtures.append(("missing_class_header", missing_class))

    rank_three = [row[:] for row in base]
    rank_three[1] = [0] * len(rank_three[1])
    for col in range(3):
        rank_three[1][col] = 2
    fixtures.append(("rank_three", rank_three))

    noisy_header = [row[:] for row in base]
    noisy_header[0][next(col for col, value in enumerate(noisy_header[0]) if value == 0)] = 7
    fixtures.append(("wrong_header_color", noisy_header))

    dirty_separator = [row[:] for row in base]
    dirty_separator[2][0] = 3
    fixtures.append(("dirty_separator", dirty_separator))

    absent_requested_class = [row[:] for row in base]
    target = _target_class(sum(value == 1 for value in absent_requested_class[0]))
    for obj in _components(absent_requested_class):
        if obj["class"] == target:
            for row, col in obj["cells"]:
                absent_requested_class[row][col] = 0
    fixtures.append(("requested_class_absent", absent_requested_class))
    return fixtures


# Fail during import if a future edit corrupts the finite morphology library.
for _class, _pool in _SHAPES_BY_CLASS.items():
    for _shape in _pool:
        assert _connected4(_shape)
        assert _sym_class(_shape) == _class
        assert not _is_rectangular(_shape)
assert len(_LARGE_BOTH) == 13 and _sym_class(_LARGE_BOTH) == 3
assert len(_LARGE_ROW) == 10 and _sym_class(_LARGE_ROW) == 1
