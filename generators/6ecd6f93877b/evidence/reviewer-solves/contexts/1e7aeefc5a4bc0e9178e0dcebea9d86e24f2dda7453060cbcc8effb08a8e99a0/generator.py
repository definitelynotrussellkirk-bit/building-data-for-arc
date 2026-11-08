"""Honest input sampler for ARC task 6ecd6f93877b (Sorted Count Strip).

The unchanged Racket authority counts every non-zero color, sorts colors by
numeric value, and emits one output cell per input occurrence.  This sampler
keeps a canonical-density anchor while deliberately generating two cases the
five labeled pairs do not cover: a count above three and an output longer than
six cells.  Those cases rule out the strongest canonical-fitting shortcuts.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6ecd6f93877b"
TASK_ID = GENERATOR_ID
RULE_HASH = "66d1273fdbac"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3
SUMMARY = (
    "A 5..10 by 5..10 zero-background grid contains 2..5 scattered non-zero "
    "colors, each occurring 1..4 times. Count every occurrence, sort colors "
    "numerically, and emit a one-row strip containing each color repeated by "
    "its count; an all-zero input would map to [[0]]."
)

INVARIANTS = [
    "zero is background and at least one background cell remains",
    "2..5 distinct non-zero integer colors from 1..9",
    "every non-zero color occurs 1..4 times",
    "positions are irrelevant; multiplicity and numeric color order determine the output",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled within 5..10", "valid": "5..10"},
    "grid_w": {"type": "int", "default": "scheduled within 5..10", "valid": "5..10"},
    "n_colors": {"type": "int", "default": "scheduled within 2..5", "valid": "2..5"},
    "max_count": {"type": "int", "default": "scheduled within 1..4", "valid": "1..4"},
}
# Every Cartesian combination is constructive: at most 5*4=20 occupied cells,
# while the smallest declared canvas has 25 cells.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = ("canonical_anchor", "shortcut_witness")
_CANONICAL_SHAPES = ((6, 6), (7, 7), (6, 8), (5, 9), (7, 8))
_CANONICAL_COUNTS = ((2, 1, 2), (1, 3, 1), (2, 2, 2), (1, 1, 3), (2, 2, 2))
_DIFFICULTY_OPTIONS = {
    None: {
        "grid_h": tuple(range(5, 11)),
        "grid_w": tuple(range(5, 11)),
        "n_colors": (2, 3, 4, 5),
    },
    "easy": {
        "grid_h": (5, 6, 7),
        "grid_w": (5, 6, 7),
        "n_colors": (2, 3),
    },
    "medium": {
        "grid_h": (6, 7, 8, 9),
        "grid_w": (6, 7, 8, 9),
        "n_colors": (3, 4),
    },
    "hard": {
        "grid_h": (8, 9, 10),
        "grid_w": (8, 9, 10),
        "n_colors": (4, 5),
    },
}


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Alternate anchors and broad counterexamples in every four-pair window."""
    del seed, difficulty
    return "canonical_anchor" if sample_index % 2 == 0 else "shortcut_witness"


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    if difficulty not in _DIFFICULTY_OPTIONS:
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'; "
            f"got {difficulty!r}"
        )
    bounds = {
        "grid_h": (5, 10),
        "grid_w": (5, 10),
        "n_colors": (2, 5),
        "max_count": (1, 4),
    }
    for name, value in overrides.items():
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _draw_axis(ctx: Any, name: str, lo: int, hi: int, default: int | tuple[int, ...]) -> int:
    """Draw one exact observable integer axis without narrowing override support."""
    if name in ctx.overrides:
        return ctx.draw_int_strict(name, lo, hi)
    choices = (default,) if type(default) is int else tuple(default)
    return int(ctx.draw_choice(name, choices))


def _scheduled_axes(ctx: Any, sample_index: int, difficulty: Any, profile: str) -> tuple[int, int, int, int]:
    options = _DIFFICULTY_OPTIONS[difficulty]
    if profile == "canonical_anchor":
        anchor = (sample_index // 2) % len(_CANONICAL_SHAPES)
        scheduled_h, scheduled_w = _CANONICAL_SHAPES[anchor]
        scheduled_n = 3
        scheduled_max = max(_CANONICAL_COUNTS[anchor])
    else:
        scheduled_h = options["grid_h"]
        # Keep the canonical output-shape relation: broad outputs contain
        # 7..10 cells, so the default broad canvas is ten columns wide.
        scheduled_w = 10
        scheduled_n = options["n_colors"]
        scheduled_max = 4

    height = _draw_axis(ctx, "grid_h", 5, 10, scheduled_h)
    width = _draw_axis(ctx, "grid_w", 5, 10, scheduled_w)
    n_colors = _draw_axis(ctx, "n_colors", 2, 5, scheduled_n)
    max_count = _draw_axis(ctx, "max_count", 1, 4, scheduled_max)
    return height, width, n_colors, max_count


def _draw_counts(
    ctx: Any,
    sample_index: int,
    profile: str,
    n_colors: int,
    max_count: int,
) -> list[int]:
    count_overridden = "n_colors" in ctx.overrides or "max_count" in ctx.overrides
    if profile == "canonical_anchor" and not count_overridden:
        return list(_CANONICAL_COUNTS[(sample_index // 2) % len(_CANONICAL_COUNTS)])

    rng = ctx.draw_rng("color_counts")
    if profile == "shortcut_witness" and max_count == 4:
        # Totals are 7, 8, 9, or 10 for 2..5 colors. This refutes both
        # canonical-fitting rivals while retaining the canonical shrink relation
        # on the scheduled ten-column broad canvas.
        counts = [4, 3] + [1] * (n_colors - 2)
    else:
        counts = [max_count]
        if n_colors >= 2:
            counts.append(rng.randint(1, max_count))
        counts.extend(
            rng.randint(1, max_count) for _ in range(n_colors - len(counts))
        )
    rng.shuffle(counts)
    return counts


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any) -> list[list[int]]:
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    # Record the schedule branch in deterministic draw provenance without
    # advertising it as an independently overridable axis.
    ctx.draw_choice("curriculum_profile", (profile,))
    height, width, n_colors, max_count = _scheduled_axes(
        ctx, sample_index, difficulty, profile
    )
    counts = _draw_counts(ctx, sample_index, profile, n_colors, max_count)

    palette = ctx.draw_rng("palette").sample(range(1, 10), n_colors)
    assignments = list(zip(palette, counts))
    ctx.draw_rng("count_to_color_assignment").shuffle(assignments)

    cells = [(row, col) for row in range(height) for col in range(width)]
    chosen = ctx.draw_rng("positions").sample(cells, sum(counts))
    grid = full_grid(height, width, 0)
    cursor = 0
    for color, count in assignments:
        for row, col in chosen[cursor : cursor + count]:
            grid[row][col] = color
        cursor += count
    return grid


def _analyze_grid(grid: Any) -> tuple[list[str], Counter[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"], Counter()
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"], Counter()
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["expected a rectangular grid; found a ragged row"], Counter()

    height = len(grid)
    errors: list[str] = []
    if not 5 <= height <= 10:
        errors.append(f"grid height {height} outside 5..10")
    if not 5 <= width <= 10:
        errors.append(f"grid width {width} outside 5..10")

    bad_cells = [
        value
        for row in grid
        for value in row
        if type(value) is not int or not 0 <= value <= 9
    ]
    if bad_cells:
        errors.append("cells must be integer ARC colors 0..9 (bool is not a color)")
        return errors, Counter()

    flat = [value for row in grid for value in row]
    if 0 not in flat:
        errors.append("expected at least one zero-background cell")
    counts = Counter(value for value in flat if value != 0)
    if not 2 <= len(counts) <= 5:
        errors.append(f"expected 2..5 distinct non-zero colors, found {len(counts)}")
    for color, count in sorted(counts.items()):
        if not 1 <= count <= 4:
            errors.append(f"color {color} count {count} outside 1..4")
    return errors, counts


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Validate the complete declared input manifold without consulting labels."""
    del difficulty, meta
    errors, _ = _analyze_grid(grid)
    return errors


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every advertised exact axis from returned pixels."""
    errors, counts = _analyze_grid(grid)
    if errors:
        raise ValueError(f"cannot observe axes from invalid grid: {errors[0]}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_colors": len(counts),
        "max_count": max(counts.values()),
    }


def strict_canonical_like(grid: Any) -> list[str]:
    """Recognize the labeled task's shape, color-count, and density manifold."""
    errors, counts = _analyze_grid(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    reasons: list[str] = []
    if not 5 <= height <= 7:
        reasons.append(f"canonical height must be 5..7, found {height}")
    if not 6 <= width <= 9:
        reasons.append(f"canonical width must be 6..9, found {width}")
    if len(counts) != 3:
        reasons.append(f"canonical inputs use exactly 3 colors, found {len(counts)}")
    total = sum(counts.values())
    if not 5 <= total <= 6:
        reasons.append(f"canonical non-zero total must be 5..6, found {total}")
    if counts and max(counts.values()) > 3:
        reasons.append("canonical per-color counts do not exceed 3")
    return reasons


def _color_counts(grid: Any) -> Counter[int]:
    return Counter(value for row in grid for value in row if value != 0)


def rule_mirror(grid: Any) -> list[list[int]]:
    """Independent Python mirror of the pinned Racket authority."""
    counts = _color_counts(grid)
    row = [color for color in sorted(counts) for _ in range(counts[color])]
    return [row or [0]]


def _clip_counts_at_three(grid: Any) -> list[list[int]]:
    counts = _color_counts(grid)
    row = [
        color
        for color in sorted(counts)
        for _ in range(min(counts[color], 3))
    ]
    return [row or [0]]


def _truncate_to_six(grid: Any) -> list[list[int]]:
    return [rule_mirror(grid)[0][:6]]


def _count_above_three(grid: Any) -> bool:
    errors, counts = _analyze_grid(grid)
    return not errors and any(count > 3 for count in counts.values())


def _output_longer_than_six(grid: Any) -> bool:
    errors, counts = _analyze_grid(grid)
    return not errors and sum(counts.values()) > 6


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "count_above_three": _count_above_three,
    "output_longer_than_six": _output_longer_than_six,
}
SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "clip_counts_at_three": _clip_counts_at_three,
    "truncate_to_six": _truncate_to_six,
}
WITNESS_RIVALS = {
    "count_above_three": ["clip_counts_at_three"],
    "output_longer_than_six": ["truncate_to_six"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Report only rivals that fit every demonstration and alter the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output does not match the canonical rule")

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output does not match the canonical rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        fits_demos = all(
            rival(pair["input"]) == pair["output"] for pair in demos
        )
        changes_query = rival(query["input"]) != query["output"]
        if fits_demos and changes_query:
            reasons.append(f"competitor {name!r} fits every demo but changes query")
    return reasons
