"""Generator for ARC task 9bfbec04496c.

A 3×3 mosaic repeats one small tile, with uniform separator rows and columns.
The selected rule compresses the mosaic to one tile and paints every local cell
where the nine copies are not unanimous blue (1).

The generator deliberately places both an 8-to-1 disagreement and a broader
7-to-2-or-stronger disagreement in every instance.  That pair of witnesses
teaches "any disagreement" rather than either threshold shortcut.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "9bfbec04496c"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "25e19a18a7ae"

SUMMARY = (
    "A 3×3 mosaic repeats a 2×2, 2×3, 3×2, or 3×3 base tile, with two "
    "uniform separator rows and columns.  At least two local cells disagree "
    "across the nine copies: one has exactly one outlier and one has two to "
    "four outliers.  Compress to one tile, preserving unanimous values and "
    "painting every non-unanimous local cell blue (1)."
)

INVARIANTS = [
    "exactly three tile rows and three tile columns",
    "two equally spaced separator rows and columns of one nonzero color",
    "tile cells never use the separator color",
    "every generated input has at least one 8-to-1 disagreement",
    "every generated input has at least one 7-to-2-or-broader disagreement",
    "generated inputs omit blue 1 so disagreement markers are visibly introduced",
]

TILE_SHAPES = ("2x2", "2x3", "3x2", "3x3")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
PALETTE_POOLS = {
    "warm": (0, 2, 3, 4, 6, 9),
    "cool": (0, 5, 7, 8),
    "broad": (0, 2, 3, 4, 5, 6, 7, 8, 9),
    "primary": (0, 2, 3, 4),
}

# Negative textures are no longer advertised as ordinary generation controls.
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "tile_shape": {
        "type": "str",
        "default": "sample_index cycle",
        "valid": "2x2|2x3|3x2|3x3",
    },
    "palette_kind": {
        "type": "str",
        "default": "rng helpful",
        "valid": "warm|cool|broad|primary",
    },
    "n_mut": {
        "type": "int",
        "default": "difficulty-aware 2..4",
        "valid": "2..4",
    },
    "multi_outliers": {
        "type": "int",
        "default": "difficulty-aware 2..4",
        "valid": "2..4",
    },
}

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0


def _validate_request(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty is not None:
        if type(difficulty) is not str:
            raise TypeError("difficulty must be one of easy, medium, hard, or None")
        if difficulty not in {"easy", "medium", "hard"}:
            raise ValueError("difficulty must be one of easy, medium, hard, or None")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    if "tile_shape" in overrides and overrides["tile_shape"] is not None:
        value = overrides["tile_shape"]
        if type(value) is not str:
            raise TypeError("tile_shape override must be a string")
        if value not in TILE_SHAPES:
            raise ValueError(f"tile_shape must be one of {TILE_SHAPES}")

    if "palette_kind" in overrides and overrides["palette_kind"] is not None:
        value = overrides["palette_kind"]
        if type(value) is not str:
            raise TypeError("palette_kind override must be a string")
        if value not in PALETTE_KINDS:
            raise ValueError(f"palette_kind must be one of {PALETTE_KINDS}")

    for name in ("n_mut", "multi_outliers"):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
        if not 2 <= value <= 4:
            raise ValueError(f"{name} override must be in 2..4")


def _shape_dimensions(name: str) -> tuple[int, int]:
    height, width = name.split("x", 1)
    return int(height), int(width)


def _default_n_mut(ctx, difficulty: str | None, cell_count: int) -> int:
    if difficulty == "easy":
        return ctx.draw_int_strict("n_mut", 2, 2)
    if difficulty == "medium":
        return ctx.draw_int_strict("n_mut", 2, min(3, cell_count))
    if difficulty == "hard":
        return ctx.draw_int_strict("n_mut", min(3, cell_count), min(4, cell_count))
    return ctx.draw_int_strict("n_mut", 2, min(4, cell_count))


def _default_multi_outliers(ctx, difficulty: str | None) -> int:
    if difficulty == "easy":
        return ctx.draw_int_strict("multi_outliers", 2, 2)
    if difficulty == "medium":
        return ctx.draw_int_strict("multi_outliers", 2, 3)
    if difficulty == "hard":
        return ctx.draw_int_strict("multi_outliers", 3, 4)
    return ctx.draw_int_strict("multi_outliers", 2, 4)


def _base_tile(
    rng,
    *,
    tile_h: int,
    tile_w: int,
    palette: list[int],
) -> list[list[int]]:
    values = [rng.choice(palette) for _ in range(tile_h * tile_w)]
    if len(set(values)) == 1:
        replacement = next(color for color in palette if color != values[0])
        values[-1] = replacement
    return [values[row * tile_w:(row + 1) * tile_w] for row in range(tile_h)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic separator-mosaic input grid."""
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides={},
    )
    rng = ctx.draw_rng("layout")

    tile_shape = overrides.get("tile_shape")
    if tile_shape is None:
        tile_shape = TILE_SHAPES[sample_index % len(TILE_SHAPES)]
    tile_h, tile_w = _shape_dimensions(tile_shape)

    palette_kind = overrides.get("palette_kind")
    if palette_kind is None:
        palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    pool = list(PALETTE_POOLS[palette_kind])
    separator_candidates = [color for color in pool if color not in {0, 1}]
    separator_color = rng.choice(separator_candidates)
    tile_palette = [color for color in pool if color not in {1, separator_color}]
    if len(tile_palette) < 2:  # Defensive; all declared pools currently have >= 2.
        tile_palette = [color for color in range(10) if color not in {1, separator_color}]

    base_tile = _base_tile(
        rng,
        tile_h=tile_h,
        tile_w=tile_w,
        palette=tile_palette,
    )
    tiles = [copy_grid(base_tile) for _ in range(9)]

    cell_count = tile_h * tile_w
    n_mut = overrides.get("n_mut")
    if n_mut is None:
        n_mut = _default_n_mut(ctx, difficulty, cell_count)
    multi_outliers = overrides.get("multi_outliers")
    if multi_outliers is None:
        multi_outliers = _default_multi_outliers(ctx, difficulty)

    local_cells = rng.sample(
        [(row, col) for row in range(tile_h) for col in range(tile_w)],
        n_mut,
    )
    for mutation_index, (row, col) in enumerate(local_cells):
        if mutation_index == 0:
            outlier_count = 1
        elif mutation_index == 1:
            outlier_count = multi_outliers
        else:
            outlier_count = rng.choice((1, multi_outliers))
        tile_indexes = rng.sample(range(9), outlier_count)
        base_value = base_tile[row][col]
        replacements = [color for color in tile_palette if color != base_value]
        for tile_index in tile_indexes:
            tiles[tile_index][row][col] = rng.choice(replacements)

    height = 3 * tile_h + 2
    width = 3 * tile_w + 2
    grid = full_grid(height, width, separator_color)
    for tile_row in range(3):
        for tile_col in range(3):
            tile = tiles[tile_row * 3 + tile_col]
            row0 = tile_row * (tile_h + 1)
            col0 = tile_col * (tile_w + 1)
            for row in range(tile_h):
                for col in range(tile_w):
                    grid[row0 + row][col0 + col] = tile[row][col]
    return grid


def copy_grid(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _grid_shape_errors(grid: Any) -> list[str]:
    if type(grid) is not list or not grid:
        return ["grid must be a nonempty list of rows"]
    if type(grid[0]) is not list or not grid[0]:
        return ["grid rows must be nonempty lists"]
    width = len(grid[0])
    errors: list[str] = []
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        errors.append("grid dimensions must be in 1..30")
    for row_index, row in enumerate(grid):
        if type(row) is not list or len(row) != width:
            errors.append(f"row {row_index} is ragged or not a list")
            continue
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            errors.append(f"row {row_index} contains a non-integer or out-of-range color")
    return errors


def _analyze_grid(grid: Any, *, require_disagreement: bool) -> tuple[dict[str, Any] | None, list[str]]:
    errors = _grid_shape_errors(grid)
    if errors:
        return None, errors

    height = len(grid)
    width = len(grid[0])
    full_rows = [row for row in range(height) if len(set(grid[row])) == 1]
    full_cols = [
        col
        for col in range(width)
        if len({grid[row][col] for row in range(height)}) == 1
    ]
    if len(full_rows) != 2:
        errors.append(f"expected exactly two uniform separator rows, found {len(full_rows)}")
    if len(full_cols) != 2:
        errors.append(f"expected exactly two uniform separator columns, found {len(full_cols)}")
    if errors:
        return None, errors

    separator_color = grid[full_rows[0]][0]
    if separator_color == 0:
        errors.append("separator color must be nonzero")
    if any(grid[row][0] != separator_color for row in full_rows):
        errors.append("separator rows use different colors")
    if any(grid[0][col] != separator_color for col in full_cols):
        errors.append("separator columns do not match separator-row color")

    tile_h = full_rows[0]
    tile_w = full_cols[0]
    expected_rows = [tile_h, 2 * tile_h + 1]
    expected_cols = [tile_w, 2 * tile_w + 1]
    if full_rows != expected_rows or height != 3 * tile_h + 2:
        errors.append("separator rows are not equally spaced for a 3x3 mosaic")
    if full_cols != expected_cols or width != 3 * tile_w + 2:
        errors.append("separator columns are not equally spaced for a 3x3 mosaic")
    if tile_h not in {2, 3} or tile_w not in {2, 3}:
        errors.append("tile dimensions must each be 2 or 3")
    if errors:
        return None, errors

    separator_rows = set(full_rows)
    separator_cols = set(full_cols)
    for row in range(height):
        for col in range(width):
            if row in separator_rows or col in separator_cols:
                if grid[row][col] != separator_color:
                    errors.append("separator lines are not solid")
                    return None, errors
            elif grid[row][col] == separator_color:
                errors.append("separator color appears inside a tile")
                return None, errors

    row_starts = (0, tile_h + 1, 2 * (tile_h + 1))
    col_starts = (0, tile_w + 1, 2 * (tile_w + 1))
    cell_values: list[list[tuple[int, ...]]] = []
    outlier_counts: list[int] = []
    modal_values: list[list[int]] = []
    for local_row in range(tile_h):
        value_row: list[tuple[int, ...]] = []
        modal_row: list[int] = []
        for local_col in range(tile_w):
            values = tuple(
                grid[row0 + local_row][col0 + local_col]
                for row0 in row_starts
                for col0 in col_starts
            )
            counts = Counter(values)
            modal_value, modal_count = counts.most_common(1)[0]
            if len(counts) > 1 and modal_count < 5:
                errors.append(
                    f"local cell ({local_row},{local_col}) has no strict majority"
                )
            value_row.append(values)
            modal_row.append(modal_value)
            outlier_counts.append(9 - modal_count)
        cell_values.append(value_row)
        modal_values.append(modal_row)
    if errors:
        return None, errors

    disagreement_counts = [count for count in outlier_counts if count > 0]
    if require_disagreement and not disagreement_counts:
        errors.append("all nine tiles are identical; no disagreement is taught")
        return None, errors

    facts = {
        "height": height,
        "width": width,
        "tile_h": tile_h,
        "tile_w": tile_w,
        "separator_color": separator_color,
        "cell_values": cell_values,
        "modal_values": modal_values,
        "outlier_counts": tuple(outlier_counts),
        "disagreement_cells": len(disagreement_counts),
        "single_outlier_cells": sum(count == 1 for count in disagreement_counts),
        "multi_outlier_cells": sum(count >= 2 for count in disagreement_counts),
        "max_outliers": max(disagreement_counts, default=0),
    }
    return facts, []


def semantic_observables(grid: Any) -> dict[str, Any]:
    facts, errors = _analyze_grid(grid, require_disagreement=True)
    if errors or facts is None:
        raise ValueError("; ".join(errors))
    return facts


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover exact mutation axes from the returned mosaic itself."""
    facts = semantic_observables(grid)
    return {
        "n_mut": facts["disagreement_cells"],
        "multi_outliers": facts["max_outliers"],
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Return short reasons unless grid is a lawful, nontrivial task input."""
    del difficulty, meta
    _facts, errors = _analyze_grid(grid, require_disagreement=True)
    return errors


def strict_canonical_like(grid):
    """Semantic-gate hook for the canonical/generator input manifold."""
    return self_check(grid)


def _render_from_cells(
    facts: dict[str, Any],
    resolver,
) -> list[list[int]]:
    return [
        [resolver(facts["cell_values"][row][col]) for col in range(facts["tile_w"])]
        for row in range(facts["tile_h"])
    ]


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure Python mirror of the unchanged canonical Racket rule."""
    facts = semantic_observables(grid)
    return _render_from_cells(
        facts,
        lambda values: values[0] if len(set(values)) == 1 else 1,
    )


def _modal_value(values: tuple[int, ...]) -> tuple[int, int]:
    value, count = Counter(values).most_common(1)[0]
    return value, count


def _rival_eight_to_one_only(grid: Any) -> list[list[int]]:
    facts = semantic_observables(grid)

    def resolve(values: tuple[int, ...]) -> int:
        if len(set(values)) == 1:
            return values[0]
        modal, count = _modal_value(values)
        return 1 if count == 8 else modal

    return _render_from_cells(facts, resolve)


def _rival_two_or_more_only(grid: Any) -> list[list[int]]:
    facts = semantic_observables(grid)

    def resolve(values: tuple[int, ...]) -> int:
        if len(set(values)) == 1:
            return values[0]
        modal, count = _modal_value(values)
        return 1 if 9 - count >= 2 else modal

    return _render_from_cells(facts, resolve)


def _rival_fixed_2x2(grid: Any) -> list[list[int]]:
    return [row[:2] for row in rule_mirror(grid)[:2]]


SEMANTIC_RIVALS = {
    "eight_to_one_only": _rival_eight_to_one_only,
    "two_or_more_only": _rival_two_or_more_only,
    "fixed_2x2": _rival_fixed_2x2,
}
CANONICAL_SHORTCUTS = {
    "eight_to_one_only": _rival_eight_to_one_only,
    "fixed_2x2": _rival_fixed_2x2,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _has_single_outlier(grid: Any) -> bool:
    try:
        return semantic_observables(grid)["single_outlier_cells"] > 0
    except (TypeError, ValueError):
        return False


def _has_multi_outlier(grid: Any) -> bool:
    try:
        return semantic_observables(grid)["multi_outlier_cells"] > 0
    except (TypeError, ValueError):
        return False


def _has_non_2x2_tile(grid: Any) -> bool:
    try:
        facts = semantic_observables(grid)
    except (TypeError, ValueError):
        return False
    return (facts["tile_h"], facts["tile_w"]) != (2, 2)


SEMANTIC_WITNESSES = {
    "single_outlier_disagreement": _has_single_outlier,
    "multi_outlier_disagreement": _has_multi_outlier,
    "non_2x2_tile": _has_non_2x2_tile,
}
WITNESS_RIVALS = {
    "single_outlier_disagreement": ["two_or_more_only"],
    "multi_outlier_disagreement": ["eight_to_one_only"],
    "non_2x2_tile": ["fixed_2x2"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons when the demonstrations leave a declared rival alive."""
    reasons: list[str] = []
    if type(demos) is not list or not demos:
        return ["demonstrations must be a nonempty list"]

    normalized: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is missing input/output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except (TypeError, ValueError) as error:
            reasons.append(f"demo {index} is off-manifold: {error}")
            continue
        if pair["output"] != expected:
            reasons.append(f"demo {index} label does not match the selected rule")
            continue
        normalized.append(pair)

    if len(normalized) != len(demos):
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in normalized):
            reasons.append(f"competitor {name} fits every demonstration")

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is missing input/output")
    else:
        try:
            expected_query = rule_mirror(query["input"])
        except (TypeError, ValueError) as error:
            reasons.append(f"query is off-manifold: {error}")
        else:
            if query["output"] != expected_query:
                reasons.append("query label does not match the selected rule")
    return reasons
