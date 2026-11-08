"""Generator for e0680a673043 — select a ranked object, then transform it.

The two header cells are commands: ``(0,0)`` is the one-based rank and
``(0,w-1)`` is the transform code.  After removing those cells, body objects
are ranked by descending area and then ascending color.  The selected object is
tightly cropped and transformed: 1=clockwise, 2=180°, 3=left/right mirror,
4=up/down mirror.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "e0680a673043"
TASK_ID = "e0680a673043"
VERSION = "3.0.0"
RULE_HASH = "2a70169611d2"

SUMMARY = (
    "Read rank k from the upper-left and a transform command from the "
    "upper-right. Remove both commands, rank the three separated body objects "
    "by area descending/color ascending, crop the k-th object, and transform it."
)

INVARIANTS = [
    "input is a rectangular 9..14 by 12..18 ARC grid",
    "(0,0) is an exact rank k in 1..3 and (0,w-1) is cmd in 1..4",
    "after removing the command cells there are exactly three 4-connected objects",
    "the three body objects have distinct sizes and distinct nonzero colors",
    "body objects have one-cell diagonal clearance",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware", "valid": "9..14"},
    "grid_w": {"type": "int", "default": "difficulty-aware", "valid": "12..18"},
    "k": {"type": "int", "default": "difficulty-aware", "valid": "1..3"},
    "cmd": {"type": "int", "default": "difficulty-aware", "valid": "1..4"},
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Connected, asymmetric alternatives of sizes 3/4/5.  D4 transforms below
# make their orientation independent of their size/rank.
_SHAPES = {
    3: (
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2)),
    ),
    4: (
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
    ),
    5: (
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
    ),
}


def _validate_nonnegative_exact_integer(value: Any, name: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative exact integer")


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    _validate_nonnegative_exact_integer(seed, "seed")
    _validate_nonnegative_exact_integer(sample_index, "sample_index")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in AXES:
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")


def _axis_int(ctx, label: str, full_lo: int, full_hi: int, default_lo: int, default_hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, full_lo, full_hi)
    return ctx.draw_int_strict(label, default_lo, default_hi)


def _normalize(cells: list[tuple[int, int]] | tuple[tuple[int, int], ...]) -> list[tuple[int, int]]:
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def _transform_cells(cells: tuple[tuple[int, int], ...], turn: int, mirror: bool) -> list[tuple[int, int]]:
    out = list(cells)
    if mirror:
        out = [(r, -c) for r, c in out]
    for _ in range(turn % 4):
        out = [(c, -r) for r, c in out]
    return _normalize(out)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input; every public override is exact."""
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    bands = {
        "easy": (9, 10, 12, 14, 1, 2, 1, 2),
        "medium": (10, 12, 13, 16, 1, 3, 1, 4),
        "hard": (12, 14, 15, 18, 2, 3, 2, 4),
        None: (9, 14, 12, 18, 1, 3, 1, 4),
    }
    h_lo, h_hi, w_lo, w_hi, k_lo, k_hi, cmd_lo, cmd_hi = bands[difficulty]
    h = _axis_int(ctx, "grid_h", 9, 14, h_lo, h_hi)
    w = _axis_int(ctx, "grid_w", 12, 18, w_lo, w_hi)
    k = _axis_int(ctx, "k", 1, 3, k_lo, k_hi)
    cmd = _axis_int(ctx, "cmd", 1, 4, cmd_lo, cmd_hi)

    grid = full_grid(h, w, 0)
    grid[0][0] = k
    grid[0][w - 1] = cmd

    rng = ctx.draw_rng("layout")
    sizes = [3, 4, 5]
    rng.shuffle(sizes)
    colors = rng.sample((1, 2, 3, 4, 5, 6, 7, 8, 9), 3)
    # Three disjoint width-three lanes with at least one blank column between
    # neighboring lanes even at the minimum width.
    lanes = [0, max(4, (w // 2) - 1), w - 3]
    rng.shuffle(lanes)
    for size, color, lane in zip(sizes, colors, lanes):
        source = rng.choice(_SHAPES[size])
        shape = _transform_cells(source, rng.randrange(4), bool(rng.randrange(2)))
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        # Every transformed template is at most 3x3 and fits its lane.
        left = lane + rng.randint(0, 3 - sw)
        top = rng.randint(2, h - sh)
        paint_at(grid, top, left, shape, color)
    return grid


def _components_same_color(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result: list[dict[str, Any]] = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        queue = deque([start])
        unseen.remove(start)
        cells: list[tuple[int, int]] = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                q = (r + dr, c + dc)
                if q in unseen and grid[q[0]][q[1]] == color:
                    unseen.remove(q)
                    queue.append(q)
        result.append({"color": color, "cells": cells})
    return result


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def _flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid[::-1]]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent pure-Python mirror of the selected canonical Racket rule."""
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    clean = [row[:] for row in grid]
    k = clean[0][0]
    cmd = clean[0][width - 1]
    clean[0][0] = 0
    clean[0][width - 1] = 0
    objects = _components_same_color(clean)
    objects.sort(key=lambda obj: (-len(obj["cells"]), obj["color"]))
    if type(k) is not int or not 1 <= k <= len(objects):
        raise ValueError("rank key does not select an object")
    chosen = objects[k - 1]
    rows = [r for r, _ in chosen["cells"]]
    cols = [c for _, c in chosen["cells"]]
    r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
    crop = [[0 for _ in range(c1, c2 + 1)] for _ in range(r1, r2 + 1)]
    for r, c in chosen["cells"]:
        crop[r - r1][c - c1] = clean[r][c]
    if cmd == 1:
        return _rotate_cw(crop)
    if cmd == 2:
        return _rotate_180(crop)
    if cmd == 3:
        return _flip_lr(crop)
    return _flip_ud(crop)


def observe_overrides(grid: list[list[int]]) -> dict[str, int]:
    if not grid or not grid[0]:
        raise ValueError("grid must be nonempty")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "k": grid[0][0],
        "cmd": grid[0][-1],
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed ordinary lessons and ambiguous ranking structure."""
    del difficulty, meta
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a nonempty row list"]
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be rectangular and nonempty"]
    if not 9 <= len(grid) <= 14 or not 12 <= width <= 18:
        errors.append(f"ordinary grid must be 9..14 by 12..18, got {len(grid)}x{width}")
    if grid[0][0] not in (1, 2, 3):
        errors.append(f"rank key at (0,0) must be 1..3, got {grid[0][0]}")
    if grid[0][-1] not in (1, 2, 3, 4):
        errors.append(f"transform cmd at (0,w-1) must be 1..4, got {grid[0][-1]}")

    clean = [row[:] for row in grid]
    clean[0][0] = 0
    clean[0][-1] = 0
    objects = _components_same_color(clean)
    if len(objects) != 3:
        errors.append(f"expected exactly 3 body objects, found {len(objects)}")
        return errors
    sizes = [len(obj["cells"]) for obj in objects]
    colors = [obj["color"] for obj in objects]
    if len(set(sizes)) != 3:
        errors.append(f"body object sizes must be distinct, got {sorted(sizes)}")
    if len(set(colors)) != 3:
        errors.append(f"body object colors must be distinct, got {sorted(colors)}")

    owner = {cell: index for index, obj in enumerate(objects) for cell in obj["cells"]}
    for (r, c), index in owner.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if not (dr or dc):
                    continue
                other = owner.get((r + dr, c + dc))
                if other is not None and other != index:
                    errors.append("body objects must have diagonal clearance")
                    return errors
    return errors
