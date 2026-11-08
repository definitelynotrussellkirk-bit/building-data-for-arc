"""Semantic generator for ARC task cee14d35e7ec (Main-Diagonal Mirror).

Canonical rule: preserve every input cell.  For each blank cell, copy the
nonzero value at its transposed coordinate when one exists.  The generator
uses a short deterministic curriculum that makes both source directions,
diagonal preservation, and already-occupied transpose pairs observable.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cee14d35e7ec"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "5d70cc8bc723"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "Copy each nonzero cell into its blank transposed partner across the main "
    "diagonal, while preserving originals, diagonal cells, and already "
    "occupied transpose pairs."
)

INVARIANTS = [
    "the grid is square with side length 6..9",
    "three to six off-diagonal transpose pairs contain exactly one source cell",
    "source pairs span near-diagonal, far-diagonal, and edge positions",
    "occupied transpose pairs and diagonal marks, when present, are preserved",
]

SCENE_PROFILES = (
    "canonical_upper",
    "canonical_lower",
    "mixed_sides",
    "diagonal_context",
    "occupied_pairs",
)

# Every cyclic four-example window contains an occupied-pair counterexample
# plus sources on both sides of the diagonal.  This kills overwrite and
# one-direction-only shortcuts in the materialized lesson, not merely in a
# large aggregate sample.
SCHEDULE_PROFILES = (
    "canonical_upper",
    "occupied_pairs",
    "canonical_lower",
    "diagonal_context",
    "occupied_pairs",
    "mixed_sides",
)

AXES = {
    "grid_size": {
        "type": "int",
        "default": "difficulty-aware keyed draw",
        "valid": "6..9",
    },
    "source_pairs": {
        "type": "int",
        "default": "difficulty-aware keyed draw",
        "valid": "3..6",
    },
    "scene_profile": {
        "type": "str",
        "default": "six-slot semantic lesson schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Expose the deterministic lesson schedule to the semantic gate."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")


def _scheduled_profile(ctx, scheduled: str, overrides: dict[str, Any]) -> str:
    if overrides.get("scene_profile") is not None:
        return ctx.draw_choice("scene_profile", SCENE_PROFILES)
    return ctx.draw_choice("scene_profile", (scheduled,))


def _spread_pair_positions(n: int, count: int, rng) -> list[tuple[int, int]]:
    """Choose unordered transpose pairs with three guaranteed spatial probes."""
    all_pairs = [(r, c) for r in range(n) for c in range(r + 1, n)]
    selected: list[tuple[int, int]] = []

    def choose(candidates: list[tuple[int, int]]) -> None:
        legal = [pair for pair in candidates if pair not in selected]
        if not legal:
            raise ValueError("no legal transpose pair remains for requested witness")
        selected.append(rng.choice(legal))

    choose([(r, r + 1) for r in range(n - 1)])
    choose([(r, c) for r, c in all_pairs if c - r >= n // 2])
    choose([(r, c) for r, c in all_pairs if r == 0 or c == n - 1])

    remaining = [pair for pair in all_pairs if pair not in selected]
    rng.shuffle(remaining)
    selected.extend(remaining[: count - len(selected)])
    rng.shuffle(selected)
    return selected


def _source_sides(profile: str, count: int, rng) -> list[str]:
    if profile == "canonical_upper":
        return ["upper"] * count
    if profile == "canonical_lower":
        return ["lower"] * count
    sides = ["upper", "lower"]
    sides.extend(rng.choice(("upper", "lower")) for _ in range(count - 2))
    rng.shuffle(sides)
    return sides


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=dict(overrides),
    )

    n = ctx.draw_int_diff("grid_size", 6, 9)
    source_count = ctx.draw_int_diff("source_pairs", 3, 6)
    profile = _scheduled_profile(
        ctx,
        schedule_profile(seed, sample_index, difficulty),
        overrides,
    )
    layout_rng = ctx.draw_rng("layout")

    source_positions = _spread_pair_positions(n, source_count, layout_rng)
    sides = _source_sides(profile, source_count, layout_rng)
    palette_size = min(4, source_count)
    colors = list(
        ctx.draw_distinct_colors("colors", n=palette_size, exclude=(0,))
    )
    source_colors = [colors[index % palette_size] for index in range(source_count)]
    layout_rng.shuffle(source_colors)

    grid = full_grid(n, n, 0)
    for (row, column), side, color in zip(
        source_positions, sides, source_colors, strict=True
    ):
        if side == "upper":
            grid[row][column] = color
        else:
            grid[column][row] = color

    unavailable = set(source_positions)
    open_pairs = [
        (row, column)
        for row in range(n)
        for column in range(row + 1, n)
        if (row, column) not in unavailable
    ]
    layout_rng.shuffle(open_pairs)

    if profile == "diagonal_context":
        diagonal = layout_rng.sample(range(n), 2)
        grid[diagonal[0]][diagonal[0]] = colors[0]
        grid[diagonal[1]][diagonal[1]] = colors[-1]
    elif profile == "occupied_pairs":
        if len(open_pairs) < 2:
            raise ValueError("grid has no room for occupied-pair witnesses")
        same_pair, different_pair = open_pairs[:2]
        row, column = same_pair
        grid[row][column] = colors[0]
        grid[column][row] = colors[0]
        row, column = different_pair
        grid[row][column] = colors[1]
        grid[column][row] = colors[2]

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    return grid


def _analyze(grid) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty grid"], {}
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return ["grid rows must be sequences"], {}
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        return ["ragged grid"], {}
    n = len(grid)
    width = next(iter(widths))
    if width == 0:
        return ["empty grid"], {}
    if n != width:
        errors.append(f"expected square grid; got {n}x{width}")
    if not 6 <= n <= 9:
        errors.append(f"grid size must be 6..9; got {n}")

    values: list[int] = []
    for row in grid:
        for value in row:
            if not isinstance(value, int) or isinstance(value, bool):
                errors.append("cell values must be integers")
                return errors, {}
            values.append(value)
    if any(value < 0 or value > 9 for value in values):
        errors.append("cell value out of 0..9")

    one_sided: list[tuple[int, int, str, int]] = []
    occupied_same: list[tuple[int, int]] = []
    occupied_different: list[tuple[int, int]] = []
    if n == width:
        for row in range(n):
            for column in range(row + 1, n):
                upper = grid[row][column]
                lower = grid[column][row]
                if bool(upper) ^ bool(lower):
                    one_sided.append(
                        (
                            row,
                            column,
                            "upper" if upper else "lower",
                            upper or lower,
                        )
                    )
                elif upper and lower:
                    target = (
                        occupied_same
                        if upper == lower
                        else occupied_different
                    )
                    target.append((row, column))
    diagonal = [index for index in range(min(n, width)) if grid[index][index] != 0]
    colors = {value for value in values if value != 0}
    sides = {item[2] for item in one_sided}

    if not 3 <= len(one_sided) <= 6:
        errors.append(
            f"expected 3..6 one-sided source pairs; found {len(one_sided)}"
        )
    if not 3 <= len(colors) <= 4:
        errors.append(f"expected 3..4 nonzero colors; found {len(colors)}")

    occupied_count = len(occupied_same) + len(occupied_different)
    profile: str | None = None
    if diagonal and occupied_count:
        errors.append("diagonal and occupied-pair contexts may not be combined")
    elif occupied_count:
        if len(diagonal) != 0:
            errors.append("occupied-pair profile must have no diagonal marks")
        if len(occupied_same) != 1 or len(occupied_different) != 1:
            errors.append(
                "occupied-pair profile needs exactly one same-color and one "
                "different-color pair"
            )
        if sides != {"upper", "lower"}:
            errors.append("occupied-pair profile needs sources on both sides")
        profile = "occupied_pairs"
    elif diagonal:
        if len(diagonal) != 2:
            errors.append(f"diagonal-context profile needs exactly 2 marks; found {len(diagonal)}")
        if sides != {"upper", "lower"}:
            errors.append("diagonal-context profile needs sources on both sides")
        profile = "diagonal_context"
    elif sides == {"upper"}:
        profile = "canonical_upper"
    elif sides == {"lower"}:
        profile = "canonical_lower"
    elif sides == {"upper", "lower"}:
        profile = "mixed_sides"
    else:
        errors.append("could not infer a legal source-side profile")

    return errors, {
        "grid_size": n,
        "source_pairs": len(one_sided),
        "scene_profile": profile,
        "one_sided": one_sided,
        "occupied_same": occupied_same,
        "occupied_different": occupied_different,
        "diagonal": diagonal,
        "colors": colors,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the observable scene grammar, independent of generation metadata."""
    del difficulty, meta
    errors, _ = _analyze(grid)
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover all public axis values exactly from a valid generated input."""
    errors, analysis = _analyze(grid)
    if errors:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    return {
        "grid_size": analysis["grid_size"],
        "source_pairs": analysis["source_pairs"],
        "scene_profile": analysis["scene_profile"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Recognize the authority-linked upper-triangle canonical family."""
    errors, analysis = _analyze(grid)
    if errors:
        return errors
    if analysis["scene_profile"] != "canonical_upper":
        return ["canonical inputs place all sources above the main diagonal"]
    return []


def rule_mirror(grid):
    """Independent Python mirror of the selected canonical Racket rule."""
    n = len(grid)
    return [
        [
            grid[column][row]
            if grid[row][column] == 0 and grid[column][row] != 0
            else grid[row][column]
            for column in range(n)
        ]
        for row in range(n)
    ]


def _transpose_only(grid):
    n = len(grid)
    return [[grid[column][row] for column in range(n)] for row in range(n)]


def _upper_only_completion(grid):
    output = [list(row) for row in grid]
    n = len(grid)
    for row in range(n):
        for column in range(row + 1, n):
            if grid[row][column] != 0 and grid[column][row] == 0:
                output[column][row] = grid[row][column]
    return output


def _lower_only_completion(grid):
    output = [list(row) for row in grid]
    n = len(grid)
    for row in range(n):
        for column in range(row + 1, n):
            if grid[column][row] != 0 and grid[row][column] == 0:
                output[row][column] = grid[column][row]
    return output


def _prefer_upper_on_conflict(grid):
    """Force symmetry, choosing the upper value whenever both sides are filled."""
    output = [list(row) for row in grid]
    n = len(grid)
    for row in range(n):
        for column in range(row + 1, n):
            upper = grid[row][column]
            lower = grid[column][row]
            chosen = upper if upper != 0 else lower
            if chosen != 0:
                output[row][column] = chosen
                output[column][row] = chosen
    return output


def _prefer_lower_on_conflict(grid):
    """Force symmetry, choosing the lower value whenever both sides are filled."""
    output = [list(row) for row in grid]
    n = len(grid)
    for row in range(n):
        for column in range(row + 1, n):
            upper = grid[row][column]
            lower = grid[column][row]
            chosen = lower if lower != 0 else upper
            if chosen != 0:
                output[row][column] = chosen
                output[column][row] = chosen
    return output


SEMANTIC_RIVALS: dict[str, Callable] = {
    "transpose_only": _transpose_only,
    "upper_only_completion": _upper_only_completion,
    "lower_only_completion": _lower_only_completion,
    "prefer_upper_on_conflict": _prefer_upper_on_conflict,
    "prefer_lower_on_conflict": _prefer_lower_on_conflict,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _valid_analysis(grid) -> dict[str, Any] | None:
    errors, analysis = _analyze(grid)
    return None if errors else analysis


def _has_upper_source(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and any(item[2] == "upper" for item in analysis["one_sided"]))


def _has_lower_source(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and any(item[2] == "lower" for item in analysis["one_sided"]))


def _has_diagonal_context(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["diagonal"])


def _has_same_occupied_pair(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["occupied_same"])


def _has_different_occupied_pair(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["occupied_different"])


SEMANTIC_WITNESSES: dict[str, Callable] = {
    "upper_source": _has_upper_source,
    "lower_source": _has_lower_source,
    "diagonal_preservation": _has_diagonal_context,
    "same_color_occupied_pair": _has_same_occupied_pair,
    "different_color_occupied_pair": _has_different_occupied_pair,
}

WITNESS_RIVALS = {
    "upper_source": ["transpose_only", "lower_only_completion"],
    "lower_source": ["transpose_only", "upper_only_completion"],
    "diagonal_preservation": ["transpose_only"],
    "same_color_occupied_pair": ["transpose_only"],
    "different_color_occupied_pair": [
        "prefer_upper_on_conflict",
        "prefer_lower_on_conflict",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named shortcut fits all demonstrations."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"pair {index} input invalid: {'; '.join(errors)}")
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"pair {index} output disagrees with conditional transpose fill")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(
                    f"named competitor {name} fits every demo but changes the query"
                )
    return reasons
