"""Generator for training puzzle 8403a5d5 / task 24247834f3c9.

A square zero-background grid contains one colored seed on the bottom row.
The Racket authority expands the seed into same-colored vertical stripes at
columns ``seed_col, seed_col + 2, ...``.  The intervening columns receive a
single gray marker (color 5), alternating top, bottom, top, bottom from left
to right.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "24247834f3c9"
VERSION = "2.3.0"
TASK_ID = "24247834f3c9"
RULE_HASH = "50abe84b936b"
EXAMPLES_NEEDED = 2

SUMMARY = (
    "A 10-18 square zero-background grid contains exactly one nonzero, "
    "non-gray seed on the bottom row in columns 1-5.  Extend that seed "
    "color upward through its column and every second column to the right. "
    "In each intervening column, place one gray 5 marker, alternating "
    "between the top and bottom rows beginning at the top."
)

INVARIANTS = [
    "the grid is square with side length 10..18 and background exactly 0",
    "there is exactly one nonzero seed, on the bottom row, in columns 1..5",
    "the seed color is one of 1,2,3,4,6,7,8,9 (never 0 or marker color 5)",
    "at least three stripe columns and two alternating gray markers are visible",
]

GRID_SIZE_OPTIONS = (10, 10, 10, 11, 12, 13, 14, 15, 16, 17, 18)
GRID_SIZE_OPTIONS_BY_BAND = {
    None: GRID_SIZE_OPTIONS,
    # Every band includes the complete public override domain; only its mass
    # shifts.  This keeps exact overrides honest while avoiding a dead knob.
    "easy": (10, 10, 10, 10, 10, 11, 12, 13, 14, 15, 16, 17, 18),
    "medium": (10, 10, 10, 10, 11, 12, 13, 14, 14, 14, 15, 16, 17, 18),
    "hard": (10, 10, 10, 10, 11, 12, 13, 14, 15, 16, 17, 18, 18, 18, 18),
}
SEED_COLUMNS = (1, 2, 3, 4, 5)
SEED_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)

AXES = {
    "grid_n": {
        "type": "int",
        "default": "difficulty-keyed choice; every band retains canonical size 10",
        "valid": "10|11|12|13|14|15|16|17|18",
    },
    "seed_col": {
        "type": "int",
        "default": "keyed choice across canonical-supported columns",
        "valid": "1|2|3|4|5",
    },
    "fg_color": {
        "type": "color",
        "default": "keyed choice excluding background 0 and marker 5",
        "valid": "1|2|3|4|6|7|8|9",
    },
}

# Every declared boundary combination is lawful: n >= 10 and seed_col <= 5
# always leave at least five columns to the right-inclusive stripe span.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input grid.

    Difficulty is accepted for the shared generator API, but the same exact
    task grammar is used in every band.  This keeps every override boundary
    valid in every band while the keyed RNG still varies all three axes.
    """
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    n = int(ctx.draw_choice("grid_n", GRID_SIZE_OPTIONS_BY_BAND[difficulty]))
    seed_col = int(ctx.draw_choice("seed_col", SEED_COLUMNS))
    fg_color = int(ctx.draw_choice("fg_color", SEED_COLORS))

    grid = full_grid(n, n, 0)
    grid[n - 1][seed_col] = fg_color
    return grid


def _coerce_grid(grid: Any) -> list[list[Any]]:
    if not isinstance(grid, list):
        return []
    return [list(row) if isinstance(row, (list, tuple, str)) else [] for row in grid]


def _seed_info(grid: list[list[int]]) -> tuple[int, int, int] | None:
    nonzero = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    return nonzero[0] if len(nonzero) == 1 else None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, degenerate, and rule-hiding teaching scenes."""
    del difficulty, meta
    rows = _coerce_grid(grid)
    if not rows or not rows[0]:
        return ["grid must be a non-empty list of non-empty rows"]
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        return ["grid must be rectangular"]

    errors: list[str] = []
    height = len(rows)
    if height != width:
        errors.append(f"grid must be square, got {height}x{width}")
    if not 10 <= height <= 18 or not 10 <= width <= 18:
        errors.append(f"grid side length must be 10..18, got {height}x{width}")

    invalid = [
        (r, c, value)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if invalid:
        errors.append(f"grid contains invalid ARC colors at {invalid[:3]}")
        return errors

    seed = _seed_info(rows)
    if seed is None:
        nonzero_count = sum(value != 0 for row in rows for value in row)
        errors.append(
            "expected exactly one nonzero seed on a zero background, "
            f"found {nonzero_count} nonzero cells"
        )
        return errors

    seed_row, seed_col, seed_color = seed
    if seed_row != height - 1:
        errors.append("the unique seed must be on the bottom row")
    if seed_col not in SEED_COLUMNS:
        errors.append("the seed column must be one of 1,2,3,4,5")
    if seed_color not in SEED_COLORS:
        errors.append("the seed color must be nonzero and not marker color 5")

    stripe_columns = list(range(seed_col, width, 2))
    marker_columns = list(range(seed_col + 1, width, 2))
    if len(stripe_columns) < 3:
        errors.append("scene must expose at least three vertical stripe columns")
    if len(marker_columns) < 2:
        errors.append("scene must expose at least two alternating marker columns")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked lawful-manifold predicate for the semantic gate."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact public axis from a returned input grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    rows = _coerce_grid(grid)
    seed = _seed_info(rows)
    assert seed is not None
    _, seed_col, seed_color = seed
    return {
        "grid_n": len(rows),
        "seed_col": seed_col,
        "fg_color": seed_color,
    }


def _solve_official(grid: list[list[int]]) -> list[list[int]]:
    """Python mirror used only for task-local semantic tests and rivals."""
    rows = _coerce_grid(grid)
    seed = _seed_info(rows)
    if seed is None:
        raise ValueError("official mirror requires exactly one nonzero seed")
    height, width = len(rows), len(rows[0])
    _, seed_col, seed_color = seed
    output = full_grid(height, width, 0)
    for col in range(seed_col, width, 2):
        for row in range(height):
            output[row][col] = seed_color
    for index, col in enumerate(range(seed_col + 1, width, 2)):
        output[0 if index % 2 == 0 else height - 1][col] = 5
    return output


def _solve_contiguous_fill(grid: list[list[int]]) -> list[list[int]]:
    """Rival: fill every column from the seed rightward, with no gaps."""
    rows = _coerce_grid(grid)
    seed = _seed_info(rows)
    if seed is None:
        raise ValueError("contiguous-fill rival requires one seed")
    height, width = len(rows), len(rows[0])
    _, seed_col, seed_color = seed
    output = full_grid(height, width, 0)
    for col in range(seed_col, width):
        for row in range(height):
            output[row][col] = seed_color
    return output


def _solve_top_markers_only(grid: list[list[int]]) -> list[list[int]]:
    """Rival: correct stripes, but place every gray marker on the top row."""
    rows = _coerce_grid(grid)
    seed = _seed_info(rows)
    if seed is None:
        raise ValueError("top-marker rival requires one seed")
    height, width = len(rows), len(rows[0])
    _, seed_col, seed_color = seed
    output = full_grid(height, width, 0)
    for col in range(seed_col, width, 2):
        for row in range(height):
            output[row][col] = seed_color
    for col in range(seed_col + 1, width, 2):
        output[0][col] = 5
    return output


def _solve_bottom_row_echo(grid: list[list[int]]) -> list[list[int]]:
    """Rival: repeat the seed horizontally only on the bottom row."""
    rows = _coerce_grid(grid)
    seed = _seed_info(rows)
    if seed is None:
        raise ValueError("bottom-row rival requires one seed")
    height, width = len(rows), len(rows[0])
    _, seed_col, seed_color = seed
    output = full_grid(height, width, 0)
    for col in range(seed_col, width, 2):
        output[height - 1][col] = seed_color
    for index, col in enumerate(range(seed_col + 1, width, 2)):
        output[0 if index % 2 == 0 else height - 1][col] = 5
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "contiguous_fill": _solve_contiguous_fill,
    "top_markers_only": _solve_top_markers_only,
    "bottom_row_echo": _solve_bottom_row_echo,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _rival_differs(grid, name: str) -> bool:
    try:
        return _solve_official(grid) != SEMANTIC_RIVALS[name](grid)
    except Exception:
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "alternating_blank_columns_visible": lambda grid: _rival_differs(
        grid, "contiguous_fill"
    ),
    "top_bottom_marker_alternation_visible": lambda grid: _rival_differs(
        grid, "top_markers_only"
    ),
    "vertical_extension_visible": lambda grid: _rival_differs(
        grid, "bottom_row_echo"
    ),
}

WITNESS_RIVALS = {
    "alternating_blank_columns_visible": ["contiguous_fill"],
    "top_bottom_marker_alternation_visible": ["top_markers_only"],
    "vertical_extension_visible": ["bottom_row_echo"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every named shortcut to be eliminated by the demonstrations."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(
            f"lesson needs at least {EXAMPLES_NEEDED} demonstrations, got {len(demos)}"
        )
        return reasons

    for index, pair in enumerate(demos):
        errors = strict_canonical_like(pair.get("input"))
        if errors:
            reasons.append(f"demo {index} is not lawful: {errors[0]}")
    query_errors = strict_canonical_like(query.get("input"))
    if query_errors:
        reasons.append(f"query is not lawful: {query_errors[0]}")

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                rival(pair["input"]) == pair["output"] for pair in demos
            )
            if survives and rival(query["input"]) != query["output"]:
                reasons.append(
                    f"competitor {name} fits every demo and changes the query answer"
                )
        except Exception as exc:
            reasons.append(
                f"competitor {name} errored: {type(exc).__name__}: {exc}"
            )
    return reasons
