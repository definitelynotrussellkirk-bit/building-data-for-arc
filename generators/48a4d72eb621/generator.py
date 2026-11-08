"""Generator for the Singleton Multiset Strip ARC task.

The authoritative Racket rule sorts all non-background colors and emits one
output cell per input occurrence. This module owns only lawful input sampling,
validation, semantic review hooks, and exact override observability.
"""
from __future__ import annotations

from collections import Counter
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]

GENERATOR_ID = "48a4d72eb621"
TASK_ID = GENERATOR_ID
RULE_HASH = "ea16ba808d09"
VERSION = "2.0.0"
SUMMARY = (
    "Sparse isolated markers in 2-5 colors; every color occurs 1-3 times. "
    "The reference rule emits the ascending color multiset as one row."
)

INVARIANTS = [
    "2..5 distinct non-background colors selected from 1..9",
    "each selected color occurs 1..3 times",
    "markers are orthogonally isolated on a 5..12 by 6..12 canvas",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile biased", "valid": "5..12"},
    "grid_w": {"type": "int", "default": "canonical-profile biased", "valid": "6..12"},
    "n_colors": {"type": "int", "default": "canonical-profile biased", "valid": "2..5"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_CANONICAL_PROFILES = (
    (7, 8, 3),
    (8, 9, 3),
    (6, 10, 3),
    (9, 7, 2),
    (8, 8, 3),
)
_BROAD_PROFILES = (
    (5, 6, 2),
    (10, 11, 4),
    (12, 12, 5),
    (5, 12, 5),
    (12, 6, 4),
)


def _validate_call(seed, sample_index, difficulty) -> None:
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_overrides(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axes: {unknown}")
    bounds = {"grid_h": (5, 12), "grid_w": (6, 12), "n_colors": (2, 5)}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer, not {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")


def _axis_choices(anchor: int, lo: int, hi: int) -> tuple[int, ...]:
    """Bias defaults toward one coherent profile while retaining full support."""
    return (anchor,) * 16 + tuple(range(lo, hi + 1))


def _branch_flags(sample_index: int) -> tuple[bool, bool]:
    """Return (include_color_five, include_a_triple_count).

    Each flag is true in three of every four consecutive sample indices. Thus,
    after any one of four lesson pairs is held out as query, at least two
    demonstrations still refute the corresponding shortcut.
    """
    branch = sample_index % 4
    return branch != 3, branch != 2


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty)
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Most draws land on an exact canonical (height, width, color-count)
    # profile. Every declared boundary remains directly selectable.
    profile_pools = {
        None: _CANONICAL_PROFILES * 4 + _BROAD_PROFILES * 2,
        "easy": _CANONICAL_PROFILES * 6 + _BROAD_PROFILES,
        "medium": _CANONICAL_PROFILES * 4 + _BROAD_PROFILES * 2,
        "hard": _CANONICAL_PROFILES * 2 + _BROAD_PROFILES * 4,
    }
    profiles = profile_pools[difficulty]
    profile = ctx.draw_choice("curriculum_profile", profiles)
    h = ctx.draw_choice("grid_h", _axis_choices(profile[0], 5, 12))
    w = ctx.draw_choice("grid_w", _axis_choices(profile[1], 6, 12))
    n_colors = ctx.draw_choice("n_colors", _axis_choices(profile[2], 2, 5))

    include_five, include_triple = _branch_flags(sample_index)
    palette_rng = ctx.draw_rng("palette")
    other_colors = [color for color in range(1, 10) if color != 5]
    if include_five:
        palette = [5, *palette_rng.sample(other_colors, n_colors - 1)]
    else:
        palette = palette_rng.sample(other_colors, n_colors)
    palette_rng.shuffle(palette)

    count_rng = ctx.draw_rng("counts")
    upper = 3 if include_triple else 2
    if difficulty == "easy":
        counts = {color: 1 for color in palette}
    elif difficulty == "hard":
        counts = {color: upper for color in palette}
    else:
        counts = {color: count_rng.randint(1, upper) for color in palette}
    required_color = palette[sample_index % len(palette)]
    counts[required_color] = 3 if include_triple else 2

    cells_needed = sum(counts.values())
    parity_rng = ctx.draw_rng("placement_parity")
    parities = [0, 1]
    parity_rng.shuffle(parities)
    candidates: list[tuple[int, int]] | None = None
    for parity in parities:
        trial = [(r, c) for r in range(h) for c in range(w) if (r + c) % 2 == parity]
        if len(trial) >= cells_needed:
            candidates = trial
            break
    if candidates is None:  # defensive: the declared bounds make this unreachable
        raise RuntimeError("canvas cannot fit the requested isolated markers")

    placement_rng = ctx.draw_rng("placement")
    positions = sorted(placement_rng.sample(candidates, cells_needed))
    values = [color for color, count in counts.items() for _ in range(count)]
    placement_rng.shuffle(values)
    if values == sorted(values):
        values[0], values[-1] = values[-1], values[0]

    grid = full_grid(h, w, 0)
    for (r, c), value in zip(positions, values):
        grid[r][c] = value
    return grid


def observe_overrides(grid) -> dict[str, int]:
    colors = {value for row in grid for value in row if value != 0}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_colors": len(colors),
    }


def _marker_counts(grid: Grid) -> Counter[int]:
    return Counter(value for row in grid for value in row if value != 0)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a nonempty row list"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not (5 <= len(grid) <= 12 and 6 <= width <= 12):
        errors.append("grid dimensions must be within 5..12 rows and 6..12 columns")

    counts: Counter[int] = Counter()
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                errors.append("grid cells must be integer ARC colors 0..9")
                return errors
            if value != 0:
                counts[value] += 1

    if not (2 <= len(counts) <= 5):
        errors.append("expected two to five distinct marker colors")
    for color, count in sorted(counts.items()):
        if not 1 <= count <= 3:
            errors.append(f"color {color} should occur one to three times")

    # Marker cells are singleton tokens; diagonal contact is harmless, but an
    # orthogonal run would introduce object-shape structure absent canonically.
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                continue
            if r + 1 < len(grid) and grid[r + 1][c] != 0:
                errors.append("marker cells must be orthogonally isolated")
                return errors
            if c + 1 < width and row[c + 1] != 0:
                errors.append("marker cells must be orthogonally isolated")
                return errors
    return errors


def strict_canonical_like(grid: Grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    counts = _marker_counts(grid)
    if not 6 <= len(grid) <= 9:
        reasons.append("canonical rows are 6..9")
    if not 7 <= len(grid[0]) <= 10:
        reasons.append("canonical columns are 7..10")
    if not 2 <= len(counts) <= 3:
        reasons.append("canonical inputs use two or three colors")
    return reasons


MIN_STRICT_FRAC = 0.15
EXAMPLES_NEEDED = 3


def _ascending_multiset(grid: Grid, *, cap: int | None = None, drop_five: bool = False) -> Grid:
    counts = _marker_counts(grid)
    row: list[int] = []
    for color in sorted(counts):
        if drop_five and color == 5:
            continue
        count = counts[color] if cap is None else min(counts[color], cap)
        row.extend([color] * count)
    return [row or [0]]


def rival_cap_two(grid: Grid) -> Grid:
    return _ascending_multiset(grid, cap=2)


def rival_drop_five(grid: Grid) -> Grid:
    return _ascending_multiset(grid, drop_five=True)


def rival_distinct_only(grid: Grid) -> Grid:
    row = sorted(_marker_counts(grid))
    return [row or [0]]


def rival_row_major(grid: Grid) -> Grid:
    row = [value for input_row in grid for value in input_row if value != 0]
    return [row or [0]]


def _has_count_three(grid: Grid) -> bool:
    return 3 in _marker_counts(grid).values()


def _has_color_five(grid: Grid) -> bool:
    return 5 in _marker_counts(grid)


def _has_duplicate_count(grid: Grid) -> bool:
    return any(count >= 2 for count in _marker_counts(grid).values())


def _sorting_matters(grid: Grid) -> bool:
    row = [value for input_row in grid for value in input_row if value != 0]
    return row != sorted(row)


def _has_two_colors(grid: Grid) -> bool:
    return len(_marker_counts(grid)) == 2


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "cap_two": rival_cap_two,
    "drop_five": rival_drop_five,
    "distinct_only": rival_distinct_only,
    "row_major": rival_row_major,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "count_three": _has_count_three,
    "color_five": _has_color_five,
    "duplicate_count": _has_duplicate_count,
    "sorting_matters": _sorting_matters,
    "two_color_case": _has_two_colors,
}
WITNESS_RIVALS = {
    "count_three": ["cap_two"],
    "color_five": ["drop_five"],
    "duplicate_count": ["distinct_only"],
    "sorting_matters": ["row_major"],
}
BRANCH_WITNESSES = ("two_color_case",)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
