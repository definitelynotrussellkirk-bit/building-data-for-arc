"""Input sampler for task 2c83e8cd1c07: fill clear diagonal spans.

The selected Racket rule is the sole label authority.  Normal draws contain
one to five clear same-color diagonal endpoint pairs and one counterexample:
another diagonal pair whose interior is blocked by an endpoint of the first
clear pair.  The counterexample distinguishes the canonical-compatible shortcut
"connect every diagonal pair" from the actual zero-interior precondition.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2c83e8cd1c07"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "177b2df2b99a"

SUMMARY = (
    "A 7..14 square/rectangular zero-background grid contains 1..5 clear "
    "same-color endpoint pairs on perfect 45-degree diagonals.  The reference "
    "fills each clear segment inclusively.  Every generated input also contains "
    "one different-color diagonal pair crossing a clear pair's endpoint in its "
    "interior, so that blocked pair remains unchanged and explicitly teaches the "
    "zero-interior condition."
)

INVARIANTS = [
    "background is color 0 and all cells are integer ARC colors",
    "each nonzero color occurs exactly twice on a perfect non-axis diagonal",
    "1..5 diagonal pairs have entirely zero interiors and are fillable",
    "normal generated draws have exactly one blocked pair",
    "the blocked pair contains exactly one nonzero interior cell, an endpoint of a fillable pair",
    "fillable paths are pairwise disjoint and every requested count is realized exactly",
]

COUNTER_HYPOTHESES = [
    "connect every same-color diagonal pair even through a nonzero blocker",
    "copy the input unchanged",
    "fill with a fixed color rather than the endpoint color",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "three canonical-size anchors then one difficulty-skewed broad draw",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "three canonical-size anchors then one difficulty-skewed broad draw",
        "valid": "7..14",
    },
    "segments": {
        "type": "int",
        "default": "3-step curriculum cycle; easy 1,1,2 / medium 1,2,3 / hard 1,4,5",
        "valid": "1..5",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# A compact constructive lesson that fits every declared 7x7-or-larger canvas.
# The first positive path ends at (3,3).  The blocked path passes through that
# cell as its sole nonzero interior point.  Prefixes realize 1..5 exact positives.
_BASE_H = 5
_BASE_W = 7
_BASE_POSITIVE_PATHS = (
    ((0, 0), (1, 1), (2, 2), (3, 3)),
    ((0, 1), (1, 2), (2, 3), (3, 4)),
    ((0, 3), (1, 4), (2, 5), (3, 6)),
    ((1, 0), (2, 1), (3, 2)),
    ((2, 6), (3, 5), (4, 4)),
)
_BASE_BLOCKED_PATH = ((0, 6), (1, 5), (2, 4), (3, 3), (4, 2))
_CANONICAL_SIZE_CYCLE = ((7, 7), (8, 8), (8, 9))
_SEGMENT_CYCLES = {
    None: (1, 2, 3),
    "easy": (1, 1, 2),
    "medium": (1, 2, 3),
    "hard": (1, 4, 5),
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    bounds = {"grid_h": (7, 14), "grid_w": (7, 14), "segments": (1, 5)}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")


def _draw_dimensions(ctx):
    # An explicit value is valid in every difficulty band.  When either dimension
    # is overridden, both labels use their full declared domain so provenance and
    # partial overrides stay honest.
    if ctx.overrides.get("grid_h") is not None or ctx.overrides.get("grid_w") is not None:
        return ctx.draw_int("grid_h", 7, 14), ctx.draw_int("grid_w", 7, 14)

    slot = ctx.sample_index % 4
    if slot < 3:
        h, w = _CANONICAL_SIZE_CYCLE[slot]
        return ctx.draw_choice("grid_h", (h,)), ctx.draw_choice("grid_w", (w,))
    return ctx.draw_int_diff("grid_h", 7, 14), ctx.draw_int_diff("grid_w", 7, 14)


def _draw_segments(ctx) -> int:
    if ctx.overrides.get("segments") is not None:
        return ctx.draw_int("segments", 1, 5)
    cycle = _SEGMENT_CYCLES[ctx.difficulty]
    scheduled = cycle[ctx.sample_index % len(cycle)]
    return ctx.draw_choice("segments", (scheduled,))


def _transform_point(point, turns: int, reflect: bool):
    r, c = point
    h, w = _BASE_H, _BASE_W
    if reflect:
        c = w - 1 - c
    for _ in range(turns):
        r, c = c, h - 1 - r
        h, w = w, h
    return r, c


def _transformed_size(turns: int):
    return (_BASE_H, _BASE_W) if turns % 2 == 0 else (_BASE_W, _BASE_H)


def _place_template(grid, positive_colors, blocked_color, rng) -> None:
    turns = rng.randrange(4)
    reflect = bool(rng.randrange(2))
    th, tw = _transformed_size(turns)
    row0 = rng.randint(0, len(grid) - th)
    col0 = rng.randint(0, len(grid[0]) - tw)

    def lift(point):
        r, c = _transform_point(point, turns, reflect)
        return row0 + r, col0 + c

    for path, color in zip(_BASE_POSITIVE_PATHS, positive_colors):
        for point in (path[0], path[-1]):
            r, c = lift(point)
            if grid[r][c] != 0:
                raise RuntimeError("constructive positive endpoints overlapped")
            grid[r][c] = color

    for point in (_BASE_BLOCKED_PATH[0], _BASE_BLOCKED_PATH[-1]):
        r, c = lift(point)
        if grid[r][c] != 0:
            raise RuntimeError("constructive blocked endpoints overlapped")
        grid[r][c] = blocked_color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w = _draw_dimensions(ctx)
    segment_count = _draw_segments(ctx)
    colors = ctx.draw_distinct_colors("colors", n=segment_count + 1, exclude={0})
    grid = full_grid(h, w, 0)
    _place_template(grid, colors[:segment_count], colors[-1], ctx.draw_rng("layout"))

    expected = {"grid_h": h, "grid_w": w, "segments": segment_count}
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(f"constructed axes drifted: expected {expected}, observed {observed}")
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": expected})
    if errors:
        raise RuntimeError("constructed invalid grid: " + "; ".join(errors))
    return grid


def _path(a, b):
    (r1, c1), (r2, c2) = a, b
    dr = (r2 > r1) - (r2 < r1)
    dc = (c2 > c1) - (c2 < c1)
    return tuple((r1 + i * dr, c1 + i * dc) for i in range(abs(r2 - r1) + 1))


def _basic_grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _analyze(grid):
    errors = _basic_grid_errors(grid)
    if errors:
        return {"errors": errors, "by_color": {}, "fillable": [], "blocked": []}

    by_color = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                by_color[value].append((r, c))

    if not by_color:
        errors.append("expected at least one fillable diagonal endpoint pair")
        return {"errors": errors, "by_color": by_color, "fillable": [], "blocked": []}

    fillable = []
    blocked = []
    for color, cells in sorted(by_color.items()):
        if len(cells) != 2:
            errors.append(f"color {color} appears {len(cells)} times, expected two endpoints")
            continue
        a, b = cells
        dr, dc = abs(a[0] - b[0]), abs(a[1] - b[1])
        if dr == 0 or dr != dc:
            errors.append(f"color {color} endpoints are not a perfect non-axis diagonal")
            continue
        path = _path(a, b)
        record = {"color": color, "a": a, "b": b, "path": path}
        nonzero_interior = tuple(point for point in path[1:-1] if grid[point[0]][point[1]] != 0)
        record["nonzero_interior"] = nonzero_interior
        (blocked if nonzero_interior else fillable).append(record)

    for index, first in enumerate(fillable):
        for second in fillable[index + 1 :]:
            if set(first["path"]) & set(second["path"]):
                errors.append("fillable diagonal paths must be pairwise disjoint")

    return {"errors": errors, "by_color": by_color, "fillable": fillable, "blocked": blocked}


def observe_overrides(grid) -> dict[str, int]:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "segments": len(info["fillable"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    info = _analyze(grid)
    errors = list(info["errors"])
    if errors:
        return errors

    fillable = info["fillable"]
    blocked = info["blocked"]
    if not 1 <= len(fillable) <= 5:
        errors.append(f"expected 1..5 fillable segments, found {len(fillable)}")
    if len(blocked) > 1:
        errors.append(f"expected at most one blocked diagonal pair, found {len(blocked)}")
    if blocked:
        points = blocked[0]["nonzero_interior"]
        if len(points) != 1:
            errors.append("blocked pair must have exactly one nonzero interior cell")
        elif not any(points[0] in (record["a"], record["b"]) for record in fillable):
            errors.append("blocked pair's blocker must be an endpoint of a fillable pair")

    if meta and isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid) if not errors else {}
            for name, value in requested.items():
                if name in AXES and observed.get(name) != value:
                    errors.append(
                        f"{name} requested {value!r}, observed {observed.get(name)!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept canonical clear-only inputs and this sampler's blocked lessons."""
    return self_check(grid)


def _colors_reading_order(grid):
    colors = []
    for row in grid:
        for value in row:
            if value != 0 and value not in colors:
                colors.append(value)
    return colors


def rule_mirror(grid, *, ignore_blockers: bool = False):
    """Pure Python test oracle; the pinned Racket program remains authority."""
    out = deepcopy(grid)
    for color in _colors_reading_order(grid):
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        if len(cells) != 2:
            continue
        a, b = cells
        dr, dc = abs(a[0] - b[0]), abs(a[1] - b[1])
        if dr == 0 or dr != dc:
            continue
        path = _path(a, b)
        if ignore_blockers or all(grid[r][c] == 0 for r, c in path[1:-1]):
            for r, c in path:
                out[r][c] = color
    return out


def _fill_without_clearance(grid):
    """Rival: incorrectly fills a diagonal even through a nonzero interior."""
    return rule_mirror(grid, ignore_blockers=True)


def _has_blocked_diagonal(grid) -> bool:
    info = _analyze(grid)
    return not info["errors"] and len(info["blocked"]) == 1


SEMANTIC_WITNESSES = {"blocked_diagonal": _has_blocked_diagonal}
SEMANTIC_RIVALS = {"ignore_interior_blocker": _fill_without_clearance}
WITNESS_RIVALS = {"blocked_diagonal": ["ignore_interior_blocker"]}
CANONICAL_SHORTCUTS = {"ignore_interior_blocker": _fill_without_clearance}
LESSON_COMPETITORS = {"ignore_interior_blocker": _fill_without_clearance}
