"""Generator for f2818d6c50ce — sorted bars of exact-pair span lengths.

The selected canonical rule groups non-background cells by color, keeps only
colors occurring exactly twice, measures each pair by Chebyshev span + 1, sorts
those lengths, and emits one left-aligned color-8 bar per length.

This sampler deliberately includes lawful non-pair colors (singletons and
3-cell groups). They are ignored by the selected rule and refute the tempting
canonical-only shortcut "every foreground color is a segment". A three-profile
schedule guarantees that every three consecutive examples contains both a
canonical-like clean scene and shortcut-refuting scenes.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
from itertools import combinations
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f2818d6c50ce"
TASK_ID = "f2818d6c50ce"
RULE_HASH = "216362042c61"
VERSION = "3.0.0"

SUMMARY = (
    "Colors occurring exactly twice define aligned segments. Measure each "
    "segment's Chebyshev span plus one, sort the lengths, and draw left-aligned "
    "color-8 bars. Scheduled singleton and 3-cell distractor colors teach that "
    "only exact pairs contribute rows."
)

INVARIANTS = [
    "background is 0 and input never uses output color 8",
    "between 1 and 6 colors occur exactly twice",
    "every exact pair is horizontal, vertical, or diagonal",
    "0 to 2 additional colors occur once or at least three times",
    "the selected rule ignores all non-pair colors",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled draw", "valid": "8..22"},
    "grid_w": {"type": "int", "default": "scheduled draw", "valid": "8..22"},
    "n_pairs": {"type": "int", "default": "scheduled draw", "valid": "1..6"},
    "n_distractor_colors": {
        "type": "int",
        "default": "sample_index mod 3",
        "valid": "0..2",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25
SCHEDULE_PROFILES = ("canonical", "singleton_distractor", "mixed_distractors")

_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))
_CANONICAL_SHAPE_PALETTES = frozenset({(10, 10, 4), (11, 11, 4), (10, 12, 4)})
_CANONICAL_SHAPES = ((10, 10), (11, 11), (10, 12))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Name the deterministic teaching branch for schedule-coverage audits."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_request(difficulty, overrides: dict) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")


def _has_override(overrides: dict, name: str) -> bool:
    return name in overrides and overrides[name] is not None


def _draw_axis(ctx, overrides: dict, name: str, domain: tuple[int, ...], *,
               forced: int | None = None, bias: tuple[int, ...] = ()) -> int:
    """Draw an exact public axis while preserving its full override domain.

    Scheduled profiles may force a default value, but an explicit override is
    always validated against the complete declared domain.
    """
    if forced is not None and not _has_override(overrides, name):
        options = (forced,)
    else:
        options = domain + bias
    return ctx.draw_choice(name, options)


def _difficulty_bias(difficulty, *, axis: str) -> tuple[int, ...]:
    if axis in {"grid_h", "grid_w"}:
        return {
            "easy": (8, 9, 10, 11, 12) * 2,
            "hard": (17, 18, 19, 20, 21, 22) * 2,
        }.get(difficulty, (11, 12, 13, 14, 15, 16, 17))
    if axis == "n_pairs":
        return {
            "easy": (1, 2, 3),
            "hard": (4, 5, 6),
        }.get(difficulty, (2, 3, 4, 5))
    return ()


@lru_cache(maxsize=15 * 15 * 21)
def _pair_candidates(h: int, w: int, length: int) -> tuple[tuple[tuple[int, int], tuple[int, int]], ...]:
    """All aligned endpoint pairs with the requested Chebyshev span length."""
    distance = length - 1
    candidates = []
    for dr, dc in _DIRECTIONS:
        for row in range(h):
            for col in range(w):
                row2 = row + distance * dr
                col2 = col + distance * dc
                if 0 <= row2 < h and 0 <= col2 < w:
                    candidates.append(((row, col), (row2, col2)))
    return tuple(candidates)


def _span_plan(h: int, w: int, count: int, profile: str, rng) -> list[int]:
    available = list(range(2, max(h, w) + 1))
    if profile == "canonical" and count == 3:
        feasible = [
            plan
            for plan in ((3, 6, 7), (3, 5, 6), (5, 6, 6))
            if max(plan) <= max(h, w)
        ]
        return list(rng.choice(feasible))

    if profile == "mixed_distractors" and count >= 3:
        # A tie is informative only when another, different bar supplies scale.
        # With exactly two equal spans the selected rule emits a solid rectangle,
        # which is lawful but poor training data and trips the defect gate.
        tie = rng.choice(available)
        remaining = [value for value in available if value != tie]
        rng.shuffle(remaining)
        return [tie, tie] + remaining[: count - 2]

    rng.shuffle(available)
    return available[:count]


def _choose_endpoint_pairs(h: int, w: int, lengths: list[int], rng):
    """Construct non-overlapping endpoints with deterministic backtracking."""
    candidate_lists = []
    for index, length in enumerate(lengths):
        candidates = list(_pair_candidates(h, w, length))
        rng.shuffle(candidates)
        if not candidates:
            raise ValueError(f"no aligned endpoint pair fits span length {length}")
        candidate_lists.append((index, candidates))

    # Place constrained (long-span) lists first, but return in original order.
    candidate_lists.sort(key=lambda item: len(item[1]))
    chosen = [None] * len(lengths)

    def search(position: int, occupied: set[tuple[int, int]]) -> bool:
        if position == len(candidate_lists):
            return True
        original_index, candidates = candidate_lists[position]
        for first, second in candidates:
            if first in occupied or second in occupied:
                continue
            chosen[original_index] = (first, second)
            occupied.add(first)
            occupied.add(second)
            if search(position + 1, occupied):
                return True
            occupied.remove(first)
            occupied.remove(second)
            chosen[original_index] = None
        return False

    if not search(0, set()):
        raise RuntimeError(
            f"constructive pair placement failed for {h}x{w} spans {lengths}"
        )
    return chosen


def _build(ctx, h: int, w: int, n_pairs: int, n_distractors: int, profile: str):
    grid = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    colors = rng.sample(list(_COLORS), n_pairs + n_distractors)
    pair_colors = colors[:n_pairs]
    distractor_colors = colors[n_pairs:]

    lengths = _span_plan(h, w, n_pairs, profile, ctx.draw_rng("span_plan"))
    endpoints = _choose_endpoint_pairs(h, w, lengths, ctx.draw_rng("pair_positions"))
    occupied: set[tuple[int, int]] = set()
    for color, (first, second) in zip(pair_colors, endpoints):
        for row, col in (first, second):
            grid[row][col] = color
            occupied.add((row, col))

    remaining = [
        (row, col)
        for row in range(h)
        for col in range(w)
        if (row, col) not in occupied
    ]
    rng.shuffle(remaining)
    cursor = 0
    if n_distractors == 1:
        multiplicities = [1 if profile == "singleton_distractor" else 3]
    elif n_distractors == 2:
        multiplicities = [1, 3]
    else:
        multiplicities = []
    for color, multiplicity in zip(distractor_colors, multiplicities):
        for row, col in remaining[cursor: cursor + multiplicity]:
            grid[row][col] = color
        cursor += multiplicity
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)

    if profile == "canonical":
        target_h, target_w = ctx.draw_rng("canonical_shape").choice(_CANONICAL_SHAPES)
        h = _draw_axis(
            ctx, overrides, "grid_h", tuple(range(8, 23)), forced=target_h
        )
        w = _draw_axis(
            ctx, overrides, "grid_w", tuple(range(8, 23)), forced=target_w
        )
        n_pairs = _draw_axis(
            ctx, overrides, "n_pairs", tuple(range(1, 7)), forced=3
        )
        n_distractors = _draw_axis(
            ctx,
            overrides,
            "n_distractor_colors",
            (0, 1, 2),
            forced=0,
        )
    else:
        h = _draw_axis(
            ctx,
            overrides,
            "grid_h",
            tuple(range(8, 23)),
            bias=_difficulty_bias(difficulty, axis="grid_h"),
        )
        w = _draw_axis(
            ctx,
            overrides,
            "grid_w",
            tuple(range(8, 23)),
            bias=_difficulty_bias(difficulty, axis="grid_w"),
        )
        n_pairs = _draw_axis(
            ctx,
            overrides,
            "n_pairs",
            tuple(range(1, 7)),
            bias=_difficulty_bias(difficulty, axis="n_pairs"),
        )
        forced_distractors = 1 if profile == "singleton_distractor" else 2
        n_distractors = _draw_axis(
            ctx,
            overrides,
            "n_distractor_colors",
            (0, 1, 2),
            forced=forced_distractors,
        )

    return _build(ctx, h, w, n_pairs, n_distractors, profile)


def _color_points(grid) -> dict[int, list[tuple[int, int]]]:
    points: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                points.setdefault(value, []).append((row, col))
    return points


def _span_length(points: list[tuple[int, int]]) -> int:
    if len(points) == 1:
        return 1
    return max(
        max(abs(first[0] - second[0]), abs(first[1] - second[1])) + 1
        for first, second in combinations(points, 2)
    )


def _bars(lengths: list[int]) -> list[list[int]]:
    if not lengths:
        raise ValueError("the selected rule requires at least one exact pair")
    ordered = sorted(lengths)
    width = max(ordered)
    return [[8] * length + [0] * (width - length) for length in ordered]


def _expected_output(grid) -> list[list[int]]:
    """Python mirror used only for tests and semantic competitors."""
    return _bars(
        [_span_length(cells) for cells in _color_points(grid).values() if len(cells) == 2]
    )


def _all_nonzero_colors_are_pairs(grid) -> list[list[int]]:
    """Wrong canonical-only shortcut: emit a bar for every foreground color."""
    return _bars([_span_length(cells) for cells in _color_points(grid).values()])


def observe_overrides(grid) -> dict[str, int | None]:
    """Recover every exact public axis from returned pixels."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return {name: None for name in AXES}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {name: None for name in AXES}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {name: None for name in AXES}
    counts = Counter(value for row in grid for value in row if value != 0)
    return {
        "grid_h": len(grid),
        "grid_w": width,
        "n_pairs": sum(count == 2 for count in counts.values()),
        "n_distractor_colors": sum(count != 2 for count in counts.values()),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]

    errors = []
    height = len(grid)
    if not 8 <= height <= 22:
        errors.append(f"grid_h={height} outside [8,22]")
    if not 8 <= width <= 22:
        errors.append(f"grid_w={width} outside [8,22]")
    illegal = [
        value
        for row in grid
        for value in row
        if type(value) is not int or not 0 <= value <= 9
    ]
    if illegal:
        return errors + ["cells must be integer ARC colors 0..9"]

    points = _color_points(grid)
    if not points:
        return errors + ["no foreground colors"]
    if 8 in points:
        errors.append("input uses output color 8")
    if len(points) > len(_COLORS):
        errors.append("too many non-background colors")

    pair_count = 0
    distractor_count = 0
    for color, cells in sorted(points.items()):
        if len(cells) == 2:
            pair_count += 1
            (row1, col1), (row2, col2) = cells
            if not (
                row1 == row2
                or col1 == col2
                or abs(row1 - row2) == abs(col1 - col2)
            ):
                errors.append(
                    f"color {color} endpoints are not horizontal/vertical/diagonal aligned"
                )
        else:
            distractor_count += 1

    if not 1 <= pair_count <= 6:
        errors.append(f"n_pairs={pair_count} outside [1,6]")
    if not 0 <= distractor_count <= 2:
        errors.append(f"n_distractor_colors={distractor_count} outside [0,2]")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept lawful inputs matching one of the three public input profiles."""
    errors = self_check(grid)
    if errors:
        return errors
    profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
    if profile not in _CANONICAL_SHAPE_PALETTES:
        return [
            f"canonical shape/palette must be one of {sorted(_CANONICAL_SHAPE_PALETTES)}, "
            f"found {profile}"
        ]
    observed = observe_overrides(grid)
    if observed["n_pairs"] != 3 or observed["n_distractor_colors"] != 0:
        return ["canonical inputs contain exactly three pair colors and no distractors"]
    return []


def _ignore_nonpairs_witness(grid) -> bool:
    try:
        return (
            observe_overrides(grid)["n_distractor_colors"] > 0
            and _all_nonzero_colors_are_pairs(grid) != _expected_output(grid)
        )
    except Exception:
        return False


SEMANTIC_RIVALS: dict[str, Callable] = {
    "all_nonzero_colors_are_pairs": _all_nonzero_colors_are_pairs,
}
SEMANTIC_WITNESSES = {"ignore_nonpairs": _ignore_nonpairs_witness}
WITNESS_RIVALS = {
    "ignore_nonpairs": ["all_nonzero_colors_are_pairs"],
}
CANONICAL_SHORTCUTS = {
    "all_nonzero_colors_are_pairs": _all_nonzero_colors_are_pairs,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """A lesson is identifiable once every declared wrong rule loses a demo."""
    del query
    reasons = []
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(demo["input"]) == demo["output"] for demo in demos
            )
        except Exception as exc:
            reasons.append(f"{name} raised {type(exc).__name__}: {exc}")
            continue
        if survives:
            reasons.append(f"{name} fits every demonstration")
    return reasons
