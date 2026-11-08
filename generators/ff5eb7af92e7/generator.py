"""Input distribution for the row-majority filter task.

The canonical Racket program remains the sole label authority.  This module
constructs lawful inputs and executable shortcut diagnostics.  Every ordinary
sample contains a three-color 2/1/1 row, so canonical-fitting shortcuts based on
an absolute majority, a count of three, a minimum count of three, or exactly two
row colors are contradicted by the input itself.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ff5eb7af92e7"
TASK_ID = GENERATOR_ID
RULE_HASH = "f3fbafdf1862"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Each nonempty row has a unique most-frequent nonzero color; the unchanged "
    "Racket rule keeps only cells of that row-local mode. Ordinary inputs include "
    "a 2/1/1 three-color plurality row, varied mode counts, repeated color roles, "
    "and scheduled canonical-size/eight-foreground-color anchors."
)

INVARIANTS = [
    "background is 0; grids are 5..12 rows by 7..14 columns",
    "2..12 rows are active, never more than the grid height",
    "each active row has at least two nonzero colors and one strict row-local mode",
    "ordinary draws contain a three-color 2/1/1 plurality witness",
    "ordinary draws use exactly 3..9 foreground colors and vary row-local color roles",
]

# The previous palette_kind/palette_size/position_bias/density/texture controls
# were no-ops or aliases.  They are deliberately retired instead of silently
# accepted.  Every remaining control is recoverable from returned pixels.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical profile every third draw; otherwise difficulty-weighted",
        "valid": "5..12",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical profile every third draw; otherwise difficulty-weighted",
        "valid": "7..14",
    },
    "active_rows": {
        "type": "int",
        "default": "4 in canonical anchors; otherwise difficulty-weighted 2..grid_h",
        "valid": "2..12",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "8 in canonical anchors; otherwise uniform 3..9",
        "valid": "3..9",
    },
}

# Only values with active_rows > grid_h are incompatible.  The exception below
# identifies the dependent axes for the override-contract checker.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [("grid_h", "active_rows")]
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
SCHEDULE_PROFILES = ("canonical_profile", "broad", "dense")
_CANONICAL_PROFILES = ((6, 8), (5, 7), (5, 9), (5, 8))
_COLORS = tuple(range(1, 10))


class IncompatibleControls(ValueError):
    incompatible_axes = ("grid_h", "active_rows")


def schedule_profile(seed, sample_index, difficulty=None):
    """Return a distribution profile, never a fixed grid identity."""
    return SCHEDULE_PROFILES[(int(seed) + sample_index) % len(SCHEDULE_PROFILES)]


def _axis(ctx, name: str, low: int, high: int) -> int:
    """Draw one exact integer axis and retain honest range provenance.

    draw_int_diff records the declared bounds while using the caller's difficulty
    band for default sampling.  Strict override types are enforced by
    _validate_call before this helper is reached.
    """
    return int(ctx.draw_int_diff(name, low, high))


def _validate_call(sample_index, difficulty, overrides) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown or retired override axes: {unknown}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    requested_h = overrides.get("grid_h")
    requested_active = overrides.get("active_rows")
    if requested_h is not None and requested_active is not None and requested_active > requested_h:
        raise IncompatibleControls(
            f"active_rows={requested_active} cannot exceed grid_h={requested_h}"
        )


def _profile_axes(ctx, seed: int, sample_index: int) -> tuple[int, int, int, int]:
    index = (int(seed) + int(sample_index) // len(SCHEDULE_PROFILES)) % len(_CANONICAL_PROFILES)
    height, width = _CANONICAL_PROFILES[index]
    return (
        ctx.draw_int_strict("grid_h", height, height),
        ctx.draw_int_strict("grid_w", width, width),
        ctx.draw_int_strict("active_rows", 4, 4),
        ctx.draw_int_strict("n_distinct_colors", 8, 8),
    )


def _general_axes(ctx, difficulty, overrides) -> tuple[int, int, int, int]:
    requested_active = overrides.get("active_rows")

    # Keep the integer-draw bounds equal to the public AXES contract.  Earlier
    # versions used draw_choice for defaults: pixels varied, but bounded-draw
    # provenance misleadingly showed only the exact canonical anchors.
    min_height = max(5, requested_active or 5)
    height = _axis(ctx, "grid_h", min_height, 12)
    width = _axis(ctx, "grid_w", 7, 14)

    if requested_active is not None:
        active_rows = ctx.draw_int_strict("active_rows", 2, height)
    else:
        active_rows = _axis(ctx, "active_rows", 2, height)

    n_colors = ctx.draw_int_strict("n_distinct_colors", 3, 9)
    return height, width, active_rows, n_colors


def _put_multiset(grid, row_index: int, counts: list[tuple[int, int]], rng) -> None:
    values = [color for color, count in counts for _ in range(count)]
    width = len(grid[0])
    if len(values) > width:
        raise ValueError(f"row recipe needs {len(values)} cells but width is {width}")
    columns = rng.sample(range(width), len(values))
    rng.shuffle(values)
    for column, color in zip(columns, values):
        grid[row_index][column] = color


def _witness_recipes(palette: tuple[int, ...]) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    # 2/1/1 is a strict plurality but not an absolute majority.  It also has a
    # mode count other than three and uses more than two nonzero row colors.
    first = [(palette[0], 2), (palette[1], 1), (palette[2], 1)]

    remaining = list(palette[3:])
    if len(remaining) >= 2:
        row_colors = remaining
    elif len(remaining) == 1:
        row_colors = [remaining[0], palette[0]]
    else:
        row_colors = [palette[0], palette[1]]
    second = [(row_colors[0], 2)] + [(color, 1) for color in row_colors[1:]]
    return first, second


def _ordinary_recipe(palette: tuple[int, ...], row_number: int, width: int, profile: str, rng):
    majority = palette[(row_number + 1) % len(palette)]
    others = [color for color in palette if color != majority]
    rng.shuffle(others)

    if profile == "dense":
        majority_count = min(5, width - 1)
    elif profile == "broad":
        majority_count = min(4, width - 1)
    else:
        majority_count = min(3 + row_number % 2, width - 1)

    slots = width - majority_count
    n_minority = min(len(others), max(1, min(3, slots)))
    counts: list[tuple[int, int]] = [(majority, majority_count)]
    for index, color in enumerate(others[:n_minority]):
        remaining_minority = n_minority - index - 1
        can_repeat = (
            index == 0
            and majority_count > 2
            and slots - 2 >= remaining_minority
            and (profile != "canonical_profile" or row_number % 2 == 0)
        )
        count = 2 if can_repeat else 1
        counts.append((color, count))
        slots -= count
    return counts


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)

    if not overrides and profile == "canonical_profile":
        height, width, active_rows, n_colors = _profile_axes(ctx, seed, sample_index)
    else:
        height, width, active_rows, n_colors = _general_axes(ctx, difficulty, overrides)

    palette_rng = ctx.draw_rng("foreground_palette")
    palette = tuple(palette_rng.sample(_COLORS, n_colors))
    active = sorted(ctx.draw_rng("active_row_positions").sample(range(height), active_rows))

    grid = full_grid(height, width, 0)
    first, second = _witness_recipes(palette)
    _put_multiset(grid, active[0], first, ctx.draw_rng("plurality_witness"))
    _put_multiset(grid, active[1], second, ctx.draw_rng("palette_witness"))
    for row_number, row_index in enumerate(active[2:], start=2):
        recipe = _ordinary_recipe(
            palette,
            row_number,
            width,
            profile,
            ctx.draw_rng(f"row_recipe_{row_number}"),
        )
        _put_multiset(grid, row_index, recipe, ctx.draw_rng(f"row_positions_{row_number}"))

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid row-majority input: {errors}")
    return grid


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal integer ARC colors 0..9"]
    return []


def _row_counts(row) -> Counter:
    return Counter(value for value in row if value != 0)


def _winner(row):
    counts = _row_counts(row)
    if not counts:
        return None
    return min(counts, key=lambda color: (-counts[color], row.index(color)))


def observe_overrides(grid):
    active = [row for row in grid if any(value != 0 for value in row)]
    colors = {value for row in grid for value in row if value != 0}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "active_rows": len(active),
        "n_distinct_colors": len(colors),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = _grid_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not 5 <= height <= 12 or not 7 <= width <= 14:
        errors.append("shape must be within 5..12 rows by 7..14 columns")

    active = 0
    colors = set()
    for row_index, row in enumerate(grid):
        counts = _row_counts(row)
        if not counts:
            continue
        active += 1
        colors.update(counts)
        if len(counts) < 2:
            errors.append(f"row {row_index} needs at least one minority color")
            continue
        ordered = sorted(counts.values(), reverse=True)
        if ordered[0] <= ordered[1]:
            errors.append(f"row {row_index} lacks a strict nonzero mode: {dict(counts)}")
        if ordered[0] < 2:
            errors.append(f"row {row_index} mode must occur at least twice")
    if not 2 <= active <= height:
        errors.append(f"expected 2..{height} active rows, got {active}")
    if not 3 <= len(colors) <= 9:
        errors.append(f"expected 3..9 distinct foreground colors, got {len(colors)}")
    return errors


def _has_non_absolute_plurality(grid) -> bool:
    for row in grid:
        counts = _row_counts(row)
        if len(counts) < 3:
            continue
        values = sorted(counts.values(), reverse=True)
        if values[0] > values[1] and 2 * values[0] <= sum(values):
            return True
    return False


def _has_mode_count_two(grid) -> bool:
    return any(
        (winner := _winner(row)) is not None and _row_counts(row)[winner] == 2
        for row in grid
    )


def _has_three_color_row(grid) -> bool:
    return any(len(_row_counts(row)) >= 3 for row in grid)


def strict_canonical_like(grid):
    """Lawful instances of the canonical row-local-mode task domain.

    Anti-shortcut teaching requirements live in SEMANTIC_WITNESSES.  They must
    not narrow this predicate so far that it disowns the canonical examples.
    """
    return self_check(grid)


def _filter_winner(row, predicate) -> list[int]:
    winner = _winner(row)
    if winner is None:
        return [0] * len(row)
    counts = _row_counts(row)
    if not predicate(counts, winner):
        return [0] * len(row)
    return [value if value == winner else 0 for value in row]


def _absolute_majority_only(grid):
    return [
        _filter_winner(row, lambda counts, winner: 2 * counts[winner] > sum(counts.values()))
        for row in grid
    ]


def _exactly_three(grid):
    return [
        _filter_winner(row, lambda counts, winner: counts[winner] == 3)
        for row in grid
    ]


def _at_least_three(grid):
    return [
        _filter_winner(row, lambda counts, winner: counts[winner] >= 3)
        for row in grid
    ]


def _two_colors_only(grid):
    return [
        _filter_winner(row, lambda counts, winner: len(counts) == 2)
        for row in grid
    ]


SEMANTIC_WITNESSES = {
    "non_absolute_plurality": _has_non_absolute_plurality,
    "mode_count_two": _has_mode_count_two,
    "three_color_row": _has_three_color_row,
}
SEMANTIC_RIVALS = {
    "absolute_majority_only": _absolute_majority_only,
    "exactly_three": _exactly_three,
    "at_least_three": _at_least_three,
    "two_colors_only": _two_colors_only,
}
WITNESS_RIVALS = {
    "non_absolute_plurality": ["absolute_majority_only"],
    "mode_count_two": ["exactly_three", "at_least_three"],
    "three_color_row": ["two_colors_only"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite declared-rival check; it is not a universal induction proof."""
    return [
        f"declared rival survives all demonstrations: {name}"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
    ]
