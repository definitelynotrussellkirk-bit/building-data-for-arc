"""Generator for task 8ab614412470: erase globally unique colors.

The input is a zero-background grid.  Every nonzero color is counted over the
whole grid: colors occurring once are erased; colors occurring at least twice
remain unchanged.  The curriculum deliberately includes non-local pairs and
multiple singleton colors so local-connectivity and one-off-erasure shortcuts
are contradicted by every generated instance.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8ab614412470"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "f20d2d2ae760"
SUMMARY = "Erase every globally unique nonzero color; retain repeated colors."

INVARIANTS = [
    "zero is the background color",
    "two to five nonzero colors repeat globally",
    "two to four other nonzero colors are singletons",
    "at least one repeated color occurs exactly twice at nonadjacent cells",
]

REPEAT_PATTERNS = ("pairs", "mixed", "heavy")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 5..9", "valid": "5..9"},
    "grid_w": {"type": "int", "default": "scheduled 5..9", "valid": "5..9"},
    "n_repeated_colors": {
        "type": "int",
        "default": "scheduled 2..5",
        "valid": "2..5",
    },
    "n_singleton_colors": {
        "type": "int",
        "default": "scheduled 2..4",
        "valid": "2..4",
    },
    "repeat_pattern": {
        "type": "str",
        "default": "scheduled pairs|mixed|heavy",
        "valid": "pairs|mixed|heavy",
    },
}

SCHEDULE_PROFILES = (
    "canonical_5x7",
    "canonical_5x8",
    "canonical_6x6",
    "broad",
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0


# ---------------------------------------------------------------------------
# Generation and schedule
# ---------------------------------------------------------------------------


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis: {', '.join(unknown)}")


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Return the deterministic four-slot curriculum branch.

    Seed and difficulty intentionally do not change the branch: each consecutive
    four-instance window gets all three canonical anchors plus one broad draw.
    """
    _validate_call(difficulty, {})
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _scheduled_defaults(sample_index: int) -> dict[str, Any]:
    profile = SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]
    if profile == "canonical_5x7":
        return {
            "grid_h": 5,
            "grid_w": 7,
            "n_repeated_colors": 3,
            "n_singleton_colors": 2,
            "repeat_pattern": "pairs",
        }
    if profile == "canonical_5x8":
        return {
            "grid_h": 5,
            "grid_w": 8,
            "n_repeated_colors": 3,
            "n_singleton_colors": 2,
            "repeat_pattern": "mixed",
        }
    if profile == "canonical_6x6":
        return {
            "grid_h": 6,
            "grid_w": 6,
            "n_repeated_colors": 3,
            "n_singleton_colors": 3,
            "repeat_pattern": "heavy",
        }

    # The broad slot cycles through the full declared domains.  It is scheduled
    # rather than sampled so every short run gets reproducible boundary support.
    cycle = sample_index // len(SCHEDULE_PROFILES)
    return {
        "grid_h": 5 + (cycle % 5),
        "grid_w": 5 + ((2 * cycle + 1) % 5),
        "n_repeated_colors": 2 + (cycle % 4),
        "n_singleton_colors": 2 + (cycle % 3),
        "repeat_pattern": REPEAT_PATTERNS[cycle % len(REPEAT_PATTERNS)],
    }


def _draw_scheduled_int(ctx, label: str, lo: int, hi: int, default: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    # A singleton choice records the branch value for provenance without
    # pretending that the schedule made a fresh uniform draw.
    return ctx.draw_choice(label, (default,))


def _draw_scheduled_choice(ctx, label: str, options: tuple[str, ...], default: str) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        value = ctx.overrides[label]
        if type(value) is not str:
            raise TypeError(f"{label} override must be a string")
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _multiplicities(n_repeated: int, pattern: str) -> list[int]:
    if pattern == "pairs":
        return [2] * n_repeated
    if pattern == "mixed":
        return [2] + [3] * (n_repeated - 1)
    if pattern == "heavy":
        return [2] + [4] * (n_repeated - 1)
    raise ValueError(f"unsupported repeat_pattern: {pattern!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer")

    defaults = _scheduled_defaults(sample_index)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_scheduled_int(ctx, "grid_h", 5, 9, defaults["grid_h"])
    w = _draw_scheduled_int(ctx, "grid_w", 5, 9, defaults["grid_w"])
    n_repeated = _draw_scheduled_int(
        ctx, "n_repeated_colors", 2, 5, defaults["n_repeated_colors"]
    )
    n_singleton = _draw_scheduled_int(
        ctx, "n_singleton_colors", 2, 4, defaults["n_singleton_colors"]
    )
    pattern = _draw_scheduled_choice(
        ctx, "repeat_pattern", REPEAT_PATTERNS, defaults["repeat_pattern"]
    )

    multiplicities = _multiplicities(n_repeated, pattern)
    required_cells = sum(multiplicities) + n_singleton
    if required_cells > h * w:
        # This is unreachable for the declared domains, but keeping the check
        # makes future axis edits fail loudly rather than corrupting examples.
        raise ValueError(
            f"requested curriculum needs {required_cells} cells but grid has {h * w}"
        )

    colors = list(
        ctx.draw_distinct_colors(
            "colors", n=n_repeated + n_singleton, exclude=(0,)
        )
    )
    grid = full_grid(h, w, 0)
    all_cells = [(r, c) for r in range(h) for c in range(w)]

    # Put the designated pair far enough apart to be indisputably global.
    # Difficulty changes only spatial inference burden, never the selected rule:
    # easy uses a diagonal distance-2 pair, medium an intermediate separation,
    # and hard opposite corners.  Unbanded generation admits the full range.
    max_distance = h + w - 2
    pair_candidates = []
    for index, first_cell in enumerate(all_cells):
        for second_cell in all_cells[index + 1 :]:
            row_gap = abs(first_cell[0] - second_cell[0])
            col_gap = abs(first_cell[1] - second_cell[1])
            distance = row_gap + col_gap
            if row_gap == 0 or col_gap == 0:
                continue
            if difficulty == "easy" and distance != 2:
                continue
            if difficulty == "medium" and not (2 < distance < max_distance):
                continue
            if difficulty == "hard" and distance != max_distance:
                continue
            if difficulty is None and distance <= 1:
                continue
            pair_candidates.append((first_cell, second_cell))
    pair_rng = ctx.draw_rng(f"global_pair:{difficulty or 'unbanded'}")
    first, second = pair_rng.choice(pair_candidates)
    grid[first[0]][first[1]] = colors[0]
    grid[second[0]][second[1]] = colors[0]

    remaining = [cell for cell in all_cells if cell not in (first, second)]
    ctx.draw_rng(f"remaining_cells:{difficulty or 'unbanded'}").shuffle(remaining)
    cursor = 0

    for color, count in zip(colors[1:n_repeated], multiplicities[1:]):
        for _ in range(count):
            row, col = remaining[cursor]
            cursor += 1
            grid[row][col] = color

    for color in colors[n_repeated:]:
        row, col = remaining[cursor]
        cursor += 1
        grid[row][col] = color

    return grid


# ---------------------------------------------------------------------------
# Validation, observation, and selected rule
# ---------------------------------------------------------------------------


def _grid_shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if any(not isinstance(row, list) or not row for row in grid):
        return ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not (5 <= len(grid) <= 9 and 5 <= width <= 9):
        return ["grid dimensions must both be in 5..9"]
    if any(type(value) is not int or not (0 <= value <= 9) for row in grid for value in row):
        return ["grid cells must be integer ARC colors 0..9 (not booleans)"]
    return []


def _counts(grid: list[list[int]]) -> Counter[int]:
    return Counter(value for row in grid for value in row if value != 0)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = _grid_shape_errors(grid)
    if errors:
        return errors
    if difficulty not in (None, "easy", "medium", "hard"):
        return ["difficulty must be None, easy, medium, or hard"]

    counts = _counts(grid)
    repeated = [count for count in counts.values() if count > 1]
    singleton_count = sum(count == 1 for count in counts.values())
    errors = []
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 must be present")
    if not (2 <= len(repeated) <= 5):
        errors.append("expected 2..5 repeated nonzero colors")
    if not (2 <= singleton_count <= 4):
        errors.append("expected 2..4 singleton nonzero colors")
    if repeated and any(count not in (2, 3, 4) for count in repeated):
        errors.append("repeated-color multiplicities must be 2, 3, or 4")
    if repeated and 2 not in repeated:
        errors.append("at least one repeated color must occur exactly twice")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    errors = self_check(grid)
    if errors:
        raise ValueError("grid is outside the declared generator domain: " + "; ".join(errors))
    counts = _counts(grid)
    repeated = sorted(count for count in counts.values() if count > 1)
    if repeated and all(count == 2 for count in repeated):
        pattern = "pairs"
    elif repeated and set(repeated) <= {2, 3} and 3 in repeated:
        pattern = "mixed"
    elif repeated and set(repeated) <= {2, 4} and 4 in repeated:
        pattern = "heavy"
    else:  # guarded by self_check, retained as a defensive fail-closed branch
        raise ValueError("repeated-color multiplicities do not identify a declared pattern")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_repeated_colors": len(repeated),
        "n_singleton_colors": sum(count == 1 for count in counts.values()),
        "repeat_pattern": pattern,
    }


def rule_mirror(grid) -> list[list[int]]:
    errors = _grid_shape_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    counts = _counts(grid)
    return [
        [value if value != 0 and counts[value] > 1 else 0 for value in row]
        for row in grid
    ]


# ---------------------------------------------------------------------------
# Semantic counterexamples and lesson contract
# ---------------------------------------------------------------------------


def _keep_three_plus(grid) -> list[list[int]]:
    counts = _counts(grid)
    return [
        [value if value != 0 and counts[value] >= 3 else 0 for value in row]
        for row in grid
    ]


def _erase_one_singleton(grid) -> list[list[int]]:
    counts = _counts(grid)
    singleton_colors = sorted(color for color, count in counts.items() if count == 1)
    erased = singleton_colors[0] if singleton_colors else None
    return [
        [0 if value == erased else value for value in row]
        for row in grid
    ]


def _adjacent_only(grid) -> list[list[int]]:
    counts = _counts(grid)
    positions: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value:
                positions[value].append((row, col))
    adjacent_colors = {
        color
        for color, cells in positions.items()
        if counts[color] > 1
        and any(
            abs(r1 - r2) + abs(c1 - c2) == 1
            for index, (r1, c1) in enumerate(cells)
            for r2, c2 in cells[index + 1 :]
        )
    }
    return [
        [value if value in adjacent_colors else 0 for value in row]
        for row in grid
    ]


def _pair_survives(grid) -> bool:
    return any(count == 2 for count in _counts(grid).values())


def _multiple_singletons(grid) -> bool:
    return sum(count == 1 for count in _counts(grid).values()) >= 2


def _nonadjacent_pair_survives(grid) -> bool:
    positions: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value:
                positions[value].append((row, col))
    return any(
        len(cells) == 2
        and abs(cells[0][0] - cells[1][0]) + abs(cells[0][1] - cells[1][1]) > 1
        for cells in positions.values()
    )


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "keep_three_plus": _keep_three_plus,
    "erase_one_singleton": _erase_one_singleton,
    "adjacent_only": _adjacent_only,
}
SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "pair_survives": _pair_survives,
    "multiple_singletons": _multiple_singletons,
    "nonadjacent_pair_survives": _nonadjacent_pair_survives,
}
WITNESS_RIVALS = {
    "pair_survives": ("keep_three_plus",),
    "multiple_singletons": ("erase_one_singleton",),
    "nonadjacent_pair_survives": ("adjacent_only",),
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _valid_labeled_pair(pair: Any) -> bool:
    return (
        isinstance(pair, dict)
        and "input" in pair
        and "output" in pair
        and not _grid_shape_errors(pair["input"])
        and pair["output"] == rule_mirror(pair["input"])
    )


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, list) or not isinstance(query, dict):
        return ["lesson must contain a demo list and one query pair"]
    if len(demos) < 1:
        return ["lesson needs at least one labeled demonstration"]
    pairs = list(demos) + [query]
    if not all(_valid_labeled_pair(pair) for pair in pairs):
        return ["lesson contains a malformed or incorrectly labeled pair"]

    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
        changes_query = rival(query["input"]) != query["output"]
        if fits_demos and changes_query:
            reasons.append(f"rival {name} fits all demonstrations but changes the query")
    return reasons
