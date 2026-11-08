"""Input distribution for horizontal interval completion (E141).

The unchanged Racket authority examines rows independently.  Exactly two
nonzero cells of the same color become one inclusive horizontal segment on a
fresh zero grid; every other row becomes zero.  Ordinary generated inputs carry
both canonical-fitting shortcut counterexamples in every grid: a mismatched
pair and a three-cell row whose outer colors match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "eb60199b6eb8"
TASK_ID = GENERATOR_ID
RULE_HASH = "7d5c5a67ac1a"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Rows are independent on a zero background. Exactly two separated nonzero "
    "cells of the same color are valid endpoints; the Racket rule fills their "
    "inclusive interval on a fresh grid. Ordinary samples also contain one "
    "two-color pair and one three-cell outer-match row, both of which must "
    "vanish, so every grid teaches the exact-two-and-same-color discriminator."
)

INVARIANTS = [
    "background is 0; grids are 4..10 rows by 5..12 columns",
    "ordinary draws contain 1..3 valid same-color endpoint rows",
    "valid endpoints are separated by at least one zero cell",
    "ordinary draws contain one separated mismatched pair row",
    "ordinary draws contain one three-cell row with matching outer colors",
    "ordinary draws use exactly 3..5 foreground colors",
]

# The previous palette_kind, palette_size, position_bias, density, and texture
# declarations were dead controls or aliases.  They are retired rather than
# silently accepted.  Every remaining axis is recoverable from returned pixels.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 4-row anchor every third draw; otherwise difficulty-weighted",
        "valid": "4..10",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 5/6/7-column anchor every third draw; otherwise difficulty-weighted",
        "valid": "5..12",
    },
    "n_rows": {
        "type": "int",
        "default": "scheduled 2/1/3 across canonical/broad/dense profiles",
        "valid": "1..3",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "scheduled 3/4/5 across canonical/broad/dense profiles",
        "valid": "3..5",
    },
}

# Two decoy rows are always present, so grid_h=4 cannot host n_rows=3.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [("grid_h", "n_rows")]
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
SCHEDULE_PROFILES = ("canonical_profile", "broad", "dense")
_CANONICAL_WIDTHS = (5, 6, 7)
_COLORS = tuple(range(1, 10))


class IncompatibleControls(ValueError):
    incompatible_axes = ("grid_h", "n_rows")


def schedule_profile(seed, sample_index, difficulty=None):
    """Return a finite distribution profile, never a fixed grid identity."""
    return SCHEDULE_PROFILES[(int(seed) + int(sample_index)) % len(SCHEDULE_PROFILES)]


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown or retired override axes: {unknown}")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")

    requested_h = overrides.get("grid_h")
    requested_rows = overrides.get("n_rows")
    if (
        requested_h is not None
        and requested_rows is not None
        and requested_rows + 2 > requested_h
    ):
        raise IncompatibleControls(
            f"n_rows={requested_rows} plus two decoy rows cannot fit grid_h={requested_h}"
        )


def _canonical_axes(ctx, seed: int, sample_index: int):
    width = _CANONICAL_WIDTHS[(int(seed) + int(sample_index) // 3) % len(_CANONICAL_WIDTHS)]
    return (
        ctx.draw_int_strict("grid_h", 4, 4),
        ctx.draw_int_strict("grid_w", width, width),
        ctx.draw_int_strict("n_rows", 2, 2),
        ctx.draw_int_strict("n_distinct_colors", 3, 3),
    )


def _scheduled_axes(ctx, profile: str):
    if profile == "broad":
        return (
            ctx.draw_int_diff("grid_h", 4, 10),
            ctx.draw_int_diff("grid_w", 5, 12),
            ctx.draw_int_strict("n_rows", 1, 1),
            ctx.draw_int_strict("n_distinct_colors", 4, 4),
        )
    return (
        ctx.draw_int_diff("grid_h", 5, 10),
        ctx.draw_int_diff("grid_w", 5, 12),
        ctx.draw_int_strict("n_rows", 3, 3),
        ctx.draw_int_strict("n_distinct_colors", 5, 5),
    )


def _override_axes(ctx, overrides):
    requested_rows = overrides.get("n_rows")
    requested_h = overrides.get("grid_h")

    min_height = max(4, (requested_rows or 1) + 2)
    height = ctx.draw_int_strict("grid_h", min_height, 10)
    width = ctx.draw_int_strict("grid_w", 5, 12)

    max_rows = min(3, height - 2)
    if requested_h is not None and requested_rows is None:
        rows = ctx.draw_int_diff("n_rows", 1, max_rows)
    else:
        rows = ctx.draw_int_strict("n_rows", 1, max_rows)
    colors = ctx.draw_int_strict("n_distinct_colors", 3, 5)
    return height, width, rows, colors


def _separated_pair(width: int, rng) -> tuple[int, int]:
    candidates = [(left, right) for left in range(width) for right in range(left + 2, width)]
    return rng.choice(candidates)


def _put_pair(grid, row: int, color: int, rng) -> None:
    left, right = _separated_pair(len(grid[0]), rng)
    grid[row][left] = color
    grid[row][right] = color


def _put_mismatch(grid, row: int, colors: tuple[int, int], rng) -> None:
    left, right = _separated_pair(len(grid[0]), rng)
    if rng.randrange(2):
        colors = colors[::-1]
    grid[row][left], grid[row][right] = colors


def _put_outer_match_triple(grid, row: int, outer: int, middle: int, rng) -> None:
    columns = sorted(rng.sample(range(len(grid[0])), 3))
    grid[row][columns[0]] = outer
    grid[row][columns[1]] = middle
    grid[row][columns[2]] = outer


def _pair_colors(palette: tuple[int, ...], count: int, rng) -> list[int]:
    colors: list[int] = []
    if len(palette) == 5:
        colors.append(palette[4])  # the two decoys expose only palette[0:4]
    while len(colors) < count:
        colors.append(rng.choice(palette))
    return colors


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
    profile = schedule_profile(seed, sample_index, difficulty)

    if not overrides and profile == "canonical_profile":
        height, width, n_rows, n_colors = _canonical_axes(ctx, seed, sample_index)
    elif not overrides:
        height, width, n_rows, n_colors = _scheduled_axes(ctx, profile)
    else:
        height, width, n_rows, n_colors = _override_axes(ctx, overrides)

    palette = tuple(ctx.draw_rng("foreground_palette").sample(_COLORS, n_colors))
    occupied_rows = ctx.draw_rng("row_positions").sample(range(height), n_rows + 2)
    pair_rows = occupied_rows[:n_rows]
    mismatch_row, triple_row = occupied_rows[-2:]

    grid = full_grid(height, width, 0)
    pair_colors = _pair_colors(palette, n_rows, ctx.draw_rng("pair_colors"))
    for index, (row, color) in enumerate(zip(pair_rows, pair_colors)):
        _put_pair(grid, row, color, ctx.draw_rng(f"pair_endpoints_{index}"))

    _put_mismatch(
        grid,
        mismatch_row,
        (palette[0], palette[1]),
        ctx.draw_rng("mismatch_endpoints"),
    )
    triple_middle = palette[3] if len(palette) >= 4 else palette[0]
    _put_outer_match_triple(
        grid,
        triple_row,
        palette[2],
        triple_middle,
        ctx.draw_rng("triple_positions"),
    )

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructed invalid interval-completion input: {errors}")
    if not _has_mismatched_pair_row(grid) or not _has_triple_outer_match_row(grid):
        raise RuntimeError("constructed input lost a required teaching witness")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_rows": n_rows,
        "n_distinct_colors": n_colors,
    }
    if observed != expected:
        raise RuntimeError(f"constructed axes do not round-trip: {observed} != {expected}")
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


def _nonzero_positions(row) -> list[int]:
    return [column for column, value in enumerate(row) if value != 0]


def _is_valid_pair_row(row) -> bool:
    positions = _nonzero_positions(row)
    return (
        len(positions) == 2
        and positions[1] - positions[0] >= 2
        and row[positions[0]] == row[positions[1]]
    )


def _is_mismatched_pair_row(row) -> bool:
    positions = _nonzero_positions(row)
    return (
        len(positions) == 2
        and positions[1] - positions[0] >= 2
        and row[positions[0]] != row[positions[1]]
    )


def _is_triple_outer_match_row(row) -> bool:
    positions = _nonzero_positions(row)
    return (
        len(positions) == 3
        and row[positions[0]] == row[positions[2]]
        and row[positions[1]] != row[positions[0]]
    )


def observe_overrides(grid):
    colors = {value for row in grid for value in row if value != 0}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_rows": sum(_is_valid_pair_row(row) for row in grid),
        "n_distinct_colors": len(colors),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical task manifold used by this sampler.

    The validator intentionally accepts the canonical single-cell decoy and
    canonical examples without the sampler's stronger two-witness curriculum.
    Teaching guarantees are checked separately by the semantic predicates.
    """
    errors = _grid_errors(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    if not 4 <= height <= 10 or not 5 <= width <= 12:
        errors.append("shape must be within 4..10 rows by 5..12 columns")

    valid_pairs = 0
    for row_index, row in enumerate(grid):
        positions = _nonzero_positions(row)
        if len(positions) > 3:
            errors.append(f"row {row_index} has more than three nonzero cells")
            continue
        if len(positions) == 2 and row[positions[0]] == row[positions[1]]:
            if positions[1] - positions[0] < 2:
                errors.append(f"row {row_index} same-color endpoints must be separated")
            else:
                valid_pairs += 1
        elif len(positions) == 2 and positions[1] - positions[0] < 2:
            errors.append(f"row {row_index} mismatched endpoints must be separated")

    if not 1 <= valid_pairs <= 3:
        errors.append(f"expected 1..3 valid same-color pair rows, got {valid_pairs}")
    colors = {value for row in grid for value in row if value != 0}
    if not 1 <= len(colors) <= 5:
        errors.append(f"expected 1..5 foreground colors, got {len(colors)}")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _blank_like(grid):
    return [[0 for _ in row] for row in grid]


def _connect_any_two(grid):
    output = _blank_like(grid)
    for row_index, row in enumerate(grid):
        positions = _nonzero_positions(row)
        if len(positions) != 2:
            continue
        left, right = positions
        for column in range(left, right + 1):
            output[row_index][column] = row[left]
    return output


def _connect_outermost_same(grid):
    output = _blank_like(grid)
    for row_index, row in enumerate(grid):
        positions = _nonzero_positions(row)
        if len(positions) < 2:
            continue
        left, right = positions[0], positions[-1]
        if row[left] != row[right]:
            continue
        for column in range(left, right + 1):
            output[row_index][column] = row[left]
    return output


def _preserve_invalid_rows(grid):
    output = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        if not _is_valid_pair_row(row):
            continue
        left, right = _nonzero_positions(row)
        output[row_index] = [0] * len(row)
        for column in range(left, right + 1):
            output[row_index][column] = row[left]
    return output


def _has_valid_pair_row(grid) -> bool:
    return any(_is_valid_pair_row(row) for row in grid)


def _has_mismatched_pair_row(grid) -> bool:
    return any(_is_mismatched_pair_row(row) for row in grid)


def _has_triple_outer_match_row(grid) -> bool:
    return any(_is_triple_outer_match_row(row) for row in grid)


SEMANTIC_WITNESSES = {
    "valid_pair_row": _has_valid_pair_row,
    "mismatched_pair_row": _has_mismatched_pair_row,
    "triple_outer_match_row": _has_triple_outer_match_row,
}
BRANCH_WITNESSES = {"valid_pair_row"}
SEMANTIC_RIVALS = {
    "connect_any_two": _connect_any_two,
    "connect_outermost_same": _connect_outermost_same,
    "preserve_invalid_rows": _preserve_invalid_rows,
}
WITNESS_RIVALS = {
    "mismatched_pair_row": ["connect_any_two", "preserve_invalid_rows"],
    "triple_outer_match_row": ["connect_outermost_same", "preserve_invalid_rows"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite declared-rival check; not a proof over undeclared hypotheses."""
    return [
        f"declared rival survives all demonstrations: {name}"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
    ]
