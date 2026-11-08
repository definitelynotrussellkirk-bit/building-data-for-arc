"""Lesson generator for ARC task 64a8d13b4024: count colors into bars.

Count cells of colors 1, 2, and 3 in the input.  The output is a 6x3 grid
whose columns are bottom-aligned bars of those respective heights and colors.
The sampler exposes only pixel-observable controls and deliberately schedules redundant count-six witnesses so a five-row shortcut
cannot survive any query rotation of a three-demo lesson.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]

GENERATOR_ID = "64a8d13b4024"
TASK_ID = GENERATOR_ID
RULE_HASH = "e9d7e0db9b8a"
VERSION = "2.1.0"
SUMMARY = (
    "A sparse 8..14 by 8..14 grid contains 1..6 cells of each of colors "
    "1, 2, and 3. Count each color and draw a 6x3 bottom-aligned bar chart, "
    "one colored column per count."
)

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("count_six", "adjacent_pair", "border_scatter")
MIN_STRICT_FRAC = 1.0
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

INVARIANTS = [
    "the input is an 8..14 by 8..14 rectangular grid",
    "only colors 0, 1, 2, and 3 occur",
    "each counted color occurs between one and six times, including equal counts",
    "every four consecutive default samples include at least two count-six witnesses",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-weighted", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "difficulty-weighted", "valid": "8..14"},
    "n1": {"type": "int", "default": "scheduled/weighted", "valid": "1..6"},
    "n2": {"type": "int", "default": "scheduled/weighted", "valid": "1..6"},
    "n3": {"type": "int", "default": "scheduled/weighted", "valid": "1..6"},
}

_INT_AXES = {
    "grid_h": (8, 14),
    "grid_w": (8, 14),
    "n1": (1, 6),
    "n2": (1, 6),
    "n3": (1, 6),
}
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
    """Cycle exact semantic profiles; seed and band change pixels, not coverage."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _favorites(difficulty: Any) -> dict[str, tuple[int, ...]]:
    if difficulty == "easy":
        return {"grid_h": (8, 9, 10), "grid_w": (8, 9, 10), "count": (1, 2, 3)}
    if difficulty == "medium":
        return {"grid_h": (10, 11, 12, 13), "grid_w": (10, 11, 12, 13), "count": (2, 3, 4, 5)}
    if difficulty == "hard":
        return {"grid_h": (12, 13, 14), "grid_w": (12, 13, 14), "count": (4, 5, 6)}
    return {"grid_h": tuple(range(8, 15)), "grid_w": tuple(range(8, 15)), "count": tuple(range(1, 7))}


def _draw_int_axis(ctx, name: str, lo: int, hi: int, options: tuple[int, ...]) -> int:
    # Overrides are validated against the full advertised domain, independent of
    # the sampling band's weighted options.
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return int(ctx.draw_choice(name, options))


def _draw_counts(ctx, seed: int, sample_index: int, profile: str, difficulty: Any) -> tuple[int, int, int]:
    favored = _favorites(difficulty)["count"]
    count_names = ("n1", "n2", "n3")
    forced_name = None
    if profile in ("count_six", "adjacent_pair"):
        available = [name for name in count_names if ctx.overrides.get(name) is None]
        if available:
            forced_name = available[(seed + sample_index // LESSON_SCHEDULE_PERIOD) % len(available)]
    values = []
    for name in count_names:
        options = (6,) if name == forced_name else favored
        values.append(_draw_int_axis(ctx, name, 1, 6, options))
    return tuple(values)  # type: ignore[return-value]


def _random_available(rng, available: set[tuple[int, int]]) -> tuple[int, int]:
    return rng.choice(sorted(available))


def _place_counts(height: int, width: int, counts: tuple[int, int, int], profile: str, rng) -> Grid:
    grid = full_grid(height, width, 0)
    available = {(row, col) for row in range(height) for col in range(width)}
    placed: dict[int, list[tuple[int, int]]] = {1: [], 2: [], 3: []}

    if profile == "border_scatter":
        border = {
            (row, col)
            for row in range(height)
            for col in range(width)
            if row in (0, height - 1) or col in (0, width - 1)
        }
        for color in (1, 2, 3):
            cell = rng.choice(sorted(border & available))
            placed[color].append(cell)
            available.remove(cell)

    if profile == "adjacent_pair":
        candidate_colors = [color for color, count in zip((1, 2, 3), counts) if count >= 2]
        if candidate_colors:
            color = rng.choice(candidate_colors)
            pairs = []
            for row, col in sorted(available):
                for neighbor in ((row, col + 1), (row + 1, col)):
                    if neighbor in available:
                        pairs.append(((row, col), neighbor))
            first, second = rng.choice(pairs)
            placed[color].extend((first, second))
            available.remove(first)
            available.remove(second)

    for color, wanted in zip((1, 2, 3), counts):
        while len(placed[color]) < wanted:
            cell = _random_available(rng, available)
            placed[color].append(cell)
            available.remove(cell)
        for row, col in placed[color]:
            grid[row][col] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Build one deterministic lawful input; the Racket program remains authority."""
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
    favored = _favorites(difficulty)
    height = _draw_int_axis(ctx, "grid_h", 8, 14, favored["grid_h"])
    width = _draw_int_axis(ctx, "grid_w", 8, 14, favored["grid_w"])
    counts = _draw_counts(ctx, seed, sample_index, profile, difficulty)
    return _place_counts(height, width, counts, profile, ctx.draw_rng("placements"))


def _analyze(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None, ["expected a rectangular grid"]
    if any(type(value) is not int or value not in (0, 1, 2, 3) for row in grid for value in row):
        return None, ["cells must be literal integer colors in {0,1,2,3}"]

    height = len(grid)
    errors: list[str] = []
    if not 8 <= height <= 14:
        errors.append(f"grid height {height} outside [8, 14]")
    if not 8 <= width <= 14:
        errors.append(f"grid width {width} outside [8, 14]")
    counts = tuple(sum(value == color for row in grid for value in row) for color in (1, 2, 3))
    for color, count in zip((1, 2, 3), counts):
        if not 1 <= count <= 6:
            errors.append(f"color {color} count {count} outside [1, 6]")
    return {"grid_h": height, "grid_w": width, "counts": counts}, errors


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
    n1, n2, n3 = info["counts"]
    return {
        "grid_h": info["grid_h"],
        "grid_w": info["grid_w"],
        "n1": n1,
        "n2": n2,
        "n3": n3,
    }


def rule_mirror(grid) -> Grid:
    """Independent-size Python mirror of the canonical six-row bar rule."""
    info, errors = _analyze(grid)
    if info is None or errors:
        raise ValueError("cannot apply rule to invalid grid: " + "; ".join(errors))
    counts = info["counts"]
    return [
        [color if row >= 6 - counts[color - 1] else 0 for color in (1, 2, 3)]
        for row in range(6)
    ]


def _cap_bars_at_five(grid) -> Grid:
    info, errors = _analyze(grid)
    if info is None or errors:
        raise ValueError("cannot apply rival to invalid grid: " + "; ".join(errors))
    counts = tuple(min(5, count) for count in info["counts"])
    return [
        [color if row >= 6 - counts[color - 1] else 0 for color in (1, 2, 3)]
        for row in range(6)
    ]


def _has_count_six(grid) -> bool:
    info, errors = _analyze(grid)
    return bool(info is not None and not errors and 6 in info["counts"])


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "count_reaches_six": _has_count_six,
}
SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "cap_bars_at_five": _cap_bars_at_five,
}
WITNESS_RIVALS = {"count_reaches_six": ["cap_bars_at_five"]}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def semantic_observables(grid) -> dict[str, Any]:
    info, errors = _analyze(grid)
    if info is None:
        return {"errors": errors}
    return {
        "errors": errors,
        **(observe_overrides(grid) if not errors else {}),
        "count_reaches_six": not errors and 6 in info["counts"],
    }


def lesson_identifiable(demos, query) -> list[str]:
    """Reject malformed labels or any named rival that survives all demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]
    reasons: list[str] = []
    pairs = list(demos) + [query]
    for index, item in enumerate(pairs):
        if not isinstance(item, dict) or "input" not in item or "output" not in item:
            reasons.append(f"pair {index} must contain input and output")
            continue
        errors = self_check(item["input"])
        if errors:
            reasons.append(f"pair {index} input is outside grammar: {errors[0]}")
            continue
        if rule_mirror(item["input"]) != item["output"]:
            reasons.append(f"pair {index} output does not match color-count bars")
    if reasons:
        return sorted(set(reasons))
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(item["input"]) == item["output"] for item in demos):
            reasons.append(f"competitor {name} fits every demonstration")
    return sorted(set(reasons))
