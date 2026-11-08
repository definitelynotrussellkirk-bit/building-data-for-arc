"""Generator for v2_meta_puzzles:H2 — translate by the signed marker vector.

The unchanged Racket authority copies the single connected color-3 object by
``position(2) - position(1)`` and paints the ghost in color 2 while preserving
all input cells.  The sampler deliberately covers all four vector quadrants so
lessons cannot collapse to the canonical-only ``abs(dr), abs(dc)`` shortcut.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "83e2dcfca651"
TASK_ID = GENERATOR_ID
RULE_HASH = "94474e600431"
VERSION = "3.0.0"

SUMMARY = (
    "A 0-background grid contains exactly one blue marker (1), one red marker "
    "(2), and one connected green polyomino (3). The signed displacement from "
    "the blue marker to the red marker has nonzero row and column components. "
    "Copy the entire green object by that displacement and paint the copy red, "
    "leaving the markers and original green object unchanged. Grid size, object "
    "size and shape, marker vector, object position, and marker position vary; "
    "default lessons cycle through all four vector quadrants."
)

INVARIANTS = [
    "background is 0 and the only non-background colors are 1, 2, and 3",
    "exactly one color-1 marker and one color-2 marker define a signed vector with both components nonzero",
    "exactly one 4-connected color-3 object has 3..6 cells",
    "the translated object is in bounds, disjoint from the source, and lands on background",
    "both markers are disjoint from the source object and its translated target",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical anchors plus broad 8..12", "valid": "8..12"},
    "grid_w": {"type": "int", "default": "canonical anchors plus broad 10..15", "valid": "10..15"},
    "object_size": {"type": "int", "default": "difficulty-weighted 3..6", "valid": "3..6"},
    "vector_dr": {"type": "int", "default": "scheduled sign, difficulty-weighted magnitude", "valid": "-4..4 (≠0)"},
    "vector_dc": {"type": "int", "default": "scheduled sign, difficulty-weighted magnitude", "valid": "-5..5 (≠0)"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = ("down_right", "down_left", "up_right", "up_left")
_PROFILE_SIGNS = {
    "down_right": (1, 1),
    "down_left": (1, -1),
    "up_right": (-1, 1),
    "up_left": (-1, -1),
}

_ALLOWED_RANGES = {
    "grid_h": (8, 12),
    "grid_w": (10, 15),
    "object_size": (3, 6),
    "vector_dr": (-4, 4),
    "vector_dc": (-5, 5),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the deterministic vector-quadrant curriculum profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_controls(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        lo, hi = _ALLOWED_RANGES[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
        if name in ("vector_dr", "vector_dc") and value == 0:
            raise ValueError(f"{name} must be nonzero")


def _draw_dimension(ctx, name, sample_index, difficulty, overrides):
    lo, hi = _ALLOWED_RANGES[name]
    full = list(range(lo, hi + 1))
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, full)

    # Consecutive pinned samples always include both exact canonical profiles.
    profile_slot = int(sample_index) % 10
    if name == "grid_h" and profile_slot == 0:
        return ctx.draw_choice(name, [9])
    if name == "grid_w" and profile_slot == 0:
        return ctx.draw_choice(name, [12])
    if name == "grid_h" and profile_slot == 1:
        return ctx.draw_choice(name, [10])
    if name == "grid_w" and profile_slot == 1:
        return ctx.draw_choice(name, [13])

    favored = {
        "easy": {"grid_h": [8, 9, 9, 10], "grid_w": [10, 11, 12, 12, 13]},
        "medium": {"grid_h": [9, 9, 10, 10, 11], "grid_w": [11, 12, 12, 13, 13, 14]},
        "hard": {"grid_h": [9, 10, 10, 11, 11, 12], "grid_w": [12, 13, 13, 14, 14, 15]},
        None: {"grid_h": [9, 10, 10, 11], "grid_w": [11, 12, 13, 13, 14]},
    }[difficulty][name]
    return ctx.draw_choice(name, full + favored * 4)


def _draw_object_size(ctx, difficulty, overrides):
    full = [3, 4, 5, 6]
    if overrides.get("object_size") is not None:
        return ctx.draw_choice("object_size", full)
    favored = {
        "easy": [3, 3, 3, 4, 4],
        "medium": [3, 4, 4, 5, 5, 6],
        "hard": [4, 5, 5, 6, 6, 6],
        None: [3, 4, 4, 5, 5, 6],
    }[difficulty]
    return ctx.draw_choice("object_size", full + favored * 5)


def _draw_vector_component(ctx, name, sign, difficulty, overrides):
    max_abs = 4 if name == "vector_dr" else 5
    full = [value for value in range(-max_abs, max_abs + 1) if value]
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, full)
    magnitudes = {
        "easy": [1, 1, 1, 2, 2, 3],
        "medium": [1, 2, 2, 3, 3, 4],
        "hard": [2, 3, 3, 4, 4, max_abs],
        None: [1, 2, 2, 3, 3, 4],
    }[difficulty]
    legal = [m for m in magnitudes if m <= max_abs]
    return ctx.draw_choice(name, [sign * m for m in legal])


def _normalized(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    materialized = tuple(cells)
    r0 = min(r for r, _ in materialized)
    c0 = min(c for _, c in materialized)
    return tuple(sorted((r - r0, c - c0) for r, c in materialized))


@lru_cache(maxsize=8)
def _polyominoes(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Enumerate fixed 4-connected polyominoes, translation-normalized."""
    shapes = {((0, 0),)}
    for _ in range(1, size):
        expanded = set()
        for shape in sorted(shapes):
            occupied = set(shape)
            for r, c in shape:
                for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if point not in occupied:
                        expanded.add(_normalized((*shape, point)))
        shapes = expanded
    return tuple(sorted(shapes))


def _shape_dims(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _shape_options(size, h, w, dr, dc):
    options = []
    for shape in _polyominoes(size):
        cells = set(shape)
        shifted = {(r + dr, c + dc) for r, c in cells}
        if cells & shifted:
            continue
        sh, sw = _shape_dims(shape)
        min_r = max(0, -dr)
        max_r = min(h - sh, h - sh - dr)
        min_c = max(0, -dc)
        max_c = min(w - sw, w - sw - dc)
        if min_r <= max_r and min_c <= max_c:
            options.append((shape, min_r, max_r, min_c, max_c))
    return options


def _positions(grid, color):
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def _components4(cells):
    unseen = set(cells)
    components = []
    while unseen:
        component = {unseen.pop()}
        stack = list(component)
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    stack.append(point)
        components.append(component)
    return components


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_controls(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_dimension(ctx, "grid_h", sample_index, difficulty, overrides)
    w = _draw_dimension(ctx, "grid_w", sample_index, difficulty, overrides)
    object_size = _draw_object_size(ctx, difficulty, overrides)

    profile = schedule_profile(seed, sample_index, difficulty)
    sign_r, sign_c = _PROFILE_SIGNS[profile]
    dr = _draw_vector_component(ctx, "vector_dr", sign_r, difficulty, overrides)
    dc = _draw_vector_component(ctx, "vector_dc", sign_c, difficulty, overrides)

    shape_options = _shape_options(object_size, h, w, dr, dc)
    if not shape_options:
        raise ValueError(
            "requested grid/object/vector combination has no disjoint in-bounds placement"
        )
    shape, min_r, max_r, min_c, max_c = ctx.draw_rng("shape").choice(shape_options)
    r0 = ctx.draw_rng("object_row").randint(min_r, max_r)
    c0 = ctx.draw_rng("object_col").randint(min_c, max_c)
    source = {(r0 + r, c0 + c) for r, c in shape}
    target = {(r + dr, c + dc) for r, c in source}

    blocked = source | target
    marker_starts = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if 0 <= r + dr < h
        and 0 <= c + dc < w
        and (r, c) not in blocked
        and (r + dr, c + dc) not in blocked
    ]
    if not marker_starts:
        raise ValueError(
            "requested grid/object/vector combination leaves no independent marker pair"
        )
    p1 = ctx.draw_rng("marker_position").choice(marker_starts)
    p2 = (p1[0] + dr, p1[1] + dc)

    grid = full_grid(h, w, 0)
    grid[p1[0]][p1[1]] = 1
    grid[p2[0]][p2[1]] = 2
    for r, c in source:
        grid[r][c] = 3
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete input-domain contract without executing the rule."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty row list"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int for row in grid for value in row):
        return ["grid cells must be integers, not booleans or other types"]

    errors = []
    palette = {value for row in grid for value in row}
    unknown = sorted(palette - {0, 1, 2, 3})
    if unknown:
        errors.append(f"unexpected colors: {unknown}")

    p1 = _positions(grid, 1)
    p2 = _positions(grid, 2)
    green = set(_positions(grid, 3))
    if len(p1) != 1:
        errors.append(f"expected exactly one color-1 marker; found {len(p1)}")
    if len(p2) != 1:
        errors.append(f"expected exactly one color-2 marker; found {len(p2)}")
    if not 3 <= len(green) <= 6:
        errors.append(f"expected a 3..6-cell color-3 object; found {len(green)} cells")
    if green and len(_components4(green)) != 1:
        errors.append("color-3 cells must form exactly one 4-connected object")

    if len(p1) == 1 and len(p2) == 1:
        dr = p2[0][0] - p1[0][0]
        dc = p2[0][1] - p1[0][1]
        if dr == 0 or dc == 0:
            errors.append("marker vector must have nonzero row and column components")
        if green:
            h, w = len(grid), width
            target = {(r + dr, c + dc) for r, c in green}
            out_of_bounds = sorted((r, c) for r, c in target if not (0 <= r < h and 0 <= c < w))
            if out_of_bounds:
                errors.append(f"translated object leaves the grid at {out_of_bounds[:3]}")
            if green & target:
                errors.append("translated object overlaps the source object")
            markers = {p1[0], p2[0]}
            if markers & green:
                errors.append("marker overlaps the source object")
            if markers & target:
                errors.append("marker overlaps the translated target")
            occupied_target = sorted(
                (r, c)
                for r, c in target
                if 0 <= r < h and 0 <= c < w and grid[r][c] != 0
            )
            if occupied_target:
                errors.append(f"translated target must be background; occupied at {occupied_target[:3]}")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    findings = self_check(grid)
    if findings:
        raise ValueError("cannot observe axes on invalid grid: " + "; ".join(findings))
    p1 = _positions(grid, 1)[0]
    p2 = _positions(grid, 2)[0]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "object_size": len(_positions(grid, 3)),
        "vector_dr": p2[0] - p1[0],
        "vector_dc": p2[1] - p1[1],
    }


def _copy_with_vector(grid, dr, dc):
    out = [list(row) for row in grid]
    for r, c in _positions(grid, 3):
        rr, cc = r + dr, c + dc
        if 0 <= rr < len(out) and 0 <= cc < len(out[0]):
            out[rr][cc] = 2
    return out


def _absolute_vector(grid):
    p1 = _positions(grid, 1)[0]
    p2 = _positions(grid, 2)[0]
    return _copy_with_vector(grid, abs(p2[0] - p1[0]), abs(p2[1] - p1[1]))


def _signed_vector_witness(grid):
    p1 = _positions(grid, 1)
    p2 = _positions(grid, 2)
    if len(p1) != 1 or len(p2) != 1:
        return False
    return p2[0][0] < p1[0][0] or p2[0][1] < p1[0][1]


def lesson_identifiable(demos, query):
    reasons = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need {EXAMPLES_NEEDED} demonstrations; found {len(demos)}")
    vectors = set()
    for index, pair in enumerate(demos):
        grid = pair.get("input") if isinstance(pair, dict) else None
        output = pair.get("output") if isinstance(pair, dict) else None
        findings = self_check(grid)
        if findings:
            reasons.append(f"demo {index} is outside the task domain: {findings[0]}")
            continue
        p1 = _positions(grid, 1)[0]
        p2 = _positions(grid, 2)[0]
        vectors.add((p2[0] - p1[0], p2[1] - p1[1]))
        if _absolute_vector(grid) != output:
            # One labelled counterexample is sufficient to refute this shortcut.
            pass
    if len(vectors) < 2:
        reasons.append("demonstrations do not vary the marker vector")
    if demos and all(
        isinstance(pair, dict)
        and _absolute_vector(pair["input"]) == pair.get("output")
        for pair in demos
    ):
        reasons.append("demonstrations do not refute the absolute-vector shortcut")
    if not isinstance(query, dict) or self_check(query.get("input")):
        reasons.append("query is outside the task domain")
    return reasons


SEMANTIC_WITNESSES = {"signed_vector": _signed_vector_witness}
SEMANTIC_RIVALS = {"absolute_vector": _absolute_vector}
WITNESS_RIVALS = {"signed_vector": ["absolute_vector"]}
CANONICAL_SHORTCUTS = {"absolute_vector": _absolute_vector}
LESSON_COMPETITORS = {"absolute_vector": _absolute_vector}
