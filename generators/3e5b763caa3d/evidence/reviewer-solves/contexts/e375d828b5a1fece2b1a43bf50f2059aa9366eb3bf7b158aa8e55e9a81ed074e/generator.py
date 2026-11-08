"""Generator for 3e5b763caa3d — mirror left-side cells across a divider.

The selected rule is structural, not positional: the unique full-height,
uniform, nonzero column is the mirror axis.  Every nonzero cell strictly to
its left is copied to the reflected coordinate on the right, preserving color.

The default schedule deliberately varies both divider position and divider
color.  Every four consecutive examples contain an off-center divider and a
non-gray divider, refuting the two canonical-fitting shortcuts encoded below.
"""
from __future__ import annotations

from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3e5b763caa3d"
TASK_ID = "3e5b763caa3d"
VERSION = "2.0.0"
RULE_HASH = "da67ea740136"

SUMMARY = (
    "Find the unique full-height uniform nonzero divider column. Preserve the "
    "input and copy every nonzero cell strictly left of that divider to its "
    "equal-distance position on the right, preserving color."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is black (0)",
    "exactly one column is full-height, uniform, and nonzero",
    "all source cells lie strictly left of the divider",
    "the right side starts empty",
    "every source reflection is in bounds",
]

_GRID_HEIGHTS = (7, 8, 9)
_GRID_WIDTHS = (7, 9, 11)
_AXIS_MODES = ("left", "center", "right")
_DIVIDER_COLORS = (1, 5, 9)
_CELL_COUNTS = (6, 9, 12)
_DISTINCT_COLOR_COUNTS = (4, 5, 6)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "sample_index cycles official heights 7,9,8,7,9",
        "valid": "7|8|9",
    },
    "grid_w": {
        "type": "int",
        "default": "sample_index cycles official widths 7,7,7,9,9",
        "valid": "7|9|11",
    },
    "axis_mode": {
        "type": "str",
        "default": "four-step semantic schedule",
        "valid": "left|center|right",
    },
    "divider_color": {
        "type": "color",
        "default": "four-step semantic schedule",
        "valid": "1|5|9",
    },
    "cells": {
        "type": "int",
        "default": "6 easy, 9 medium/default, 12 hard",
        "valid": "6|9|12",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "chosen to reproduce an official palette profile",
        "valid": "4|5|6",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# (height, width, number of distinct source colors). Adding background and
# divider gives the five exact official (height, width, palette-size) profiles.
_CANONICAL_DEFAULTS = (
    (7, 7, 5),
    (9, 7, 6),
    (8, 7, 4),
    (7, 9, 6),
    (9, 9, 5),
)
_CANONICAL_PROFILES = frozenset(
    (height, width, source_colors + 2)
    for height, width, source_colors in _CANONICAL_DEFAULTS
)

# Each profile fires at least one executable semantic witness. Any four
# consecutive samples cover all four profiles, including both shortcut types.
_SCHEDULE = (
    ("left_gray", "left", 5),
    ("center_non_gray", "center", 1),
    ("right_non_gray", "right", 9),
    ("left_non_gray", "left", 1),
)
SCHEDULE_PROFILES = tuple(profile for profile, _, _ in _SCHEDULE)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the replayable four-step semantic teaching profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have at least one column"]

    width = len(grid[0])
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} is not rectangular width {width}")
            continue
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int):
                return ["grid values must be integer ARC colors 0..9"]
            if not 0 <= value <= 9:
                return ["grid values must be integer ARC colors 0..9"]
    return errors


def _uniform_nonzero_columns(grid) -> list[tuple[int, int]]:
    if _grid_errors(grid):
        return []
    height, width = len(grid), len(grid[0])
    hits: list[tuple[int, int]] = []
    for column in range(width):
        color = grid[0][column]
        if color != 0 and all(grid[row][column] == color for row in range(height)):
            hits.append((column, color))
    return hits


def _axis_column(width: int, mode: str) -> int:
    if mode == "left":
        return 2
    if mode == "center":
        return (width - 1) // 2
    if mode == "right":
        return width - 3
    raise ValueError(f"unknown axis_mode {mode!r}")


def _axis_mode(width: int, column: int) -> str:
    matches = [mode for mode in _AXIS_MODES if _axis_column(width, mode) == column]
    if len(matches) != 1:
        raise ValueError(
            f"divider column {column} does not identify one declared axis mode"
        )
    return matches[0]


def semantic_profile(grid) -> dict[str, object]:
    """Expose the exact structural/profile facts used by review gates."""
    errors = _grid_errors(grid)
    if errors:
        return {"valid": False, "errors": errors}
    hits = _uniform_nonzero_columns(grid)
    if len(hits) != 1:
        return {"valid": False, "divider_count": len(hits)}
    axis, divider_color = hits[0]
    source = [
        grid[row][column]
        for row in range(len(grid))
        for column in range(axis)
        if grid[row][column] != 0
    ]
    try:
        mode = _axis_mode(len(grid[0]), axis)
    except ValueError:
        mode = "other"
    return {
        "valid": not self_check(grid),
        "height": len(grid),
        "width": len(grid[0]),
        "palette_size": len({value for row in grid for value in row}),
        "axis_mode": mode,
        "divider_color": divider_color,
        "cells": len(source),
        "n_distinct_colors": len(set(source)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the authoritative grammar and reject rule-ambiguous near misses."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    if height not in _GRID_HEIGHTS:
        errors.append(f"height {height} outside honest generator domain {_GRID_HEIGHTS}")
    if width not in _GRID_WIDTHS:
        errors.append(f"width {width} outside honest generator domain {_GRID_WIDTHS}")

    hits = _uniform_nonzero_columns(grid)
    if len(hits) != 1:
        errors.append(
            f"expected exactly one full-height uniform nonzero divider, found {len(hits)}"
        )
        return errors

    axis, divider_color = hits[0]
    try:
        _axis_mode(width, axis)
    except ValueError as exc:
        errors.append(str(exc))

    if divider_color not in range(1, 10):
        errors.append("divider color must be nonzero")

    source_values: list[int] = []
    for row in range(height):
        for column in range(width):
            value = grid[row][column]
            if column == axis:
                continue
            if column > axis and value != 0:
                errors.append(
                    f"right side must start empty; found color at ({row},{column})"
                )
                continue
            if column < axis and value != 0:
                mirror_column = 2 * axis - column
                if not 0 <= mirror_column < width:
                    errors.append(
                        f"source ({row},{column}) reflects out of bounds to {mirror_column}"
                    )
                source_values.append(value)

    if len(source_values) < 1:
        errors.append("at least one nonzero source cell is required")
    if divider_color in source_values:
        errors.append("source colors must exclude the divider color")
    if 0 not in {value for row in grid for value in row}:
        errors.append("scene must retain black background cells")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the five official height/width/palette profiles exactly."""
    errors = self_check(grid)
    if errors:
        return errors
    signature = (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )
    if signature not in _CANONICAL_PROFILES:
        return [f"profile {signature} is outside the five official input profiles"]
    return []


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror of the selected canonical Racket rule."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("rule_mirror expects a rectangular ARC grid")
    hits = _uniform_nonzero_columns(grid)
    if len(hits) != 1:
        raise ValueError("rule_mirror requires one unique uniform nonzero divider")
    axis, _ = hits[0]

    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for column in range(axis):
            value = grid[row][column]
            mirror_column = 2 * axis - column
            if value != 0 and 0 <= mirror_column < width:
                output[row][mirror_column] = value
    return output


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact declared axis from the generated input grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    axis, divider_color = _uniform_nonzero_columns(grid)[0]
    source = [
        grid[row][column]
        for row in range(len(grid))
        for column in range(axis)
        if grid[row][column] != 0
    ]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "axis_mode": _axis_mode(len(grid[0]), axis),
        "divider_color": divider_color,
        "cells": len(source),
        "n_distinct_colors": len(set(source)),
    }


def _validate_call(difficulty, overrides: dict[str, object]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis: " + ", ".join(unknown))

    domains = {
        "grid_h": _GRID_HEIGHTS,
        "grid_w": _GRID_WIDTHS,
        "axis_mode": _AXIS_MODES,
        "divider_color": _DIVIDER_COLORS,
        "cells": _CELL_COUNTS,
        "n_distinct_colors": _DISTINCT_COLOR_COUNTS,
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if name == "axis_mode":
            if not isinstance(value, str):
                raise TypeError("axis_mode override must be a string")
        elif type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
        if value not in domains[name]:
            raise ValueError(
                f"{name} override {value!r} outside declared domain {domains[name]!r}"
            )


def _default_overrides(sample_index: int, difficulty) -> dict[str, int | str]:
    height, width, source_colors = _CANONICAL_DEFAULTS[
        sample_index % len(_CANONICAL_DEFAULTS)
    ]
    _, axis_mode, divider_color = _SCHEDULE[sample_index % len(_SCHEDULE)]
    cells = {
        "easy": 6,
        "medium": 9,
        "hard": 12,
        None: _CELL_COUNTS[sample_index % len(_CELL_COUNTS)],
    }[difficulty]
    return {
        "grid_h": height,
        "grid_w": width,
        "axis_mode": axis_mode,
        "divider_color": divider_color,
        "cells": cells,
        "n_distinct_colors": source_colors,
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)

    effective = _default_overrides(sample_index, difficulty)
    for name, value in overrides.items():
        if value is not None:
            effective[name] = value

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_choice("grid_h", _GRID_HEIGHTS)
    width = ctx.draw_choice("grid_w", _GRID_WIDTHS)
    axis_mode = ctx.draw_choice("axis_mode", _AXIS_MODES)
    divider_color = ctx.draw_choice("divider_color", _DIVIDER_COLORS)
    cells = ctx.draw_choice("cells", _CELL_COUNTS)
    n_distinct_colors = ctx.draw_choice(
        "n_distinct_colors", _DISTINCT_COLOR_COUNTS
    )

    axis = _axis_column(width, axis_mode)
    legal_columns = [
        column
        for column in range(axis)
        if 0 <= 2 * axis - column < width
    ]

    # Exclude one deterministic row in every legal source column. This keeps
    # the intended divider unique even at the densest exact override (12 cells
    # on a 7-row grid with only two legal source columns).
    position_rng = ctx.draw_rng("source_positions")
    blocked_rows = {
        column: position_rng.randrange(height) for column in legal_columns
    }
    positions = [
        (row, column)
        for column in legal_columns
        for row in range(height)
        if row != blocked_rows[column]
    ]
    position_rng.shuffle(positions)
    if cells > len(positions):
        raise ValueError(
            f"cells={cells} exceeds legal capacity {len(positions)} for "
            f"grid {height}x{width} and axis_mode={axis_mode}"
        )
    selected_positions = positions[:cells]

    palette = ctx.draw_distinct_colors(
        "source_palette",
        n=n_distinct_colors,
        exclude={0, divider_color},
    )
    color_rng = ctx.draw_rng("source_colors")
    source_colors = list(palette)
    source_colors.extend(
        color_rng.choice(palette) for _ in range(cells - len(palette))
    )
    color_rng.shuffle(source_colors)

    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][axis] = divider_color
    for (row, column), color in zip(selected_positions, source_colors):
        grid[row][column] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generator emitted invalid grid: " + "; ".join(errors))
    return grid


def _copy_grid(grid):
    return [list(row) for row in grid]


def _mirror_about_column(grid, axis: int):
    output = _copy_grid(grid)
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for column in range(axis):
            value = grid[row][column]
            mirror_column = 2 * axis - column
            if value != 0 and 0 <= mirror_column < width:
                output[row][mirror_column] = value
    return output


def _grid_center_axis(grid):
    """Wrong shortcut: use geometric center instead of detecting divider."""
    if _grid_errors(grid):
        return _copy_grid(grid)
    return _mirror_about_column(grid, (len(grid[0]) - 1) // 2)


def _fixed_gray_axis(grid):
    """Wrong shortcut: only color 5 can be the divider."""
    if _grid_errors(grid):
        return _copy_grid(grid)
    height, width = len(grid), len(grid[0])
    axes = [
        column
        for column in range(width)
        if all(grid[row][column] == 5 for row in range(height))
    ]
    if not axes:
        return _copy_grid(grid)
    return _mirror_about_column(grid, axes[0])


def _has_off_center_divider(grid) -> bool:
    hits = _uniform_nonzero_columns(grid)
    return len(hits) == 1 and hits[0][0] != (len(grid[0]) - 1) // 2


def _has_non_gray_divider(grid) -> bool:
    hits = _uniform_nonzero_columns(grid)
    return len(hits) == 1 and hits[0][1] != 5


SEMANTIC_WITNESSES = {
    "off_center_divider": _has_off_center_divider,
    "non_gray_divider": _has_non_gray_divider,
}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)

SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "grid_center_axis": _grid_center_axis,
    "fixed_gray_axis": _fixed_gray_axis,
}
WITNESS_RIVALS = {
    "off_center_divider": ["grid_center_axis"],
    "non_gray_divider": ["fixed_gray_axis"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named rival survives demos but changes query."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]

    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is missing input/output")
            continue
        structural = self_check(pair["input"])
        if structural:
            reasons.append(f"{role} input is not lawful: {structural[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{role} output disagrees with divider-reflection rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes query answer"
            )
    return reasons


def mutation_fixtures():
    """Task-linked malformed near misses that self_check must reject."""
    legal = generate(
        9001,
        0,
        grid_h=7,
        grid_w=7,
        axis_mode="center",
        divider_color=5,
        cells=6,
        n_distinct_colors=4,
    )
    axis, _ = _uniform_nonzero_columns(legal)[0]

    divider_gap = _copy_grid(legal)
    divider_gap[0][axis] = 0

    right_side_content = _copy_grid(legal)
    right_side_content[0][axis + 1] = 4

    second_divider = _copy_grid(legal)
    for row in range(len(second_divider)):
        second_divider[row][0] = 8

    return [
        ("divider_gap", divider_gap),
        ("right_side_content", right_side_content),
        ("second_uniform_full_column", second_divider),
        ("full_one_color", [[4] * 7 for _ in range(7)]),
        ("ragged", [[0, 0, 5], [0, 5]]),
    ]
