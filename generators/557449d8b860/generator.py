"""Reviewed generator for ARC task 557449d8b860 — column gravity.

The selected rule is ``(rule! (gravity g "down"))``: within each column,
remove the background gaps and place the nonzero cells against the bottom edge
without changing their top-to-bottom order.

The public override surface contains only quantities that can be recovered
exactly from a returned grid.  Internal scene modes deliberately exercise
canonical-scale sparse inputs, deep stacks, and columns that already touch the
floor but still contain gaps above that floor contact.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "557449d8b860"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "c3638032481f"

SUMMARY = (
    "Place 5..10 colored cells in 2..4 columns of a 6..10 grid.  Applying "
    "gravity independently to each column packs its cells against the bottom "
    "while preserving their top-to-bottom color order."
)

INVARIANTS = [
    "grid dimensions are 6..10 by 6..10",
    "there are exactly 5..10 nonzero cells in exactly 2..4 occupied columns",
    "the foreground uses exactly 2..5 distinct nonzero ARC colors",
    "at least one multicolor stack makes within-column order observable",
    "at least one cell moves under downward gravity",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "full-support weighted draw with canonical-profile prior",
        "valid": "6..10",
    },
    "grid_w": {
        "type": "int",
        "default": "full-support weighted draw with canonical-profile prior",
        "valid": "6..10",
    },
    "n_cells": {
        "type": "int",
        "default": "full-support difficulty-biased draw",
        "valid": "5..10",
    },
    "n_occupied_columns": {
        "type": "int",
        "default": "full-support draw with a three-column prior",
        "valid": "2..4",
    },
    "palette_size": {
        "type": "int",
        "default": "full-support draw with canonical four/five-color prior",
        "valid": "2..5",
    },
}

# Every value in the Cartesian product above is constructively realizable.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Official inputs occupy these (height, width, total palette including 0)
# profiles.  The ordinary distribution keeps a substantial prior on all four
# while retaining full support outside them in every difficulty band.
_CANONICAL_PROFILES = (
    (6, 6, 5, 5, 3),
    (7, 7, 5, 5, 3),
    (6, 8, 5, 5, 3),
    (8, 7, 6, 6, 3),
)
_CANONICAL_SHAPE_PALETTES = {
    (height, width, total_palette)
    for height, width, total_palette, _cells, _columns in _CANONICAL_PROFILES
}
MIN_STRICT_FRAC = 0.25


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["grid rows must be sequences"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]
    height = len(grid)
    if not 6 <= height <= 10:
        return [f"grid height must be in 6..10, found {height}"]
    if not 6 <= width <= 10:
        return [f"grid width must be in 6..10, found {width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers in 0..9"]
    return []


def _gravity_down(grid: list[list[int]] | tuple[tuple[int, ...], ...]) -> list[list[int]]:
    """Small Python mirror used only for validation and semantic witnesses."""
    height, width = len(grid), len(grid[0])
    out = [[0] * width for _ in range(height)]
    for column in range(width):
        values = [grid[row][column] for row in range(height) if grid[row][column] != 0]
        start = height - len(values)
        for offset, value in enumerate(values):
            out[start + offset][column] = value
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes and lawful-looking scenes that hide the rule."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    foreground = [
        (row, column, grid[row][column])
        for row in range(height)
        for column in range(width)
        if grid[row][column] != 0
    ]
    if not 5 <= len(foreground) <= 10:
        errors.append(f"foreground cell count must be in 5..10, found {len(foreground)}")

    occupied_columns = sorted({column for _row, column, _value in foreground})
    if not 2 <= len(occupied_columns) <= 4:
        errors.append(
            "occupied-column count must be in 2..4, "
            f"found {len(occupied_columns)}"
        )

    colors = {value for _row, _column, value in foreground}
    if not 2 <= len(colors) <= 5:
        errors.append(f"foreground palette size must be in 2..5, found {len(colors)}")

    has_order_witness = False
    for column in occupied_columns:
        values = [
            grid[row][column]
            for row in range(height)
            if grid[row][column] != 0
        ]
        if len(values) >= 2 and len(set(values)) >= 2:
            has_order_witness = True
            break
    if not has_order_witness:
        errors.append("at least one occupied column must contain two distinct colors")

    if not errors and _gravity_down(grid) == [list(row) for row in grid]:
        errors.append("input must contain at least one downward gravity movement")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Official empirical profile: lawful input with a canonical H/W/palette."""
    errors = self_check(grid)
    if errors:
        return errors
    profile = (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )
    if profile not in _CANONICAL_SHAPE_PALETTES:
        return [
            "canonical profiles are "
            f"{sorted(_CANONICAL_SHAPE_PALETTES)}, found {profile}"
        ]
    return []


def observe_overrides(grid) -> dict[str, int | None]:
    """Recover every public exact axis from a returned lawful grid."""
    if _grid_errors(grid):
        return {axis: None for axis in AXES}
    foreground = [value for row in grid for value in row if value != 0]
    occupied_columns = {
        column
        for column in range(len(grid[0]))
        if any(grid[row][column] != 0 for row in range(len(grid)))
    }
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_cells": len(foreground),
        "n_occupied_columns": len(occupied_columns),
        "palette_size": len(set(foreground)),
    }


def _weighted_options(
    domain: tuple[int, ...],
    *,
    difficulty: str | None,
    canonical_target: int | None,
    easy_bias: tuple[int, ...],
    medium_bias: tuple[int, ...],
    hard_bias: tuple[int, ...],
) -> tuple[int, ...]:
    """Return a weighted option tuple that always retains full domain support."""
    if canonical_target is not None:
        return domain + (canonical_target,) * 60
    bias = {
        "easy": easy_bias,
        "hard": hard_bias,
    }.get(difficulty, medium_bias)
    return domain + bias * 4


def _allocate_column_counts(
    *, total: int, columns: int, height: int, scene: str, rng
) -> list[int]:
    """Positive bounded composition; each column leaves room for a gap."""
    counts = [1] * columns
    remaining = total - columns
    cap = height - 1

    if scene in {"deep", "mixed"}:
        target = min(4, cap, total - (columns - 1))
        addition = min(remaining, target - counts[0])
        counts[0] += addition
        remaining -= addition

    if scene in {"supported", "mixed"} and max(counts) < 2:
        counts[0] += 1
        remaining -= 1

    while remaining:
        available = [index for index, count in enumerate(counts) if count < cap]
        if not available:
            raise ValueError("requested foreground count exceeds constructive capacity")
        if scene == "canonical":
            minimum = min(counts[index] for index in available)
            choices = [index for index in available if counts[index] == minimum]
            index = rng.choice(choices)
        else:
            index = rng.choice(available)
        counts[index] += 1
        remaining -= 1
    return counts


def _choose_rows(
    *, height: int, count: int, supported: bool, rng
) -> list[int]:
    if supported:
        # Touch the floor but leave the penultimate row empty.  A wrong
        # "floor contact freezes the whole column" rule is therefore visible.
        upper = rng.sample(range(0, height - 2), count - 1)
        return sorted(upper + [height - 1])
    # Excluding the floor guarantees some movement even when cells happen to
    # form a contiguous stack within the sampled upper rows.
    return sorted(rng.sample(range(0, height - 1), count))


def _validate_override_types(overrides: dict[str, object]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    for axis, value in overrides.items():
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{axis} override must be an integer, found {value!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input; the Racket rule owns outputs."""
    _validate_override_types(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile_rng = ctx.draw_rng("canonical_profile_prior")
    canonical_mode = profile_rng.random() < 0.62
    canonical = profile_rng.choice(_CANONICAL_PROFILES) if canonical_mode else None

    heights = tuple(range(6, 11))
    widths = tuple(range(6, 11))
    cell_counts = tuple(range(5, 11))
    occupied_counts = tuple(range(2, 5))
    palette_sizes = tuple(range(2, 6))

    height = ctx.draw_choice(
        "grid_h",
        _weighted_options(
            heights,
            difficulty=difficulty,
            canonical_target=canonical[0] if canonical else None,
            easy_bias=(6, 7),
            medium_bias=(6, 7, 8, 9),
            hard_bias=(8, 9, 10),
        ),
    )
    width = ctx.draw_choice(
        "grid_w",
        _weighted_options(
            widths,
            difficulty=difficulty,
            canonical_target=canonical[1] if canonical else None,
            easy_bias=(6, 7),
            medium_bias=(6, 7, 8, 9),
            hard_bias=(8, 9, 10),
        ),
    )
    n_cells = ctx.draw_choice(
        "n_cells",
        _weighted_options(
            cell_counts,
            difficulty=difficulty,
            canonical_target=canonical[3] if canonical else None,
            easy_bias=(5, 6, 7),
            medium_bias=(5, 6, 7, 8, 9),
            hard_bias=(7, 8, 9, 10),
        ),
    )
    n_columns = ctx.draw_choice(
        "n_occupied_columns",
        _weighted_options(
            occupied_counts,
            difficulty=difficulty,
            canonical_target=canonical[4] if canonical else None,
            easy_bias=(2, 3),
            medium_bias=(2, 3, 4),
            hard_bias=(3, 4),
        ),
    )
    palette_size = ctx.draw_choice(
        "palette_size",
        _weighted_options(
            palette_sizes,
            difficulty=difficulty,
            canonical_target=(canonical[2] - 1) if canonical else None,
            easy_bias=(2, 3, 4),
            medium_bias=(3, 4, 5),
            hard_bias=(4, 5),
        ),
    )

    scene_rng = ctx.draw_rng("scene_mode")
    if canonical_mode:
        scene = "canonical"
    else:
        scene_options = {
            "easy": ("canonical", "supported", "mixed", "deep"),
            "hard": ("supported", "mixed", "mixed", "deep", "deep"),
        }.get(difficulty, ("canonical", "supported", "mixed", "deep"))
        scene = scene_rng.choice(scene_options)

    column_rng = ctx.draw_rng("occupied_columns")
    columns = sorted(column_rng.sample(range(width), n_columns))
    counts = _allocate_column_counts(
        total=n_cells,
        columns=n_columns,
        height=height,
        scene=scene,
        rng=ctx.draw_rng("column_counts"),
    )

    support_index = None
    if scene in {"supported", "mixed"}:
        support_index = max(
            (index for index, count in enumerate(counts) if count >= 2),
            key=lambda index: counts[index],
        )

    row_rng = ctx.draw_rng("row_positions")
    column_rows: list[list[int]] = []
    for index, count in enumerate(counts):
        column_rows.append(
            _choose_rows(
                height=height,
                count=count,
                supported=index == support_index,
                rng=row_rng,
            )
        )

    palette = ctx.draw_distinct_colors("palette", n=palette_size, exclude={0})
    primary_index = max(range(n_columns), key=lambda index: counts[index])
    primary_coords = [
        (row, columns[primary_index]) for row in column_rows[primary_index]
    ]
    all_coords = [
        (row, columns[index])
        for index in range(n_columns)
        for row in column_rows[index]
    ]

    assignments: dict[tuple[int, int], int] = {
        primary_coords[0]: palette[0],
        primary_coords[-1]: palette[1],
    }
    unused_colors = list(palette[2:])
    remaining_coords = [coord for coord in all_coords if coord not in assignments]
    color_rng = ctx.draw_rng("color_assignment")
    color_rng.shuffle(remaining_coords)
    for color, coord in zip(unused_colors, remaining_coords):
        assignments[coord] = color
    for coord in remaining_coords[len(unused_colors):]:
        assignments[coord] = color_rng.choice(palette)

    grid = full_grid(height, width, 0)
    for (row, column), color in assignments.items():
        grid[row][column] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid gravity scene: {errors}")
    return [list(row) for row in grid]


# ---------------------------------------------------------------------------
# Task-linked semantic contract
# ---------------------------------------------------------------------------

def _identity(grid):
    """Wrong rival: infer that sparse colored cells remain fixed."""
    return [list(row) for row in grid]


def _reverse_column_order(grid):
    """Wrong rival: pack each column but reverse the cells while falling."""
    height, width = len(grid), len(grid[0])
    out = [[0] * width for _ in range(height)]
    for column in range(width):
        values = [grid[row][column] for row in range(height) if grid[row][column] != 0]
        values.reverse()
        for offset, value in enumerate(values):
            out[height - len(values) + offset][column] = value
    return out


def _freeze_bottom_supported_columns(grid):
    """Wrong shortcut: any floor contact freezes that entire column."""
    height, width = len(grid), len(grid[0])
    out = [[0] * width for _ in range(height)]
    for column in range(width):
        if grid[-1][column] != 0:
            for row in range(height):
                out[row][column] = grid[row][column]
            continue
        values = [grid[row][column] for row in range(height) if grid[row][column] != 0]
        for offset, value in enumerate(values):
            out[height - len(values) + offset][column] = value
    return out


def _cap_three_cells_per_column(grid):
    """Wrong shortcut: apply gravity only to the <=3-cell canonical regime."""
    height, width = len(grid), len(grid[0])
    out = [[0] * width for _ in range(height)]
    for column in range(width):
        values = [grid[row][column] for row in range(height) if grid[row][column] != 0]
        if len(values) > 3:
            for row in range(height):
                out[row][column] = grid[row][column]
            continue
        for offset, value in enumerate(values):
            out[height - len(values) + offset][column] = value
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity,
    "reverse_column_order": _reverse_column_order,
    "freeze_bottom_supported_columns": _freeze_bottom_supported_columns,
    "cap_three_cells_per_column": _cap_three_cells_per_column,
}


def _moves_under_gravity(grid) -> bool:
    return not self_check(grid) and _identity(grid) != _gravity_down(grid)


def _has_order_counterexample(grid) -> bool:
    return not self_check(grid) and _reverse_column_order(grid) != _gravity_down(grid)


def _has_bottom_support_counterexample(grid) -> bool:
    return (
        not self_check(grid)
        and _freeze_bottom_supported_columns(grid) != _gravity_down(grid)
    )


def _has_deep_column_counterexample(grid) -> bool:
    return not self_check(grid) and _cap_three_cells_per_column(grid) != _gravity_down(grid)


SEMANTIC_WITNESSES = {
    "moving_cells": _moves_under_gravity,
    "preserve_column_order": _has_order_counterexample,
    "bottom_contact_does_not_freeze_column": _has_bottom_support_counterexample,
    "gravity_handles_four_plus_cells": _has_deep_column_counterexample,
}

WITNESS_RIVALS = {
    "moving_cells": ["identity"],
    "preserve_column_order": ["reverse_column_order"],
    "bottom_contact_does_not_freeze_column": ["freeze_bottom_supported_columns"],
    "gravity_handles_four_plus_cells": ["cap_three_cells_per_column"],
}

# Both shortcuts fit every public canonical pair.  Generated supported and deep
# columns are the cheapest direct counterexamples to those extrapolation errors.
CANONICAL_SHORTCUTS = {
    "freeze_bottom_supported_columns": _freeze_bottom_supported_columns,
    "cap_three_cells_per_column": _cap_three_cells_per_column,
}
