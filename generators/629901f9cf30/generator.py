"""Lesson generator for ARC task 629901f9cf30: Manhattan Voronoi seeds.

Every nonzero input cell is a seed.  Each output cell takes the color of its
unique nearest seed in Manhattan distance; cells tied between different nearest
seed colors remain background 0.  The sampler constructs a visible tie in every
instance and schedules more-than-three-seed scenes so the canonical-fitting
"first three seeds only" shortcut cannot survive a three-demo lesson.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Seed = tuple[int, int, int]

GENERATOR_ID = "629901f9cf30"
TASK_ID = GENERATOR_ID
RULE_HASH = "96013a689278"
VERSION = "3.0.0"
SUMMARY = (
    "A 4..18 rectangular zero-background grid contains 2..6 distinct-color "
    "single-cell seeds. Fill each cell from its unique nearest Manhattan seed; "
    "leave cells tied between different nearest colors as 0."
)

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("three_seeds", "four_seeds", "six_seeds")
_PROFILE_SEED_COUNTS = {"three_seeds": 3, "four_seeds": 4, "six_seeds": 6}
MIN_STRICT_FRAC = 1.0
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

INVARIANTS = [
    "input dimensions are independently 4..18",
    "there are 2..6 nonzero single-cell seeds",
    "seed colors are distinct ARC colors 1..9",
    "every generated input contains at least one genuine nearest-color tie",
    "every three consecutive default samples include a scene with more than three seeds",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-weighted", "valid": "4..18"},
    "grid_w": {"type": "int", "default": "difficulty-weighted", "valid": "4..18"},
    "n_seeds": {"type": "int", "default": "periodic 3|4|6", "valid": "2..6"},
}

_INT_AXES = {"grid_h": (4, 18), "grid_w": (4, 18), "n_seeds": (2, 6)}
_DIFFICULTIES = (None, "easy", "medium", "hard")


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer (not bool)")
    if difficulty not in _DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        lo, hi = _INT_AXES[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def schedule_profile(seed: Any, sample_index: int, difficulty: Any = None) -> str:
    """Exact period-three coverage schedule; seed/band affect geometry only."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _dimension_options(difficulty: Any) -> tuple[int, ...]:
    if difficulty == "easy":
        return tuple(range(4, 9))
    if difficulty == "medium":
        return tuple(range(8, 15))
    if difficulty == "hard":
        return tuple(range(14, 19))
    return tuple(range(4, 19))


def _draw_axis(ctx, name: str, lo: int, hi: int, options: tuple[int, ...]) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return int(ctx.draw_choice(name, options))


def _tie_templates(height: int, width: int) -> list[tuple[tuple[int, int], tuple[int, int], tuple[int, int]]]:
    templates = []
    for row in range(height):
        for col in range(width - 2):
            templates.append(((row, col), (row, col + 1), (row, col + 2)))
    for row in range(height - 2):
        for col in range(width):
            templates.append(((row, col), (row + 1, col), (row + 2, col)))
    return templates


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one deterministic sparse seed grid with a guaranteed tie."""
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    dimensions = _dimension_options(difficulty)
    height = _draw_axis(ctx, "grid_h", 4, 18, dimensions)
    width = _draw_axis(ctx, "grid_w", 4, 18, dimensions)
    profile = schedule_profile(seed, sample_index, difficulty)
    seed_options = (_PROFILE_SEED_COUNTS[profile],)
    n_seeds = _draw_axis(ctx, "n_seeds", 2, 6, seed_options)

    layout_rng = ctx.draw_rng("layout")
    first, midpoint, second = layout_rng.choice(_tie_templates(height, width))
    colors = ctx.draw_rng("seed_colors").sample(tuple(range(1, 10)), n_seeds)
    occupied = {first, midpoint, second}
    remaining = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in occupied
    ]
    extras = layout_rng.sample(remaining, n_seeds - 2)

    grid = full_grid(height, width, 0)
    grid[first[0]][first[1]] = colors[0]
    grid[second[0]][second[1]] = colors[1]
    for (row, col), color in zip(extras, colors[2:]):
        grid[row][col] = color
    return grid


def _parse_basic(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None, ["expected a rectangular grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return None, ["cells must be literal integer ARC colors 0..9"]
    height = len(grid)
    seeds: list[Seed] = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    return {"grid_h": height, "grid_w": width, "seeds": seeds}, []


def _render(info: dict[str, Any], *, seed_limit: int | None = None, tie_policy: str = "zero") -> Grid:
    seeds: list[Seed] = info["seeds"]
    if seed_limit is not None:
        seeds = seeds[:seed_limit]
    if not seeds:
        raise ValueError("Voronoi rule requires at least one seed")
    output: Grid = []
    for row in range(info["grid_h"]):
        values = []
        for col in range(info["grid_w"]):
            distances = [
                (abs(row - seed_row) + abs(col - seed_col), color)
                for seed_row, seed_col, color in seeds
            ]
            nearest = min(distance for distance, _ in distances)
            colors = sorted({color for distance, color in distances if distance == nearest})
            values.append(colors[0] if len(colors) == 1 or tie_policy == "lowest" else 0)
        output.append(values)
    return output


def _tie_positions(info: dict[str, Any]) -> set[tuple[int, int]]:
    intended = _render(info)
    lowest = _render(info, tie_policy="lowest")
    return {
        (row, col)
        for row in range(info["grid_h"])
        for col in range(info["grid_w"])
        if intended[row][col] != lowest[row][col]
    }


def _analyze(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    info, errors = _parse_basic(grid)
    if info is None:
        return None, errors
    height, width = info["grid_h"], info["grid_w"]
    if not 4 <= height <= 18:
        errors.append(f"grid height {height} outside [4, 18]")
    if not 4 <= width <= 18:
        errors.append(f"grid width {width} outside [4, 18]")
    seeds: list[Seed] = info["seeds"]
    if not 2 <= len(seeds) <= 6:
        errors.append(f"seed count {len(seeds)} outside [2, 6]")
    colors = [color for _, _, color in seeds]
    if len(set(colors)) != len(colors):
        errors.append(f"seed colors must be distinct, found {colors}")
    if not errors:
        ties = _tie_positions(info)
        info["tie_positions"] = ties
        if not ties:
            errors.append("expected at least one nearest-color tie cell")
    return info, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    _, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    info, errors = _analyze(grid)
    if info is None or errors:
        raise ValueError("invalid generator grid: " + "; ".join(errors))
    return {
        "grid_h": info["grid_h"],
        "grid_w": info["grid_w"],
        "n_seeds": len(info["seeds"]),
    }


def rule_mirror(grid) -> Grid:
    info, errors = _analyze(grid)
    if info is None or errors:
        raise ValueError("cannot apply rule to invalid grid: " + "; ".join(errors))
    return _render(info)


def _first_three_seeds_only(grid) -> Grid:
    info, errors = _analyze(grid)
    if info is None or errors:
        raise ValueError("cannot apply rival to invalid grid: " + "; ".join(errors))
    return _render(info, seed_limit=3)


def _lowest_color_on_ties(grid) -> Grid:
    info, errors = _analyze(grid)
    if info is None or errors:
        raise ValueError("cannot apply rival to invalid grid: " + "; ".join(errors))
    return _render(info, tie_policy="lowest")


def _more_than_three_seeds(grid) -> bool:
    info, errors = _analyze(grid)
    return bool(info is not None and not errors and len(info["seeds"]) > 3)


def _tie_cells_remain_zero(grid) -> bool:
    info, errors = _analyze(grid)
    return bool(info is not None and not errors and info.get("tie_positions"))


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "more_than_three_seeds": _more_than_three_seeds,
    "tie_cells_remain_zero": _tie_cells_remain_zero,
}
SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "first_three_seeds_only": _first_three_seeds_only,
    "lowest_color_on_ties": _lowest_color_on_ties,
}
WITNESS_RIVALS = {
    "more_than_three_seeds": ["first_three_seeds_only"],
    "tie_cells_remain_zero": ["lowest_color_on_ties"],
}
CANONICAL_SHORTCUTS = {"first_three_seeds_only": _first_three_seeds_only}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def semantic_observables(grid) -> dict[str, Any]:
    info, errors = _analyze(grid)
    if info is None:
        return {"errors": errors}
    return {
        "errors": errors,
        **(observe_overrides(grid) if not errors else {}),
        "tie_cells": len(info.get("tie_positions", ())),
        "more_than_three_seeds": not errors and len(info["seeds"]) > 3,
    }


def lesson_identifiable(demos, query) -> list[str]:
    """Reject malformed labels or a named rival left consistent with all demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]
    reasons: list[str] = []
    for index, item in enumerate(list(demos) + [query]):
        if not isinstance(item, dict) or "input" not in item or "output" not in item:
            reasons.append(f"pair {index} must contain input and output")
            continue
        errors = self_check(item["input"])
        if errors:
            reasons.append(f"pair {index} input is outside grammar: {errors[0]}")
            continue
        if rule_mirror(item["input"]) != item["output"]:
            reasons.append(f"pair {index} output does not match Manhattan Voronoi rule")
    if reasons:
        return sorted(set(reasons))
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(item["input"]) == item["output"] for item in demos):
            reasons.append(f"competitor {name} fits every demonstration")
    return sorted(set(reasons))
