"""Generator for ARC task c8138b7e476c (mirror above a 9-row separator).

The sampler keeps every advertised override exact and observable. Ordinary draws
mix three canonical-linked profiles with a broader lawful distribution, while
all generated inputs contain a vertical-order witness that distinguishes true
reflection from merely copying the top rows downward in their original order.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c8138b7e476c"
TASK_ID = GENERATOR_ID
RULE_HASH = "df62a46d5c10"
VERSION = "3.0.0"
SUMMARY = (
    "Odd-height 0-background grids contain a centered full row of maroon 9s. "
    "Two to four source colors occupy 4..12 cells above the separator, with "
    "witness cells at both vertical extremes. The unchanged rule reflects the "
    "entire top half into the bottom half in reversed row order."
)

INVARIANTS = [
    "the grid is rectangular with a single centered full separator row of 9s",
    "all cells below the separator are 0 before transformation",
    "source cells above the separator use colors 1..8",
    "ordinary draws realize every declared exact override without clipping",
    "ordinary draws are vertically asymmetric, distinguishing reflection from copy-in-order",
]

_GRID_HEIGHTS = (7, 9, 11, 13)
_GRID_WIDTHS = tuple(range(7, 13))
_CELL_COUNTS = tuple(range(4, 13))
_COLOR_COUNTS = (2, 3, 4)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-linked 7|9 plus broad 7|9|11|13",
        "valid": "7|9|11|13",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-linked 8|9|10 plus broad 7..12",
        "valid": "7..12",
    },
    "cells": {
        "type": "int",
        "default": "canonical-linked 4|5 plus broad 4..12",
        "valid": "4..12",
    },
    "n_colors": {
        "type": "int",
        "default": "canonical-linked 2|3 plus broad 2..4",
        "valid": "2..4",
    },
}

# Every boundary-matrix combination is constructive: the smallest top half has
# 3*7=21 slots, comfortably above the maximum 12 cells and 4 colors.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_CANONICAL_PROFILES = {
    "canonical_0": {
        "grid_h": 7,
        "grid_w": 8,
        "cells": 4,
        "n_colors": 2,
        "palette": (2, 6),
    },
    "canonical_1": {
        "grid_h": 9,
        "grid_w": 9,
        "cells": 4,
        "n_colors": 2,
        "palette": (3, 7),
    },
    "canonical_2": {
        "grid_h": 9,
        "grid_w": 10,
        "cells": 5,
        "n_colors": 3,
        "palette": (2, 4, 6),
    },
}
_PROFILE_OPTIONS = (
    "canonical_0",
    "canonical_1",
    "canonical_2",
    "canonical_0",
    "canonical_1",
    "canonical_2",
    "broad",
    "broad",
)


def _weighted_axis_options(name: str, difficulty: Any, preferred: int | None) -> tuple[int, ...]:
    allowed = {
        "grid_h": _GRID_HEIGHTS,
        "grid_w": _GRID_WIDTHS,
        "cells": _CELL_COUNTS,
        "n_colors": _COLOR_COUNTS,
    }[name]
    options = list(allowed)
    if preferred is not None:
        options.extend([preferred] * 12)
        return tuple(options)

    if difficulty == "easy":
        favored = {
            "grid_h": (7, 7, 7, 9),
            "grid_w": (7, 8, 8, 9),
            "cells": (4, 4, 5, 6),
            "n_colors": (2, 2, 2, 3),
        }[name]
    elif difficulty == "hard":
        favored = {
            "grid_h": (9, 11, 13, 13),
            "grid_w": (9, 10, 11, 12),
            "cells": (7, 9, 11, 12),
            "n_colors": (3, 3, 4, 4),
        }[name]
    else:
        favored = {
            "grid_h": (7, 9, 9, 11),
            "grid_w": (8, 9, 10, 11),
            "cells": (4, 5, 6, 8),
            "n_colors": (2, 2, 3, 4),
        }[name]
    options.extend(favored * 2)
    return tuple(options)


def _palette(profile_name: str, n_colors: int, rng) -> tuple[int, ...]:
    base = list(_CANONICAL_PROFILES.get(profile_name, {}).get("palette", ()))
    colors: list[int] = []
    for color in base:
        if color not in colors and len(colors) < n_colors:
            colors.append(color)
    remaining = [color for color in range(1, 9) if color not in colors]
    rng.shuffle(remaining)
    colors.extend(remaining[: n_colors - len(colors)])
    return tuple(colors)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} override must be an integer, not {type(value).__name__}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile_name = ctx.draw_choice("curriculum_profile", _PROFILE_OPTIONS)
    profile = _CANONICAL_PROFILES.get(profile_name, {})

    h = ctx.draw_choice(
        "grid_h",
        _weighted_axis_options("grid_h", difficulty, profile.get("grid_h")),
    )
    w = ctx.draw_choice(
        "grid_w",
        _weighted_axis_options("grid_w", difficulty, profile.get("grid_w")),
    )
    cells = ctx.draw_choice(
        "cells",
        _weighted_axis_options("cells", difficulty, profile.get("cells")),
    )
    n_colors = ctx.draw_choice(
        "n_colors",
        _weighted_axis_options("n_colors", difficulty, profile.get("n_colors")),
    )

    half = h // 2
    grid = full_grid(h, w, 0)
    grid[half] = [9] * w

    layout_rng = ctx.draw_rng("layout")
    witness_col = layout_rng.randrange(w)
    near_col = layout_rng.choice([col for col in range(w) if col != witness_col])
    anchors = [(0, witness_col), (half - 1, near_col)]

    # Keep the vertical partner of the top witness blank. This makes the top
    # half observably asymmetric, so reverse-order reflection and copy-in-order
    # cannot agree by accident.
    forbidden = {(half - 1, witness_col)}
    candidates = [
        (row, col)
        for row in range(half)
        for col in range(w)
        if (row, col) not in set(anchors) | forbidden
    ]
    chosen = anchors + layout_rng.sample(candidates, cells - len(anchors))

    colors = _palette(profile_name, n_colors, ctx.draw_rng("palette"))
    assignments = list(colors)
    color_rng = ctx.draw_rng("cell_colors")
    assignments.extend(color_rng.choice(colors) for _ in range(cells - len(colors)))
    color_rng.shuffle(assignments)
    layout_rng.shuffle(chosen)
    for (row, col), color in zip(chosen, assignments):
        grid[row][col] = color
    return grid


def _grid_shape_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return ["every grid row must be a sequence"]
    width = len(grid[0])
    if width == 0:
        return ["grid rows must be non-empty"]
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid cells must be integer ARC colors 0..9"]
    return []


def _separator_row(grid) -> int:
    width = len(grid[0])
    rows = [row for row in range(len(grid)) if all(grid[row][col] == 9 for col in range(width))]
    if len(rows) != 1:
        raise ValueError(f"expected exactly one full separator row of 9s, found {len(rows)}")
    return rows[0]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task law without assuming a particular sampled profile."""
    errors = _grid_shape_errors(grid)
    if errors:
        return errors

    height = len(grid)
    width = len(grid[0])
    full_rows = [
        row for row in range(height) if all(grid[row][col] == 9 for col in range(width))
    ]
    if len(full_rows) != 1:
        return [f"expected exactly one full separator row of 9s, found {len(full_rows)}"]
    separator = full_rows[0]
    if height != 2 * separator + 1:
        errors.append("separator must be centered with equal space above and below")

    stray_nines = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if row != separator and grid[row][col] == 9
    ]
    if stray_nines:
        errors.append(f"color 9 may appear only in the separator row; first stray at {stray_nines[0]}")

    bad_bottom = [
        (row, col)
        for row in range(separator + 1, height)
        for col in range(width)
        if grid[row][col] != 0
    ]
    if bad_bottom:
        errors.append(f"bottom half must be all 0 before mirroring; first nonzero at {bad_bottom[0]}")

    source = [
        grid[row][col]
        for row in range(separator)
        for col in range(width)
        if grid[row][col] != 0
    ]
    if not source:
        errors.append("top half must contain at least one source cell")
    elif any(not 1 <= color <= 8 for color in source):
        errors.append("top-half source colors must lie in 1..8")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides on invalid grid: " + "; ".join(errors))
    separator = _separator_row(grid)
    source = [
        grid[row][col]
        for row in range(separator)
        for col in range(len(grid[0]))
        if grid[row][col] != 0
    ]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "cells": len(source),
        "n_colors": len(set(source)),
    }


def _mirror_top(grid):
    """Independent Python oracle for tests and semantic-rival checks."""
    separator = _separator_row(grid)
    output = deepcopy(grid)
    for row in range(separator):
        output[2 * separator - row] = list(grid[row])
    return output


def _copy_top_in_order(grid):
    """Plausible wrong rule: copy top rows downward without reversing them."""
    separator = _separator_row(grid)
    output = deepcopy(grid)
    for row in range(separator):
        output[separator + 1 + row] = list(grid[row])
    return output


def _vertical_order_matters(grid) -> bool:
    try:
        return _mirror_top(grid) != _copy_top_in_order(grid)
    except (TypeError, ValueError, IndexError):
        return False


def strict_canonical_like(grid) -> list[str]:
    errors = list(self_check(grid))
    if errors:
        return errors
    observed = observe_overrides(grid)
    if observed["grid_h"] not in _GRID_HEIGHTS:
        errors.append(f"grid_h={observed['grid_h']} outside reviewed profile")
    if observed["grid_w"] not in _GRID_WIDTHS:
        errors.append(f"grid_w={observed['grid_w']} outside reviewed profile")
    if observed["cells"] not in _CELL_COUNTS:
        errors.append(f"cells={observed['cells']} outside reviewed profile")
    if observed["n_colors"] not in _COLOR_COUNTS:
        errors.append(f"n_colors={observed['n_colors']} outside reviewed profile")
    if not _vertical_order_matters(grid):
        errors.append("top half is vertically symmetric, so row order is not taught")
    return errors


MIN_STRICT_FRAC = 1.0
SEMANTIC_WITNESSES = {"vertical_order_matters": _vertical_order_matters}
SEMANTIC_RIVALS = {"copy_top_in_order": _copy_top_in_order}
WITNESS_RIVALS = {"vertical_order_matters": ["copy_top_in_order"]}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos: Iterable[dict], query: dict | None) -> list[str]:
    demos = list(demos)
    errors: list[str] = []
    for index, pair in enumerate(demos):
        grammar_errors = strict_canonical_like(pair["input"])
        if grammar_errors:
            errors.append(f"demo {index} is outside strict task support: {grammar_errors[0]}")

    if query is not None:
        grammar_errors = strict_canonical_like(query["input"])
        if grammar_errors:
            errors.append(f"query is outside strict task support: {grammar_errors[0]}")

    for name, competitor in LESSON_COMPETITORS.items():
        fits_demos = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if not fits_demos:
            continue
        if query is None or "output" not in query:
            errors.append(f"competitor {name} fits every demonstration")
        elif competitor(query["input"]) != query["output"]:
            errors.append(f"competitor {name} fits demonstrations but changes the query answer")
    return errors
