"""Input generator for task 22304ccc509c: per-column downward gravity.

The selected Racket rule packs each column's nonzero values against the bottom
without changing their top-to-bottom order.  This sampler deliberately includes
an occupied bottom row and a numerically descending stack in every production
draw.  Those two small witnesses close the retained "discard the bottom row"
and "sort values, then drop" shortcuts while keeping the canonical rule and
selected authority unchanged.
"""
from __future__ import annotations

from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "22304ccc509c"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "c3638032481f"

SUMMARY = (
    "A 0-background grid with 2..6 populated columns and 1..9 foreground "
    "colors.  In each column independently, collect nonzero values in their "
    "original top-to-bottom order and pack them flush to the bottom.  Every "
    "default draw contains both an occupied bottom-row cell and a descending "
    "multi-color stack, so dropping the input bottom row or sorting values "
    "cannot imitate the intended order-preserving gravity rule."
)

INVARIANTS = [
    "background is 0 and all foreground colors are in 1..9",
    "columns transform independently and never exchange cells",
    "each column preserves the original top-to-bottom order of nonzero values",
    "all nonzero values settle flush at the bottom of their original column",
    "production draws contain a bottom-row payload and a descending-order witness",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchors plus broad 8..18 profiles",
        "valid": "6..18",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchors plus broad 8..18 profiles",
        "valid": "6..18",
    },
    "columns": {
        "type": "int",
        "default": "scheduled 2..6 populated columns",
        "valid": "2..6",
    },
    "palette_size": {
        "type": "int",
        "default": "scheduled 3..9 distinct foreground colors",
        "valid": "1..9",
    },
}

# The declared domains are jointly feasible: min capacity is 6*2-1=11 cells,
# enough to realize all nine colors while reserving one gap for non-identity.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SCHEDULE_PROFILES = (
    "canonical_6x6_p7",
    "canonical_7x7_p6",
    "canonical_6x6_p5",
    "broad_sparse",
    "broad_dense",
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Five consecutive accepted sample indices cover every curriculum profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    """Use a pinned curriculum value unless the caller explicitly overrides it."""
    explicit = label in ctx.overrides and ctx.overrides[label] is not None
    options = tuple(range(lo, hi + 1)) if explicit else (scheduled,)
    return ctx.draw_choice(label, options)


def _profile_defaults(profile: str, difficulty) -> tuple[int, int, int, int]:
    """Return h, w, populated-column count, and foreground palette size."""
    if profile == "canonical_6x6_p7":
        return 6, 6, 4, 7
    if profile == "canonical_7x7_p6":
        return 7, 7, 5, 6
    if profile == "canonical_6x6_p5":
        return 6, 6, 5, 5

    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    if profile == "broad_sparse":
        return {
            "easy": (8, 8, 3, 3),
            "medium": (11, 12, 4, 5),
            "hard": (15, 16, 5, 7),
        }[band]
    if profile == "broad_dense":
        return {
            "easy": (9, 10, 4, 5),
            "medium": (13, 14, 5, 7),
            "hard": (18, 18, 6, 9),
        }[band]
    raise ValueError(f"unknown schedule profile: {profile!r}")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(
                f"{name} override must be an integer (not {type(value).__name__})"
            )


def _target_nonzero_count(
    profile: str, h: int, columns: int, palette_size: int
) -> int:
    """Choose a profile density while preserving one empty witness gap."""
    minimum = max(5, columns + 1, palette_size)
    capacity = h * columns - 1
    if profile == "broad_dense":
        requested = max(minimum, (3 * h * columns) // 5)
    elif profile == "broad_sparse":
        requested = max(minimum, columns + palette_size)
    else:
        requested = max(minimum, palette_size + 2)
    return min(capacity, requested)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a deterministic, non-identity input on the declared manifold."""
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w, default_columns, default_palette = _profile_defaults(
        profile, difficulty
    )
    h = _scheduled_int(ctx, "grid_h", 6, 18, default_h)
    w = _scheduled_int(ctx, "grid_w", 6, 18, default_w)
    columns = _scheduled_int(ctx, "columns", 2, 6, default_columns)
    palette_size = _scheduled_int(ctx, "palette_size", 1, 9, default_palette)

    rng = ctx.draw_rng(f"layout:{profile}:{difficulty!r}")
    populated_columns = rng.sample(range(w), columns)
    palette = sorted(rng.sample(range(1, 10), palette_size))
    grid = full_grid(h, w, 0)

    witness_column = populated_columns[0]
    witness_top = rng.randrange(0, h - 2)
    reserved_gap = (h - 2, witness_column)
    high_color = palette[-1]
    low_color = palette[0]
    grid[witness_top][witness_column] = high_color
    grid[h - 1][witness_column] = low_color

    occupied = {(witness_top, witness_column), (h - 1, witness_column)}
    used_colors = {high_color, low_color}
    missing_colors = [color for color in palette if color not in used_colors]

    # Populate every advertised column.  Consume missing colors first so the
    # realized palette is exact even at the smallest density.
    for column in populated_columns[1:]:
        row = rng.randrange(0, h - 1)
        color = missing_colors.pop(0) if missing_colors else rng.choice(palette)
        grid[row][column] = color
        occupied.add((row, column))
        used_colors.add(color)

    candidates = [
        (row, column)
        for column in populated_columns
        for row in range(h)
        if (row, column) not in occupied and (row, column) != reserved_gap
    ]
    rng.shuffle(candidates)

    for color in missing_colors:
        row, column = candidates.pop()
        grid[row][column] = color
        occupied.add((row, column))
        used_colors.add(color)

    target_count = _target_nonzero_count(profile, h, columns, palette_size)
    while len(occupied) < target_count:
        row, column = candidates.pop()
        grid[row][column] = rng.choice(palette)
        occupied.add((row, column))

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid gravity scene: " + "; ".join(errors))
    return grid


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact public axis from returned pixels."""
    h = len(grid)
    w = len(grid[0])
    populated = sum(any(grid[row][column] != 0 for row in range(h)) for column in range(w))
    palette = {value for row in grid for value in row if value != 0}
    return {
        "grid_h": h,
        "grid_w": w,
        "columns": populated,
        "palette_size": len(palette),
    }


def _column_values(grid, column: int) -> list[int]:
    return [row[column] for row in grid if row[column] != 0]


def rule_mirror(grid):
    """Independent Python mirror: bottom-pack each column, preserving order."""
    if not grid:
        return []
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    for column in range(w):
        values = _column_values(grid, column)
        start = h - len(values)
        for offset, value in enumerate(values):
            output[start + offset][column] = value
    return output


def _sort_values_then_drop(grid):
    """Plausible wrong rule that canonical labels do not distinguish."""
    if not grid:
        return []
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    for column in range(w):
        values = sorted(_column_values(grid, column))
        start = h - len(values)
        for offset, value in enumerate(values):
            output[start + offset][column] = value
    return output


def _discard_bottom_row_then_drop(grid):
    """Retained generated-data shortcut from the prior audit."""
    if not grid:
        return []
    stripped = [list(row) for row in grid]
    stripped[-1] = [0 for _ in stripped[-1]]
    return rule_mirror(stripped)


def _occupied_bottom_row(grid) -> bool:
    return bool(grid and grid[-1] and any(value != 0 for value in grid[-1]))


def _descending_column_order(grid) -> bool:
    if not grid or not grid[0]:
        return False
    return any(
        (values := _column_values(grid, column)) != sorted(values)
        for column in range(len(grid[0]))
        if len(_column_values(grid, column)) >= 2
    )


SEMANTIC_WITNESSES = {
    "occupied_bottom_row": _occupied_bottom_row,
    "descending_column_order": _descending_column_order,
}
SEMANTIC_RIVALS = {
    "sort_values_then_drop": _sort_values_then_drop,
    "discard_bottom_row_then_drop": _discard_bottom_row_then_drop,
}
WITNESS_RIVALS = {
    "occupied_bottom_row": ["discard_bottom_row_then_drop"],
    "descending_column_order": ["sort_values_then_drop"],
}
CANONICAL_SHORTCUTS = {
    "sort_values_then_drop": _sort_values_then_drop,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Name any declared rival that fits all demos but changes the query."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                rival(pair["input"]) == pair["output"] for pair in demos
            )
            changes_query = rival(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"{name} could not be scored: {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(
                f"{name} fits every demonstration but predicts a different query output"
            )
    return reasons


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the sampler/canonical task manifold, not merely ARC syntax."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9 (bool is not a color)"]

    h, w = len(grid), width
    errors: list[str] = []
    if not 6 <= h <= 18:
        errors.append(f"grid_h={h} outside [6,18]")
    if not 6 <= w <= 18:
        errors.append(f"grid_w={w} outside [6,18]")

    nonzero = [(row, column) for row in range(h) for column in range(w) if grid[row][column] != 0]
    populated_columns = [
        column for column in range(w) if any(grid[row][column] != 0 for row in range(h))
    ]
    palette = {grid[row][column] for row, column in nonzero}
    if len(nonzero) < 5:
        errors.append("need at least five nonzero cells")
    if not 2 <= len(populated_columns) <= 6:
        errors.append(
            f"populated columns={len(populated_columns)} outside [2,6]"
        )
    if not 1 <= len(palette) <= 9:
        errors.append(f"foreground palette size={len(palette)} outside [1,9]")
    if not _occupied_bottom_row(grid):
        errors.append("bottom row must carry at least one nonzero payload")

    moving_columns = 0
    for column in populated_columns:
        values = _column_values(grid, column)
        settled = [0] * (h - len(values)) + values
        if [grid[row][column] for row in range(h)] != settled:
            moving_columns += 1
    if moving_columns == 0:
        errors.append("all populated columns are already settled; rule would be identity")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def mutation_fixtures() -> Iterable[tuple[str, list[list[int]]]]:
    """Small malformed near-misses that this task's validator must reject."""
    all_background = full_grid(6, 6, 0)

    singleton = full_grid(6, 6, 0)
    singleton[-1][0] = 1

    settled_line = full_grid(6, 6, 0)
    for column in range(5):
        settled_line[-1][column] = column + 1

    no_bottom_payload = full_grid(6, 6, 0)
    for column in range(5):
        no_bottom_payload[column % 3][column] = column + 1

    one_column = full_grid(6, 6, 0)
    for row, color in enumerate((1, 2, 3, 4, 5)):
        one_column[row][2] = color
    one_column[-1][2] = 6

    solid_block = full_grid(6, 6, 0)
    for row in (4, 5):
        for column in (2, 3):
            solid_block[row][column] = 7

    return (
        ("all_background", all_background),
        ("singleton", singleton),
        ("already_settled_short_line", settled_line),
        ("no_bottom_payload", no_bottom_payload),
        ("single_populated_column", one_column),
        ("solid_2x2", solid_block),
    )
