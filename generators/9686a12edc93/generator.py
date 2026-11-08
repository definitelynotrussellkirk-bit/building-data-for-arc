"""Input sampler for task 9686a12edc93: connect clear axis-aligned pairs.

The selected Racket rule is the sole label authority.  It starts from an empty
same-size grid.  For every nonzero color that occurs exactly twice, it fills the
inclusive row/column segment only when the endpoints are axis aligned and every
interior input cell is zero.

The five-step default schedule interleaves canonical-role clear-only anchors
with blocked counterexamples.  A blocked pair crosses an endpoint of the first
clear pair, supplying an exact counterexample to the canonical-fitting shortcut
"connect every aligned pair even through a blocker" without changing the rule.
Every three consecutive scheduled examples includes at least one counterexample.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9686a12edc93"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "74f975abb98b"

SUMMARY = (
    "A 7..16 by 9..18 zero-background grid contains 1..5 clear same-color "
    "axis-aligned endpoint pairs. The reference draws only their inclusive "
    "segments on an otherwise empty output. Scheduled examples may also contain "
    "one different-color aligned pair blocked by an endpoint of a clear pair, "
    "explicitly teaching the zero-interior precondition while clear-only anchors "
    "preserve canonical palette roles."
)

INVARIANTS = [
    "background is color 0 and every cell is an integer ARC color",
    "every nonzero color occurs exactly twice on a shared row or column",
    "1..5 endpoint pairs have entirely zero interiors and are connectable",
    "scheduled counterexample draws have exactly one blocked aligned pair",
    "the blocked pair has exactly one nonzero interior cell, an endpoint of a clear pair",
    "clear paths are pairwise disjoint and every requested axis is realized exactly",
]

COUNTER_HYPOTHESES = [
    "connect every aligned same-color pair even through nonzero blockers",
    "copy all input endpoints and invalid motifs into the output",
    "connect only horizontal pairs or only vertical pairs",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 5
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "three canonical-profile anchors, then difficulty-skewed broad draws",
        "valid": "7..16",
    },
    "grid_w": {
        "type": "int",
        "default": "three canonical-profile anchors, then difficulty-skewed broad draws",
        "valid": "9..18",
    },
    "n": {
        "type": "int",
        "default": "5-step curriculum: canonical palette anchors, high-count lesson, one-pair lesson",
        "valid": "1..5",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# A compact constructive lesson that fits every declared canvas.  The first
# clear vertical path ends at (3, 3).  The blocked horizontal path passes
# through that endpoint as its sole nonzero interior cell.  Prefixes of the
# clear-path tuple realize all exact n values from 1 through 5.
_BASE_H = 6
_BASE_W = 7
_BASE_CLEAR_PATHS = (
    ((0, 3), (1, 3), (2, 3), (3, 3)),
    ((5, 0), (5, 1), (5, 2)),
    ((5, 4), (5, 5), (5, 6)),
    ((1, 0), (2, 0), (3, 0), (4, 0)),
    ((1, 6), (2, 6), (3, 6), (4, 6)),
)
_BASE_BLOCKED_PATH = ((3, 1), (3, 2), (3, 3), (3, 4), (3, 5))
_CANONICAL_PROFILE_CYCLE = (
    (8, 9, 3),   # clear-only: 0 + three colors => canonical palette size 4
    (9, 10, 2),  # blocked: 0 + two clear colors + blocker color => palette size 4
    (10, 10, 4), # clear-only: 0 + four colors => canonical palette size 5
)
_CLEAR_ONLY_RESIDUES = frozenset({0, 2})
_HIGH_N = {None: 4, "easy": 2, "medium": 3, "hard": 5}


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    bounds = {"grid_h": (7, 16), "grid_w": (9, 18), "n": (1, 5)}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")


def _draw_dimensions(ctx) -> tuple[int, int]:
    # Explicit values are valid in every band.  If either dimension is pinned,
    # draw both through their complete declared ranges so partial overrides and
    # recorded provenance remain truthful.
    if ctx.overrides.get("grid_h") is not None or ctx.overrides.get("grid_w") is not None:
        return (
            ctx.draw_int_strict("grid_h", 7, 16),
            ctx.draw_int_strict("grid_w", 9, 18),
        )

    slot = ctx.sample_index % 5
    if slot < len(_CANONICAL_PROFILE_CYCLE):
        h, w, _ = _CANONICAL_PROFILE_CYCLE[slot]
        return (
            ctx.draw_int_strict("grid_h", h, h),
            ctx.draw_int_strict("grid_w", w, w),
        )
    return (
        ctx.draw_int_diff("grid_h", 7, 16),
        ctx.draw_int_diff("grid_w", 9, 18),
    )


def _draw_n(ctx) -> int:
    if ctx.overrides.get("n") is not None:
        return ctx.draw_int_strict("n", 1, 5)

    slot = ctx.sample_index % 5
    if slot < len(_CANONICAL_PROFILE_CYCLE):
        scheduled = _CANONICAL_PROFILE_CYCLE[slot][2]
    elif slot == 3:
        scheduled = _HIGH_N[ctx.difficulty]
    else:
        scheduled = 1
    return ctx.draw_int_strict("n", scheduled, scheduled)


def _transform_point(point: tuple[int, int], turns: int, reflect: bool) -> tuple[int, int]:
    r, c = point
    h, w = _BASE_H, _BASE_W
    if reflect:
        c = w - 1 - c
    for _ in range(turns):
        r, c = c, h - 1 - r
        h, w = w, h
    return r, c


def _transformed_size(turns: int) -> tuple[int, int]:
    return (_BASE_H, _BASE_W) if turns % 2 == 0 else (_BASE_W, _BASE_H)


def _place_template(
    grid: list[list[int]],
    clear_colors: tuple[int, ...],
    blocked_color: int | None,
    rng,
) -> None:
    turns = rng.randrange(4)
    reflect = bool(rng.randrange(2))
    th, tw = _transformed_size(turns)
    row0 = rng.randint(0, len(grid) - th)
    col0 = rng.randint(0, len(grid[0]) - tw)

    def lift(point: tuple[int, int]) -> tuple[int, int]:
        r, c = _transform_point(point, turns, reflect)
        return row0 + r, col0 + c

    for path, color in zip(_BASE_CLEAR_PATHS, clear_colors):
        for point in (path[0], path[-1]):
            r, c = lift(point)
            if grid[r][c] != 0:
                raise RuntimeError("constructive clear endpoints overlapped")
            grid[r][c] = color

    if blocked_color is not None:
        for point in (_BASE_BLOCKED_PATH[0], _BASE_BLOCKED_PATH[-1]):
            r, c = lift(point)
            if grid[r][c] != 0:
                raise RuntimeError("constructive blocked endpoints overlapped")
            grid[r][c] = blocked_color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w = _draw_dimensions(ctx)
    n = _draw_n(ctx)
    has_explicit_override = any(value is not None for value in overrides.values())
    include_blocked = has_explicit_override or sample_index % LESSON_SCHEDULE_PERIOD not in _CLEAR_ONLY_RESIDUES
    colors = ctx.draw_distinct_colors(
        "colors", n=n + int(include_blocked), exclude={0}
    )

    grid = full_grid(h, w, 0)
    blocked_color = colors[-1] if include_blocked else None
    clear_colors = colors[:-1] if include_blocked else colors
    _place_template(grid, clear_colors, blocked_color, ctx.draw_rng("layout"))

    expected = {"grid_h": h, "grid_w": w, "n": n}
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(f"constructed axes drifted: expected {expected}, observed {observed}")
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": expected})
    if errors:
        raise RuntimeError("constructed invalid grid: " + "; ".join(errors))
    return grid


def _segment(a: tuple[int, int], b: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    (r1, c1), (r2, c2) = a, b
    if r1 == r2:
        lo, hi = sorted((c1, c2))
        return tuple((r1, c) for c in range(lo, hi + 1))
    if c1 == c2:
        lo, hi = sorted((r1, r2))
        return tuple((r, c1) for r in range(lo, hi + 1))
    return ()


def _basic_grid_errors(grid: Any) -> list[str]:
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


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _basic_grid_errors(grid)
    if errors:
        return {
            "errors": errors,
            "by_color": {},
            "clear": [],
            "blocked": [],
            "unaligned": [],
        }

    h, w = len(grid), len(grid[0])
    if not 7 <= h <= 16:
        errors.append(f"grid height must be 7..16, got {h}")
    if not 9 <= w <= 18:
        errors.append(f"grid width must be 9..18, got {w}")

    by_color: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                by_color[value].append((r, c))

    if not by_color:
        errors.append("expected at least one clear endpoint pair")
        return {
            "errors": errors,
            "by_color": dict(by_color),
            "clear": [],
            "blocked": [],
            "unaligned": [],
        }

    clear: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    unaligned: list[dict[str, Any]] = []
    for color, cells in sorted(by_color.items()):
        if len(cells) != 2:
            errors.append(f"color {color} appears {len(cells)} times, expected two endpoints")
            continue
        a, b = cells
        path = _segment(a, b)
        record = {"color": color, "a": a, "b": b, "cells": tuple(cells), "path": path}
        if not path:
            errors.append(f"color {color} endpoints are not row/column aligned")
            unaligned.append(record)
            continue
        blockers = tuple(point for point in path[1:-1] if grid[point[0]][point[1]] != 0)
        record["blockers"] = blockers
        (blocked if blockers else clear).append(record)

    for index, first in enumerate(clear):
        for second in clear[index + 1 :]:
            if set(first["path"]) & set(second["path"]):
                errors.append("clear paths must be pairwise disjoint")

    return {
        "errors": errors,
        "by_color": dict(by_color),
        "clear": clear,
        "blocked": blocked,
        "unaligned": unaligned,
    }


def observe_overrides(grid) -> dict[str, int]:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n": len(info["clear"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    info = _analyze(grid)
    errors = list(info["errors"])
    if errors:
        return errors

    clear = info["clear"]
    blocked = info["blocked"]
    if not 1 <= len(clear) <= 5:
        errors.append(f"expected 1..5 clear pairs, found {len(clear)}")
    if len(blocked) > 1:
        errors.append(f"expected at most one blocked pair, found {len(blocked)}")
    if blocked:
        blockers = blocked[0]["blockers"]
        if len(blockers) != 1:
            errors.append("blocked pair must have exactly one nonzero interior cell")
        elif not any(blockers[0] in (record["a"], record["b"]) for record in clear):
            errors.append("blocked pair's blocker must be an endpoint of a clear pair")

    if meta and isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid) if not errors else {}
            for name, value in requested.items():
                if name in AXES and value is not None and observed.get(name) != value:
                    errors.append(f"{name} requested {value!r}, observed {observed.get(name)!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept canonical clear-only inputs and this sampler's blocked lessons."""
    return self_check(grid)


def _colors_reading_order(grid) -> list[int]:
    colors: list[int] = []
    for row in grid:
        for value in row:
            if value != 0 and value not in colors:
                colors.append(value)
    return colors


def rule_mirror(grid, *, ignore_blockers: bool = False):
    """Pure Python oracle for tests; the pinned selected Racket rule is authority."""
    errors = _basic_grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = full_grid(len(grid), len(grid[0]), 0)
    for color in _colors_reading_order(grid):
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        if len(cells) != 2:
            continue
        path = _segment(cells[0], cells[1])
        if not path:
            continue
        if ignore_blockers or all(grid[r][c] == 0 for r, c in path[1:-1]):
            for r, c in path:
                out[r][c] = color
    return out


def _ignore_clearance(grid):
    """Rival: incorrectly connects aligned pairs through nonzero interiors."""
    return rule_mirror(grid, ignore_blockers=True)


def _has_blocked_pair(grid) -> bool:
    info = _analyze(grid)
    return not info["errors"] and len(info["blocked"]) == 1


SEMANTIC_WITNESSES = {"blocked_pair": _has_blocked_pair}
SEMANTIC_RIVALS = {"ignore_clearance": _ignore_clearance}
WITNESS_RIVALS = {"blocked_pair": ["ignore_clearance"]}
CANONICAL_SHORTCUTS = {"ignore_clearance": _ignore_clearance}
LESSON_COMPETITORS = {"ignore_clearance": _ignore_clearance}
