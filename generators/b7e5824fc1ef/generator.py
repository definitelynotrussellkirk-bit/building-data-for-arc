"""Semantic generator for ARC task b7e5824fc1ef.

A full-height color-5 column divides equal left and right halves.  Mirror the
right half horizontally onto the left half; a nonzero mirrored-right cell wins,
otherwise keep the left cell.

Ordinary draws always contain four decisive lesson cues: a left-only fallback,
a right-only mirrored copy, a different-color overlap proving right-side
precedence, and an asymmetric right-only cell that refutes copying the right
half without mirroring.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b7e5824fc1ef"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "57dc24967d17"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Split at the centered full-height 5-divider, mirror the right half, "
    "and overlay nonzero right cells over the left half."
)
INVARIANTS = [
    "the grid is rectangular with an odd width",
    "exactly one centered full-height column is color 5",
    "no color 5 occurs outside the divider",
    "left and right halves have equal width and both contain foreground",
    "ordinary draws contain left-only, right-only, and different-color overlap cues",
]

SHAPE_PROFILES = ("canonical", "compact", "expanded")
DENSITY_LEVELS = ("sparse", "balanced", "dense")
BALANCE_MODES = ("even", "left_heavy", "right_heavy")

AXES = {
    "shape_profile": {
        "type": "str",
        "default": "rng canonical|compact|expanded",
        "valid": "|".join(SHAPE_PROFILES),
    },
    "palette_size": {
        "type": "int",
        "default": "rng 2..4 foreground colors",
        "valid": "2..4",
    },
    "density": {
        "type": "str",
        "default": "rng sparse|balanced|dense",
        "valid": "|".join(DENSITY_LEVELS),
    },
    "balance": {
        "type": "str",
        "default": "rng even|left_heavy|right_heavy",
        "valid": "|".join(BALANCE_MODES),
    },
}


def _validate_grid(grid: object) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be nonempty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _divider(grid: list[list[int]]) -> int | None:
    height = len(grid)
    full_fives = [
        column
        for column in range(len(grid[0]))
        if all(grid[row][column] == 5 for row in range(height))
    ]
    return full_fives[0] if len(full_fives) == 1 else None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check the authority-valid input grammar, not curriculum-only cues."""
    errors = _validate_grid(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if width < 7 or width % 2 == 0:
        errors.append("width must be odd and at least 7")
    if not 5 <= height <= 30:
        errors.append("height must be in 5..30")

    divider = _divider(grid)
    if divider is None:
        full_fives = [
            column
            for column in range(width)
            if all(grid[row][column] == 5 for row in range(height))
        ]
        errors.append(f"expected exactly one full-height 5-divider, got {full_fives}")
        return errors
    if divider != width // 2:
        errors.append("divider must be centered so the two halves have equal width")
    if any(
        grid[row][column] == 5
        for row in range(height)
        for column in range(width)
        if column != divider
    ):
        errors.append("color 5 may appear only in the divider column")

    left_count = sum(
        grid[row][column] != 0
        for row in range(height)
        for column in range(divider)
    )
    right_count = sum(
        grid[row][column] != 0
        for row in range(height)
        for column in range(divider + 1, width)
    )
    if left_count == 0:
        errors.append("left half must contain foreground")
    if right_count == 0:
        errors.append("right half must contain foreground")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The task manifold is exactly the centered-divider grammar."""
    return self_check(grid)


def _shape(profile: str, *, difficulty: str | None, rng) -> tuple[int, int]:
    if profile == "canonical":
        return 10, 4
    if profile == "compact":
        return 8, 3
    if difficulty == "easy":
        return rng.choice(((11, 5), (12, 5), (12, 6)))
    if difficulty == "hard":
        return rng.choice(((14, 6), (15, 7), (16, 8)))
    return rng.choice(((12, 5), (13, 6), (14, 7)))


def _targets(
    capacity: int, density: str, balance: str, difficulty: str | None
) -> tuple[int, int]:
    ratio = {"sparse": 0.17, "balanced": 0.32, "dense": 0.50}[density]
    ratio += {"easy": -0.03, "medium": 0.0, "hard": 0.03}.get(difficulty, 0.0)
    base = max(2, round(capacity * ratio))
    delta = max(2, round(capacity * 0.08))
    if balance == "left_heavy":
        return min(capacity, base + delta), max(2, base - delta)
    if balance == "right_heavy":
        return max(2, base - delta), min(capacity, base + delta)
    return base, base


def _allocate_depths(
    *, height: int, side_width: int, target: int, forced: list[int], rng
) -> list[int]:
    depths = list(forced)
    eligible = list(range(3, height))
    while sum(depths) < target:
        available = [row for row in eligible if depths[row] < side_width]
        if not available:
            raise AssertionError(
                f"cannot allocate target={target} with height={height}, width={side_width}"
            )
        depths[rng.choice(available)] += 1
    return depths


def _paint_connected_runs(
    *, height: int, side_width: int, left_target: int, right_target: int,
    palette: list[int], rng
) -> list[list[int]]:
    width = 2 * side_width + 1
    divider = side_width
    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][divider] = 5

    # Rows 0..2 are locked so the four semantic cues cannot be erased by later
    # density allocation.  Every occupied run touches the divider, keeping the
    # morphology close to the canonical single connected non-background object.
    left_depths = _allocate_depths(
        height=height,
        side_width=side_width,
        target=left_target,
        forced=[1, 0, 1] + [0] * (height - 3),
        rng=rng,
    )
    right_depths = _allocate_depths(
        height=height,
        side_width=side_width,
        target=right_target,
        forced=[0, 1, 1] + [0] * (height - 3),
        rng=rng,
    )

    occupied: list[tuple[int, int]] = []
    for row, depth in enumerate(left_depths):
        for column in range(divider - depth, divider):
            occupied.append((row, column))
    for row, depth in enumerate(right_depths):
        for column in range(divider + 1, divider + 1 + depth):
            occupied.append((row, column))

    left_color = max(palette[0], palette[1])
    right_color = min(palette[0], palette[1])
    forced_colors = {
        (0, divider - 1): left_color,   # left-only fallback
        (1, divider + 1): right_color,  # right-only mirrored copy
        (2, divider - 1): left_color,   # overlap: left candidate
        (2, divider + 1): right_color,  # overlap: right wins, even though smaller
    }
    colors = dict(forced_colors)

    remaining = [position for position in occupied if position not in colors]
    rng.shuffle(remaining)
    already_used = set(colors.values())
    for color in palette:
        if color in already_used:
            continue
        if not remaining:
            raise AssertionError("not enough occupied cells to realize the palette")
        colors[remaining.pop()] = color
        already_used.add(color)
    for position in remaining:
        colors[position] = rng.choice(palette)

    for (row, column), color in colors.items():
        grid[row][column] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # Anchor the canonical 10x9 scale frequently while retaining exact
    # overrideability and meaningful compact/expanded support.
    profile = ctx.draw_choice(
        "shape_profile",
        ("canonical",) * 8 + ("compact", "expanded"),
    )
    palette_size = ctx.draw_choice("palette_size", (2, 2, 3, 4))
    density = ctx.draw_choice("density", DENSITY_LEVELS)
    balance = ctx.draw_choice("balance", BALANCE_MODES)
    rng = ctx.draw_rng("shape-and-layout")
    height, side_width = _shape(profile, difficulty=difficulty, rng=rng)
    palette = rng.sample([color for color in range(1, 10) if color != 5], palette_size)
    left_target, right_target = _targets(
        height * side_width, density, balance, difficulty
    )
    grid = _paint_connected_runs(
        height=height,
        side_width=side_width,
        left_target=left_target,
        right_target=right_target,
        palette=palette,
        rng=rng,
    )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError(f"constructed invalid grid: {errors}")
    return grid


def _analysis(grid) -> dict[str, object]:
    errors = self_check(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    divider = width // 2
    left_count = right_count = 0
    left_only = right_only = overlap = different_overlap = 0
    for row in range(height):
        for column in range(divider):
            left = grid[row][column]
            right = grid[row][width - 1 - column]
            left_count += int(left != 0)
            right_count += int(right != 0)
            left_only += int(left != 0 and right == 0)
            right_only += int(right != 0 and left == 0)
            overlap += int(left != 0 and right != 0)
            different_overlap += int(left != 0 and right != 0 and left != right)
    capacity = height * divider
    occupancy = (left_count + right_count) / (2 * capacity)
    if occupancy < 0.25:
        density = "sparse"
    elif occupancy < 0.42:
        density = "balanced"
    else:
        density = "dense"
    if left_count == right_count:
        balance = "even"
    elif left_count > right_count:
        balance = "left_heavy"
    else:
        balance = "right_heavy"
    if (height, divider) == (10, 4):
        profile = "canonical"
    elif (height, divider) == (8, 3):
        profile = "compact"
    else:
        profile = "expanded"
    return {
        "errors": [],
        "shape_profile": profile,
        "palette_size": len(
            {value for row in grid for value in row if value not in (0, 5)}
        ),
        "density": density,
        "balance": balance,
        "left_only": left_only,
        "right_only": right_only,
        "overlap": overlap,
        "different_overlap": different_overlap,
    }


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analysis(grid)
    if analysis.get("errors"):
        raise ValueError(f"cannot observe malformed grid: {analysis['errors']}")
    return {
        axis: analysis[axis]
        for axis in ("shape_profile", "palette_size", "density", "balance")
    }


def rule_mirror_merge(grid: list[list[int]]) -> list[list[int]]:
    errors = _validate_grid(grid)
    if errors:
        raise ValueError(errors[0])
    divider = _divider(grid)
    if divider is None:
        raise ValueError("missing unique full-height color-5 divider")
    height, width = len(grid), len(grid[0])
    return [
        [
            grid[row][width - 1 - column]
            if grid[row][width - 1 - column] != 0
            else grid[row][column]
            for column in range(divider)
        ]
        for row in range(height)
    ]


def _rival_left_only(grid):
    divider = len(grid[0]) // 2
    return [list(row[:divider]) for row in grid]


def _rival_right_only(grid):
    height, width = len(grid), len(grid[0])
    divider = width // 2
    return [
        [grid[row][width - 1 - column] for column in range(divider)]
        for row in range(height)
    ]


def _rival_left_precedence(grid):
    height, width = len(grid), len(grid[0])
    divider = width // 2
    return [
        [
            grid[row][column]
            if grid[row][column] != 0
            else grid[row][width - 1 - column]
            for column in range(divider)
        ]
        for row in range(height)
    ]


def _rival_unmirrored_right(grid):
    height, width = len(grid), len(grid[0])
    divider = width // 2
    return [
        [
            grid[row][divider + 1 + column]
            if grid[row][divider + 1 + column] != 0
            else grid[row][column]
            for column in range(divider)
        ]
        for row in range(height)
    ]


def _rival_numeric_max(grid):
    height, width = len(grid), len(grid[0])
    divider = width // 2
    return [
        [max(grid[row][column], grid[row][width - 1 - column]) for column in range(divider)]
        for row in range(height)
    ]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "copy_left_half": _rival_left_only,
    "mirror_right_only": _rival_right_only,
    "left_wins_overlap": _rival_left_precedence,
    "copy_right_without_mirroring": _rival_unmirrored_right,
    "numeric_max_overlay": _rival_numeric_max,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _w_left_fallback(grid) -> bool:
    return int(_analysis(grid).get("left_only", 0)) > 0


def _w_right_mirror(grid) -> bool:
    return int(_analysis(grid).get("right_only", 0)) > 0


def _w_right_precedence(grid) -> bool:
    return int(_analysis(grid).get("different_overlap", 0)) > 0


def _w_mirror_orientation(grid) -> bool:
    return rule_mirror_merge(grid) != _rival_unmirrored_right(grid)


SEMANTIC_WITNESSES = {
    "left_only_fallback": _w_left_fallback,
    "right_only_mirrored_copy": _w_right_mirror,
    "different_color_right_precedence": _w_right_precedence,
    "right_half_must_be_mirrored": _w_mirror_orientation,
}
WITNESS_RIVALS = {
    "left_only_fallback": ["mirror_right_only"],
    "right_only_mirrored_copy": ["copy_left_half"],
    "different_color_right_precedence": ["left_wins_overlap", "numeric_max_overlay"],
    "right_half_must_be_mirrored": ["copy_right_without_mirroring"],
}


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            return [f"demo {index} is not an input/output pair"]
        if rule_mirror_merge(demo["input"]) != demo["output"]:
            reasons.append(f"demo {index} output does not match the canonical rule")
    if not isinstance(query, dict) or "input" not in query:
        return reasons + ["query is not an input pair"]
    expected = rule_mirror_merge(query["input"])
    if "output" in query and query["output"] != expected:
        reasons.append("query output does not match the canonical rule")
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != expected:
            reasons.append(
                f"competing rule '{name}' fits every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures():
    """Targeted malformed scenes that the structural checker must reject."""
    base = generate(991, 17, difficulty="medium", shape_profile="canonical")
    divider = len(base[0]) // 2

    missing_divider = deepcopy(base)
    for row in range(len(missing_divider)):
        missing_divider[row][divider] = 0

    extra_five = deepcopy(base)
    extra_five[0][divider - 1] = 5

    unequal_halves = [row[:-1] for row in deepcopy(base)]

    empty_left = deepcopy(base)
    for row in range(len(empty_left)):
        for column in range(divider):
            empty_left[row][column] = 0

    empty_right = deepcopy(base)
    for row in range(len(empty_right)):
        for column in range(divider + 1, len(empty_right[0])):
            empty_right[row][column] = 0

    ragged = deepcopy(base)
    ragged[0] = ragged[0][:-1]

    return [
        ("missing_full_height_divider", missing_divider),
        ("extra_five_outside_divider", extra_five),
        ("unequal_half_widths", unequal_halves),
        ("empty_left_half", empty_left),
        ("empty_right_half", empty_right),
        ("ragged_grid", ragged),
    ]
