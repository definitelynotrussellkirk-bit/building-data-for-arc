"""Generator for ARC task ``d4d38f319c8f``.

Column zero is a row-local header.  Its value says how many columns every
nonzero content cell in that row moves to the right.  Content shifted beyond
the right edge disappears; column zero itself is preserved.

The default distribution deliberately includes the canonical 4/5x7 profile,
including its clipped-cell branch, plus larger lawful generalizations.  Exact
axes are selected from a feasibility table before any keyed draw, so accepted
overrides are never silently clamped or replaced.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "d4d38f319c8f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "a0b3f7fef2e8"

SUMMARY = (
    "Preserve each row's column-zero shift header and move every nonzero "
    "content cell right by that row's header value, clipping cells that leave "
    "the grid."
)

INVARIANTS = [
    "column zero contains one shift in 1..8 for every row",
    "every row contains the same declared 1..5 nonzero content-cell count",
    "the maximum header value equals the declared max_shift axis",
    "when max_shift is greater than one, at least two row shifts differ",
    "every returned grid contains content that survives the right shift",
    "clip_mode exactly controls whether zero, some, or every row loses content",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 4..5 prior or difficulty-weighted 4..14",
        "valid": "4..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 7 prior or difficulty-weighted 7..20",
        "valid": "7..20",
    },
    "n_cells": {
        "type": "int",
        "default": "canonical 2 prior or difficulty-weighted 2..5",
        "valid": "1..5",
    },
    "max_shift": {
        "type": "int",
        "default": "canonical 3 prior or difficulty-weighted 1..8",
        "valid": "1..8",
    },
    "palette_size": {
        "type": "int",
        "default": "canonical 5..7 prior or difficulty-weighted 3..9",
        "valid": "1..9",
    },
    "clip_mode": {
        "type": "str",
        "default": "canonical some prior or difficulty-weighted",
        "valid": "none|some|all_rows",
    },
}

_AXIS_ORDER = tuple(AXES)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the Racket rule owns the output."""
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    canonical_prior = (
        not overrides
        and ctx.draw_rng("canonical_prior").random() < 0.40
    )
    constraints = tuple(
        overrides.get(axis)
        if axis in overrides and overrides.get(axis) is not None
        else None
        for axis in _AXIS_ORDER
    )
    option_index = _feasible_option_index(
        _band(difficulty), canonical_prior, bool(overrides), constraints
    )
    if not option_index:
        raise ValueError("no feasible configuration for the requested axes")

    selected: dict[str, object] = {}
    prefix: tuple[object, ...] = ()
    for axis in _AXIS_ORDER:
        options = option_index.get(prefix, ())
        if not options:
            raise ValueError(f"requested {axis} combination is infeasible")
        value = ctx.draw_choice(axis, options)
        selected[axis] = value
        prefix += (value,)

    h = int(selected["grid_h"])
    w = int(selected["grid_w"])
    n_cells = int(selected["n_cells"])
    max_shift = int(selected["max_shift"])
    palette_size = int(selected["palette_size"])
    clip_mode = str(selected["clip_mode"])

    layout_rng = ctx.draw_rng("layout")
    shifts, clipped_rows = _shift_and_clip_plan(
        h,
        w,
        n_cells,
        max_shift,
        clip_mode,
        canonical_prior,
        layout_rng,
    )
    positions: list[tuple[int, int]] = []
    for row, shift in enumerate(shifts):
        surviving = list(range(1, w - shift))
        clipped = list(range(w - shift, w))
        if row in clipped_rows:
            chosen = [layout_rng.choice(surviving), layout_rng.choice(clipped)]
            remaining = [
                column
                for column in range(1, w)
                if column not in chosen
            ]
            layout_rng.shuffle(remaining)
            chosen.extend(remaining[: n_cells - 2])
        else:
            layout_rng.shuffle(surviving)
            chosen = surviving[:n_cells]
        if len(chosen) != n_cells:
            raise ValueError("failed to place the exact requested content count")
        positions.extend((row, column) for column in chosen)

    palette = list(
        ctx.draw_distinct_colors(
            "content_palette",
            n=palette_size,
            exclude={0},
        )
    )
    color_rng = ctx.draw_rng("color_assignment")
    colors = palette + [
        color_rng.choice(palette)
        for _ in range(len(positions) - len(palette))
    ]
    color_rng.shuffle(colors)

    grid = full_grid(h, w, 0)
    for row, shift in enumerate(shifts):
        grid[row][0] = shift
    for (row, column), color in zip(positions, colors):
        grid[row][column] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid generator instance: {errors}")
    return [row[:] for row in grid]


def _band(difficulty) -> str:
    return difficulty if difficulty in {"easy", "medium", "hard"} else "medium"


def _axis_domain(axis: str, band: str, canonical: bool, explicit: bool):
    if canonical:
        return {
            "grid_h": (4, 5),
            "grid_w": (7,),
            "n_cells": (2,),
            "max_shift": (3,),
            "palette_size": (5, 6, 7),
            "clip_mode": ("some",),
        }[axis]
    if explicit:
        return {
            "grid_h": tuple(range(4, 15)),
            "grid_w": tuple(range(7, 21)),
            "n_cells": tuple(range(1, 6)),
            "max_shift": tuple(range(1, 9)),
            "palette_size": tuple(range(1, 10)),
            "clip_mode": ("none", "some", "all_rows"),
        }[axis]
    domains = {
        "easy": {
            "grid_h": tuple(range(4, 7)),
            "grid_w": tuple(range(7, 11)),
            "n_cells": (2, 3),
            "max_shift": (1, 2, 3),
            "palette_size": (3, 4, 5, 6),
            "clip_mode": ("none", "some"),
        },
        "medium": {
            "grid_h": tuple(range(5, 11)),
            "grid_w": tuple(range(9, 16)),
            "n_cells": (2, 3, 4),
            "max_shift": (2, 3, 4, 5),
            "palette_size": (4, 5, 6, 7, 8),
            "clip_mode": ("none", "some", "all_rows"),
        },
        "hard": {
            "grid_h": tuple(range(8, 15)),
            "grid_w": tuple(range(12, 21)),
            "n_cells": (3, 4, 5),
            "max_shift": (3, 4, 5, 6, 7, 8),
            "palette_size": (5, 6, 7, 8, 9),
            "clip_mode": ("some", "all_rows"),
        },
    }
    return domains[band][axis]


@lru_cache(maxsize=None)
def _feasible_configs(band: str, canonical: bool, explicit: bool):
    domains = {
        axis: _axis_domain(axis, band, canonical, explicit)
        for axis in _AXIS_ORDER
    }
    configs = []
    for h in domains["grid_h"]:
        for w in domains["grid_w"]:
            for n_cells in domains["n_cells"]:
                if n_cells > w - 2:
                    continue
                for max_shift in domains["max_shift"]:
                    if max_shift > w - 2:
                        continue
                    for palette_size in domains["palette_size"]:
                        if palette_size > h * n_cells:
                            continue
                        for clip_mode in domains["clip_mode"]:
                            if clip_mode != "none" and n_cells < 2:
                                continue
                            if (
                                clip_mode == "none"
                                and max_shift + n_cells > w - 1
                            ):
                                continue
                            configs.append(
                                (
                                    h,
                                    w,
                                    n_cells,
                                    max_shift,
                                    palette_size,
                                    clip_mode,
                                )
                            )
    return tuple(configs)


@lru_cache(maxsize=None)
def _feasible_option_index(
    band: str,
    canonical: bool,
    explicit: bool,
    constraints: tuple[object | None, ...],
) -> dict[tuple[object, ...], tuple[object, ...]]:
    """Map every feasible axis prefix to its legal next values.

    The override checker executes thousands of draws.  Re-filtering the full
    Cartesian feasibility table on every draw is quadratic work; this immutable
    prefix index pays that cost once per process and keeps every accepted or
    rejected override decision exactly the same.
    """
    staged: dict[tuple[object, ...], set[object]] = {}
    for config in _feasible_configs(band, canonical, explicit):
        if any(
            constraint is not None and config[index] != constraint
            for index, constraint in enumerate(constraints)
        ):
            continue
        for index, value in enumerate(config):
            staged.setdefault(config[:index], set()).add(value)
    return {
        prefix: tuple(sorted(values))
        for prefix, values in staged.items()
    }


def _shift_and_clip_plan(
    h: int,
    w: int,
    n_cells: int,
    max_shift: int,
    clip_mode: str,
    canonical: bool,
    rng,
) -> tuple[list[int], set[int]]:
    if clip_mode == "none":
        clipped_rows: set[int] = set()
    elif clip_mode == "all_rows":
        clipped_rows = set(range(h))
    elif clip_mode == "some":
        if canonical:
            clipped_rows = {rng.randrange(h)}
        else:
            count = rng.randint(1, h - 1)
            clipped_rows = set(rng.sample(range(h), count))
    else:
        raise ValueError(f"unknown clip_mode {clip_mode!r}")

    no_clip_max = w - 1 - n_cells
    if clip_mode == "none" and max_shift > no_clip_max:
        raise ValueError("max_shift leaves too few surviving columns for clip_mode=none")

    if canonical:
        shifts = [1, 2, 3]
        shifts.extend(rng.randint(1, 3) for _ in range(h - 3))
        rng.shuffle(shifts)
    else:
        shifts = []
        for row in range(h):
            upper = max_shift if row in clipped_rows else min(max_shift, no_clip_max)
            if upper < 1:
                raise ValueError("non-clipped row has no feasible shift")
            shifts.append(rng.randint(1, upper))
        max_row = next(iter(clipped_rows), 0)
        shifts[max_row] = max_shift
        if max_shift > 1 and h > 1:
            other = 1 if max_row != 1 else 0
            shifts[other] = 1
    return shifts, clipped_rows


def profile_signature(grid) -> dict[str, object]:
    """Extract every exact axis and rule-linked branch from a returned grid."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("grid must be a non-empty 2D list")
    h, w = len(grid), len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("grid colors must be integers in 0..9")

    shifts = [row[0] for row in grid]
    row_content_counts = [sum(value != 0 for value in row[1:]) for row in grid]
    content_colors = {
        value for row in grid for value in row[1:] if value != 0
    }
    surviving_cells = 0
    clipped_cells = 0
    clipped_rows = 0
    rows_with_survivors = 0
    for row, shift in zip(grid, shifts):
        row_survivors = 0
        row_clipped = 0
        for column, value in enumerate(row[1:], 1):
            if value == 0:
                continue
            if isinstance(shift, int) and column + shift < w:
                surviving_cells += 1
                row_survivors += 1
            else:
                clipped_cells += 1
                row_clipped += 1
        rows_with_survivors += bool(row_survivors)
        clipped_rows += bool(row_clipped)
    if clipped_rows == 0:
        clip_mode = "none"
    elif clipped_rows == h:
        clip_mode = "all_rows"
    else:
        clip_mode = "some"
    uniform_n_cells = (
        row_content_counts[0]
        if row_content_counts and len(set(row_content_counts)) == 1
        else None
    )
    return {
        "grid_h": h,
        "grid_w": w,
        "n_cells": uniform_n_cells,
        "max_shift": max(shifts) if shifts else None,
        "palette_size": len(content_colors),
        "clip_mode": clip_mode,
        "shifts": shifts,
        "shift_values": sorted(set(shifts)),
        "row_content_counts": row_content_counts,
        "content_colors": sorted(content_colors),
        "surviving_cells": surviving_cells,
        "clipped_cells": clipped_cells,
        "clipped_rows": clipped_rows,
        "rows_with_survivors": rows_with_survivors,
        "zero_count": sum(value == 0 for row in grid for value in row),
    }


def observe_overrides(grid) -> dict[str, object]:
    feature = profile_signature(grid)
    return {axis: feature[axis] for axis in _AXIS_ORDER}


def is_canonical_like(grid) -> bool:
    """Strict joint predicate matching all five official input profiles."""
    feature = profile_signature(grid)
    h = int(feature["grid_h"])
    return bool(
        h in (4, 5)
        and feature["grid_w"] == 7
        and feature["n_cells"] == 2
        and feature["max_shift"] == 3
        and feature["shift_values"] == [1, 2, 3]
        and 5 <= int(feature["palette_size"]) <= 7
        and feature["clip_mode"] == "some"
        and feature["clipped_rows"] == 1
        and feature["clipped_cells"] == 1
        and feature["surviving_cells"] == 2 * h - 1
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-prone row-header shift lessons."""
    del difficulty, meta
    try:
        feature = profile_signature(grid)
    except ValueError as exc:
        return [str(exc)]
    errors: list[str] = []
    h = int(feature["grid_h"])
    w = int(feature["grid_w"])
    if not 4 <= h <= 14 or not 7 <= w <= 20:
        errors.append(f"grid dimensions must be 4..14 by 7..20, got {h}x{w}")
    shifts = feature["shifts"]
    if any(
        not isinstance(shift, int)
        or isinstance(shift, bool)
        or not 1 <= shift <= min(8, w - 2)
        for shift in shifts
    ):
        errors.append("column zero must contain shifts in 1..min(8, width-2)")
    counts = feature["row_content_counts"]
    if any(not 1 <= count <= 5 for count in counts):
        errors.append("every row must contain 1..5 nonzero content cells")
    if feature["n_cells"] is None:
        errors.append("every row must contain the same exact content-cell count")
    if any(count > w - 2 for count in counts):
        errors.append("every row must retain at least one background content cell")
    if feature["palette_size"] < 1:
        errors.append("the content area must contain at least one nonzero color")
    if feature["surviving_cells"] < 1:
        errors.append("at least one content cell must survive the declared shifts")
    if feature["max_shift"] and feature["max_shift"] > 1 and len(feature["shift_values"]) < 2:
        errors.append("multi-valued headers must vary between rows")
    return errors
