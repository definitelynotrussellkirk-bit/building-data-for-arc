"""Canonical-aligned generator for ARC task 56ff96f3 / 021fb6acf24f.

Each non-background color has exactly two non-collinear anchors.  Colors are
processed in ascending numeric order; each fills only still-background cells
inside its anchor bounding box.  Therefore the lower color wins bbox overlaps.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "021fb6acf24f"
TASK_ID = "021fb6acf24f"
VERSION = "3.0.1"
RULE_HASH = "9a7f76b1ea86"

SUMMARY = (
    "A 0-background grid contains one or two non-zero colors, exactly two "
    "anchors per color, with distinct rows and columns. In ascending numeric "
    "color order, each color fills still-zero cells in its anchor bounding "
    "box; lower colors keep contested overlap cells."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 5

INVARIANTS = [
    "grid size is 6..10 rows by 8..11 columns",
    "there are one or two non-background colors",
    "each non-background color occurs at exactly two distinct-row/distinct-column anchors",
    "two-color production samples contain a zero-cell bbox overlap",
    "the first scan-order color is numerically larger, exposing scan-order and overwrite rivals",
]

AXES = {
    "grid_h": {"type": "int", "default": "five-profile schedule", "valid": "6..10"},
    "grid_w": {"type": "int", "default": "five-profile schedule", "valid": "8..11"},
    "n_colors": {"type": "int", "default": "five-profile schedule", "valid": "1..2"},
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

_PROFILE_SPECS = (
    ("canonical_10x10_one", 10, 10, 1),
    ("canonical_7x8_two", 7, 8, 2),
    ("canonical_9x8_two", 9, 8, 2),
    ("canonical_10x10_two", 10, 10, 2),
    ("canonical_6x11_one", 6, 11, 1),
)
SCHEDULE_PROFILES = tuple(spec[0] for spec in _PROFILE_SPECS)
_ALLOWED_DIFFICULTIES = {None, "easy", "medium", "hard"}
_AXIS_RANGES = {"grid_h": (6, 10), "grid_w": (8, 11), "n_colors": (1, 2)}


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Return the deterministic canonical-profile branch for an index."""
    _validate_call_arguments(seed, sample_index)
    _validate_difficulty(difficulty)
    return _PROFILE_SPECS[sample_index % LESSON_SCHEDULE_PERIOD][0]


def _profile_spec(sample_index: int) -> tuple[str, int, int, int]:
    return _PROFILE_SPECS[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_call_arguments(seed: int, sample_index: int) -> None:
    """Reject scalar lookalikes before indexing or constructing RNG state."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def _validate_difficulty(difficulty: str | None) -> None:
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise KeyError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
        lo, hi = _AXIS_RANGES[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")


def _scheduled_choice(ctx, label: str, lo: int, hi: int, target: int) -> int:
    """Draw from the full legal domain while making the scheduled default exact.

    ``draw_choice`` must expose every advertised override value on every sample.
    Its keyed RNG is reproducible, so arrange the complete option list such that
    the default-selected index contains the profile target.  Explicit overrides
    still select any member of the unchanged legal domain.
    """
    options = list(range(lo, hi + 1))
    selected_index = ctx.draw_rng(label).randrange(len(options))
    target_index = options.index(target)
    options[selected_index], options[target_index] = (
        options[target_index],
        options[selected_index],
    )
    return int(ctx.draw_choice(label, options))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call_arguments(seed, sample_index)
    _validate_difficulty(difficulty)
    _validate_overrides(overrides)
    _name, target_h, target_w, target_colors = _profile_spec(sample_index)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _scheduled_choice(ctx, "grid_h", 6, 10, target_h)
    width = _scheduled_choice(ctx, "grid_w", 8, 11, target_w)
    n_colors = _scheduled_choice(ctx, "n_colors", 1, 2, target_colors)
    colors = tuple(ctx.draw_distinct_colors("colors", n=n_colors, exclude={0}))
    layout_rng = ctx.draw_rng("layout")

    if n_colors == 1:
        return _draw_single_color(height, width, colors[0], layout_rng, difficulty)
    return _draw_order_contest(height, width, colors, layout_rng, difficulty)


def _draw_single_color(
    height: int, width: int, color: int, rng, difficulty: str | None
) -> list[list[int]]:
    grid = full_grid(height, width, 0)
    if difficulty == "easy":
        row_span, col_span = 1, 1
    elif difficulty == "hard":
        row_span, col_span = height - 2, width - 2
    elif difficulty == "medium":
        row_span = max(2, height // 2)
        col_span = max(2, width // 2)
    else:
        row_span = rng.randint(1, height - 1)
        col_span = rng.randint(1, width - 1)
    row0 = rng.randrange(height - row_span)
    col0 = rng.randrange(width - col_span)
    row1, col1 = row0 + row_span, col0 + col_span
    if rng.randrange(2):
        anchors = ((row0, col1), (row1, col0))
    else:
        anchors = ((row0, col0), (row1, col1))
    for row, col in anchors:
        grid[row][col] = color
    return grid


def _draw_order_contest(
    height: int, width: int, colors: tuple[int, int], rng, difficulty: str | None
) -> list[list[int]]:
    """Construct two overlapping bboxes with background contest cells."""
    # Each rectangle is at least 3x3.  Difficulty changes geometry while the
    # public canonical profile remains fixed.
    if difficulty == "easy":
        rect_h = rect_w = 3
    elif difficulty == "hard":
        rect_h, rect_w = height - 1, width - 1
    elif difficulty == "medium":
        rect_h = max(4, min(height - 2, (height + 1) // 2))
        rect_w = max(4, min(width - 2, (width + 1) // 2))
    else:
        rect_h = rng.randint(3, height - 1)
        rect_w = rng.randint(3, width - 1)
    canvas_h, canvas_w = rect_h + 1, rect_w + 1

    group_a = {(0, 0), (rect_h - 1, rect_w - 1)}
    group_b = {(1, rect_w), (rect_h, 1)}

    flip_vertical = bool(rng.randrange(2))
    flip_horizontal = bool(rng.randrange(2))

    def transform(point: tuple[int, int]) -> tuple[int, int]:
        row, col = point
        if flip_vertical:
            row = canvas_h - 1 - row
        if flip_horizontal:
            col = canvas_w - 1 - col
        return row, col

    group_a = {transform(point) for point in group_a}
    group_b = {transform(point) for point in group_b}

    origin_row = rng.randrange(height - canvas_h + 1)
    origin_col = rng.randrange(width - canvas_w + 1)

    low_color, high_color = sorted(colors)
    # Put the numerically larger color first in scan order.  The authoritative
    # rule nevertheless processes the lower color first because Racket unique
    # sorts numeric values.  Scan-order and late-overwrite shortcuts therefore
    # disagree on original-zero overlap cells.
    if min(group_a) < min(group_b):
        assignments = ((group_a, high_color), (group_b, low_color))
    else:
        assignments = ((group_a, low_color), (group_b, high_color))

    grid = full_grid(height, width, 0)
    for points, color in assignments:
        for row, col in points:
            grid[origin_row + row][origin_col + col] = color
    return grid


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact public axis from a returned input grid."""
    errors = _grid_shape_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    colors = {value for row in grid for value in row if value != 0}
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_colors": len(colors)}


def _grid_shape_errors(grid) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not all(isinstance(row, list) for row in grid):
        return ["every row must be a list"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be non-empty and rectangular"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical input manifold, including one-color examples."""
    errors = _grid_shape_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not 6 <= height <= 10:
        errors.append(f"height {height} outside 6..10")
    if not 8 <= width <= 11:
        errors.append(f"width {width} outside 8..11")

    by_color: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                by_color.setdefault(value, []).append((row, col))
    if not 1 <= len(by_color) <= 2:
        errors.append(f"need 1..2 non-background colors, got {len(by_color)}")
    for color, cells in sorted(by_color.items()):
        if len(cells) != 2:
            errors.append(f"color {color} must have exactly two anchors, got {len(cells)}")
            continue
        if len({row for row, _ in cells}) != 2:
            errors.append(f"color {color} anchors must occupy distinct rows")
        if len({col for _, col in cells}) != 2:
            errors.append(f"color {color} anchors must occupy distinct columns")
    if not any(value == 0 for row in grid for value in row):
        errors.append("grid must retain background cells")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _scan_colors(grid: list[list[int]]) -> list[int]:
    colors: list[int] = []
    for row in grid:
        for value in row:
            if value != 0 and value not in colors:
                colors.append(value)
    return colors


def _bbox(grid: list[list[int]], color: int) -> tuple[int, int, int, int]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _fill_in_order(
    grid: list[list[int]], colors: list[int], *, original_zero_only: bool = False
) -> list[list[int]]:
    original = deepcopy(grid)
    output = deepcopy(grid)
    for color in colors:
        row0, col0, row1, col1 = _bbox(grid, color)
        for row in range(row0, row1 + 1):
            for col in range(col0, col1 + 1):
                can_fill = original[row][col] == 0 if original_zero_only else output[row][col] == 0
                if can_fill:
                    output[row][col] = color
    return output


def _intended_output(grid: list[list[int]]) -> list[list[int]]:
    return _fill_in_order(grid, sorted(_scan_colors(grid)))


def _scan_color_order(grid: list[list[int]]) -> list[list[int]]:
    return _fill_in_order(grid, _scan_colors(grid))


def _late_overwrite(grid: list[list[int]]) -> list[list[int]]:
    return _fill_in_order(grid, sorted(_scan_colors(grid)), original_zero_only=True)


def _identity(grid: list[list[int]]) -> list[list[int]]:
    return deepcopy(grid)


def _scan_order_overlap(grid: list[list[int]]) -> bool:
    if self_check(grid) or len(_scan_colors(grid)) != 2:
        return False
    intended = _intended_output(grid)
    return _scan_color_order(grid) != intended and _late_overwrite(grid) != intended


SEMANTIC_WITNESSES = {"scan_order_overlap": _scan_order_overlap}
SEMANTIC_RIVALS = {
    "scan_color_order": _scan_color_order,
    "late_overwrite": _late_overwrite,
}
WITNESS_RIVALS = {
    "scan_order_overlap": ("scan_color_order", "late_overwrite"),
}
CANONICAL_SHORTCUTS = {
    "scan_color_order": _scan_color_order,
    "late_overwrite": _late_overwrite,
}
LESSON_COMPETITORS = {
    "scan_color_order": _scan_color_order,
    "late_overwrite": _late_overwrite,
    "identity": _identity,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a declared plausible rival survives the demos."""
    reasons: list[str] = []
    for name, solve in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(solve(pair["input"]) == pair["output"] for pair in demos)
            changes_query = solve(query["input"]) != query["output"]
        except Exception as exc:  # malformed materialization must be visible
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"competitor {name} fits every demonstration but changes the query")
    return reasons
