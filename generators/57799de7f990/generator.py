"""Input sampler for ARC task 57799de7f990: connect complete diamonds.

A marker center is recognized only when all four orthogonal neighbours are red
(color 2).  For every row and column, consecutive aligned centers are joined by
blue (color 1) through background cells.  The generator returns inputs only;
the selected Racket program remains the label authority.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "57799de7f990"
TASK_ID = GENERATOR_ID
RULE_HASH = "cd5434186fae"
VERSION = "3.0.0"
SUMMARY = (
    "A 9..26 zero-background grid contains 3..7 complete red diamonds. "
    "Consecutive centers sharing a row or column are connected through zero "
    "cells by blue lines. Alternating default lessons include an irregular "
    "three-arm false-center witness that refutes axis-local marker recognition."
)

INVARIANTS = [
    "every red cell is an arm of at least one complete four-arm diamond",
    "there are exactly 3..7 complete diamonds and at least one visible connection",
    "inputs contain only colors 0 and 2; color 1 is introduced only by the rule",
    "default consecutive lessons alternate rival-refuting witness and plain layouts",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile weighted", "valid": "9..26"},
    "grid_w": {"type": "int", "default": "canonical-profile weighted", "valid": "9..26"},
    "n_diamonds": {"type": "int", "default": "difficulty weighted", "valid": "3..7"},
    "three_arm_witness": {
        "type": "bool",
        "default": "alternates by sample_index",
        "valid": "false|true",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("three_arm_witness", "plain")

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_SHAPES = ((14, 16), (10, 15), (12, 15), (9, 15))
# Prefixes 3..7 retain the same axis-local shortcut separator.  The third
# center is placed at the far end of the long axis at construction time so
# large canvases still visibly demonstrate the transformation.
_WITNESS_PREFIX = ((2, 1), (3, 4))
_WITNESS_SUFFIXES = (
    ((1, 5), (3, 2), (3, 6), (4, 1)),
    ((3, 2), (1, 5), (3, 6), (4, 1)),
    ((3, 6), (1, 3), (3, 2), (4, 1)),
    ((4, 2), (1, 5), (3, 6), (4, 5)),
    ((5, 1), (1, 5), (3, 2), (3, 6)),
    ((5, 4), (1, 5), (4, 2), (5, 1)),
    ((6, 1), (1, 5), (3, 2), (1, 3)),
    ((7, 7), (1, 5), (3, 2), (3, 6)),
)
# Index-space layout; any 3x3 row/column embedding with gaps >=3 is shortcut-neutral.
_PLAIN_INDEXES = ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2))


def schedule_profile(seed, sample_index, difficulty=None):
    """Stable two-profile schedule; seed/difficulty do not alias its coverage."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "n_diamonds"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
    value = overrides.get("three_arm_witness")
    if value is not None and type(value) is not bool:
        raise TypeError("three_arm_witness must be a bool")


def _weighted_exact_int(ctx, name, lo, hi, anchor, repeats=384):
    """Keep the whole exact override domain while strongly anchoring a profile."""
    return ctx.draw_choice(name, tuple(range(lo, hi + 1)) + (anchor,) * repeats)


def _transform_square(point, size, orientation):
    r, c = point
    if orientation >= 4:
        c = size - 1 - c
    for _ in range(orientation % 4):
        r, c = c, size - 1 - r
    return r, c


def _put_diamond(grid, r, c):
    for dr, dc in _CARDINAL:
        grid[r + dr][c + dc] = 2


def _gapped_triplets(length):
    """Three legal coordinates that span the canvas instead of clustering."""
    return tuple((1, middle, length - 2) for middle in range(4, length - 4))


def _plain_centers(ctx, h, w, count):
    rows = ctx.draw_rng("plain_rows").choice(_gapped_triplets(h))
    cols = ctx.draw_rng("plain_columns").choice(_gapped_triplets(w))
    orientation = ctx.draw_rng("plain_orientation").randrange(8)
    result = []
    for point in _PLAIN_INDEXES[:count]:
        i, j = _transform_square(point, 3, orientation)
        result.append((rows[i], cols[j]))
    return result


def _witness_centers(ctx, h, w, count):
    """Embed a rival-refuting witness along the canvas's full long axis."""
    if h == w:
        horizontal = bool(ctx.draw_rng("witness_axis").randrange(2))
    else:
        horizontal = w > h
    long_size = w if horizontal else h
    suffix = ctx.draw_rng("witness_variant").choice(_WITNESS_SUFFIXES)
    centers = (
        _WITNESS_PREFIX
        + ((2, long_size - 2),)
        + suffix
    )[:count]

    mirror_short = bool(ctx.draw_rng("witness_mirror_short").randrange(2))
    mirror_long = bool(ctx.draw_rng("witness_mirror_long").randrange(2))
    transformed = []
    for r, c in centers:
        if mirror_short:
            r = 8 - r
        if mirror_long:
            c = long_size - 1 - c
        transformed.append((r, c))

    if horizontal:
        top = ctx.draw_rng("witness_short_offset").randrange(h - 8)
        return [(top + r, c) for r, c in transformed]
    left = ctx.draw_rng("witness_short_offset").randrange(w - 8)
    return [(c, left + r) for r, c in transformed]


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

    anchor_h, anchor_w = _CANONICAL_SHAPES[sample_index % len(_CANONICAL_SHAPES)]
    h = _weighted_exact_int(ctx, "grid_h", 9, 26, anchor_h)
    w = _weighted_exact_int(ctx, "grid_w", 9, 26, anchor_w)
    count_anchor = {
        "easy": 3 + (sample_index % 2),
        "medium": 4 + (sample_index % 2),
        "hard": 6 + (sample_index % 2),
        None: 3 + (sample_index % 5),
    }[difficulty]
    count = _weighted_exact_int(ctx, "n_diamonds", 3, 7, count_anchor, repeats=32)

    scheduled_witness = schedule_profile(seed, sample_index, difficulty) == "three_arm_witness"
    if overrides.get("three_arm_witness") is None:
        witness = ctx.draw_choice("three_arm_witness", (scheduled_witness,))
    else:
        witness = ctx.draw_choice("three_arm_witness", (False, True))

    grid = full_grid(h, w, 0)
    centers = (
        _witness_centers(ctx, h, w, count)
        if witness
        else _plain_centers(ctx, h, w, count)
    )
    for r, c in centers:
        _put_diamond(grid, r, c)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructive sampler violated its contract: {errors}")
    return grid


def _diamond_centers(grid):
    h, w = len(grid), len(grid[0])
    return [
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if all(grid[r + dr][c + dc] == 2 for dr, dc in _CARDINAL)
    ]


def _paint_consecutive(grid, horizontal, vertical):
    out = deepcopy(grid)
    for r, columns in horizontal.items():
        ordered = sorted(set(columns))
        for left, right in zip(ordered, ordered[1:]):
            for c in range(left + 1, right):
                if out[r][c] == 0:
                    out[r][c] = 1
    for c, rows in vertical.items():
        ordered = sorted(set(rows))
        for top, bottom in zip(ordered, ordered[1:]):
            for r in range(top + 1, bottom):
                if out[r][c] == 0:
                    out[r][c] = 1
    return out


def _intended(grid):
    horizontal = defaultdict(list)
    vertical = defaultdict(list)
    for r, c in _diamond_centers(grid):
        horizontal[r].append(c)
        vertical[c].append(r)
    return _paint_consecutive(grid, horizontal, vertical)


def _axis_local_three_arm(grid):
    """Rival: two axial arms plus only one perpendicular arm define a center."""
    h, w = len(grid), len(grid[0])
    horizontal = defaultdict(list)
    vertical = defaultdict(list)
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if (grid[r][c - 1] == grid[r][c + 1] == 2
                    and (grid[r - 1][c] == 2 or grid[r + 1][c] == 2)):
                horizontal[r].append(c)
            if (grid[r - 1][c] == grid[r + 1][c] == 2
                    and (grid[r][c - 1] == 2 or grid[r][c + 1] == 2)):
                vertical[c].append(r)
    return _paint_consecutive(grid, horizontal, vertical)


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]

    h, w = len(grid), width
    errors = []
    if not (9 <= h <= 26 and 9 <= w <= 26):
        errors.append(f"grid dimensions {(h, w)} outside 9..26")
    if any(type(value) is not int or value not in (0, 2) for row in grid for value in row):
        errors.append("input cells must be exact integer colors 0 or 2")
        return errors

    centers = _diamond_centers(grid)
    if not 3 <= len(centers) <= 7:
        errors.append(f"n_diamonds={len(centers)} outside 3..7")
    center_set = set(centers)
    nonempty_centers = [point for point in centers if grid[point[0]][point[1]] != 0]
    if nonempty_centers:
        errors.append(f"diamond centers must be background; found {nonempty_centers[:3]}")

    stray = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 2:
                continue
            if not any((r - dr, c - dc) in center_set for dr, dc in _CARDINAL):
                stray.append((r, c))
    if stray:
        errors.append(f"red cells not owned by a complete diamond: {stray[:3]}")

    if not errors and _intended(grid) == [list(row) for row in grid]:
        errors.append("no aligned diamond pair creates a visible connection")
    return errors


def strict_canonical_like(grid):
    """Lawful complete-diamond instances in the declared sampler domain."""
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe invalid grid: {errors}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_diamonds": len(_diamond_centers(grid)),
        "three_arm_witness": _intended(grid) != _axis_local_three_arm(grid),
    }


def _has_three_arm_false_center(grid):
    return _intended(grid) != _axis_local_three_arm(grid)


SEMANTIC_RIVALS = {"axis_local_three_arm": _axis_local_three_arm}
CANONICAL_SHORTCUTS = {"axis_local_three_arm": _axis_local_three_arm}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {"three_arm_false_center": _has_three_arm_false_center}
WITNESS_RIVALS = {"three_arm_false_center": ["axis_local_three_arm"]}


def lesson_identifiable(demos, query):
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
            changes_query = rival(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"competitor {name} fits every demo but changes the query answer")
    return reasons
