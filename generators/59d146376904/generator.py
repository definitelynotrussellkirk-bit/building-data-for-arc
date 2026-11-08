"""Generator for 59d146376904 — summarize quadrant nonzero majorities.

The input has even height and width and is split into four equal quadrants.
Within each quadrant, the uniquely most frequent nonzero color is selected.
Those four colors are returned in their spatial 2x2 arrangement.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "59d146376904"
VERSION = "4.0.0"
RULE_HASH = "f575832a27ff"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Split an even grid into four equal quadrants. In every quadrant, choose "
    "the uniquely most frequent non-background color (background 0 is ignored), "
    "then place the four selected colors in a 2x2 spatial summary."
)
INVARIANTS = [
    "background is color 0",
    "height and width are even",
    "every quadrant has a unique most-frequent nonzero color",
    "the four selected quadrant colors are distinct",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
_PALETTES = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (1, 2, 4, 6, 7, 9),
    "cool": (1, 3, 5, 6, 8, 9),
    "varied": (1, 2, 3, 4, 5, 6, 7, 8, 9),
}
DEGENERATE_TEXTURES = ("no_cells", "single_quadrant_filled", "tied_majority")
HELPFUL_TEXTURES: tuple[str, ...] = ()
AXES = {
    "grid_h": {"type": "int", "default": "scheduled even 6..12", "valid": "even 4..12"},
    "grid_w": {"type": "int", "default": "scheduled even 6..12", "valid": "even 4..12"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "default|warm|cool|varied"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"when": ["grid_h", "qh"], "constraint": "grid_h == 2*qh"},
    {"when": ["grid_w", "qw"], "constraint": "grid_w == 2*qw"},
]

_SCHEDULE = ((6, 8), (8, 8), (6, 10), (8, 10), (6, 6), (12, 12))


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty in (None, "easy", "medium", "hard"):
        return
    if type(difficulty) in (int, float) and 0.0 <= float(difficulty) <= 1.0:
        return
    raise ValueError("difficulty must be easy, medium, hard, None, or a number in [0,1]")


def _exact_int(name: str, value: Any, lo: int, hi: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool, float, and string are forbidden")
    if not lo <= value <= hi:
        raise ValueError(f"{name} must be in [{lo}, {hi}]")
    return value


def _scheduled_dimensions(sample_index: int, difficulty: Any) -> tuple[int, int]:
    h, w = _SCHEDULE[sample_index % len(_SCHEDULE)]
    if difficulty == "easy" or (type(difficulty) in (int, float) and float(difficulty) < 0.34):
        return (6, 6) if sample_index % 2 == 0 else (6, 8)
    if difficulty == "hard" or (type(difficulty) in (int, float) and float(difficulty) >= 0.67):
        return (12, 12) if sample_index % 2 == 0 else (10, 12)
    return h, w


def _resolve_dimension(ctx, overrides: dict[str, Any], axis: str, alias: str, default: int) -> int:
    alias_value = None
    if alias in overrides and overrides[alias] is not None:
        alias_value = 2 * _exact_int(alias, overrides[alias], 2, 6)
    if axis in overrides and overrides[axis] is not None:
        _exact_int(axis, overrides[axis], 4, 12)
        value = ctx.draw_int_strict(axis, 4, 12)
    else:
        value = alias_value if alias_value is not None else default
        value = ctx.draw_int(axis, value, value)
    if value % 2:
        raise ValueError(f"{axis} must be even so the grid has four equal quadrants")
    if alias_value is not None and alias_value != value:
        raise ValueError(f"incompatible overrides: {axis}={value} but {alias} implies {alias_value}")
    return value


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a deterministic canonical-like input grid.

    ``qh``/``qw`` remain accepted as exact legacy aliases for half-dimensions,
    while the advertised ``grid_h``/``grid_w`` axes are now truly observable.
    Negative textures are explicit fixtures outside the ordinary axis domain.
    """
    _validate_difficulty(difficulty)
    unknown = sorted(set(overrides) - set(AXES) - {"qh", "qw", "texture"})
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    texture = overrides.get("texture")
    if texture is not None:
        if texture not in DEGENERATE_TEXTURES:
            raise ValueError(f"unknown texture {texture!r}")
        return _draw_from_degenerate(texture)

    default_h, default_w = _scheduled_dimensions(sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides={key: value for key, value in overrides.items() if key in AXES},
    )
    h = _resolve_dimension(ctx, overrides, "grid_h", "qh", default_h)
    w = _resolve_dimension(ctx, overrides, "grid_w", "qw", default_w)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    palette = _PALETTES[palette_kind]
    rng = ctx.draw_rng("quadrant_contents")

    qh, qw = h // 2, w // 2
    area = qh * qw
    grid = full_grid(h, w, 0)
    majors = rng.sample(list(palette), 4)
    quadrants = ((0, 0), (0, qw), (qh, 0), (qh, qw))
    for quadrant_index, (major, (r0, c0)) in enumerate(zip(majors, quadrants)):
        cells = [(r0 + dr, c0 + dc) for dr in range(qh) for dc in range(qw)]
        rng.shuffle(cells)
        # Canonical examples are sparse: the selected color is the unique
        # nonzero plurality, not necessarily more than half of all cells.
        major_lo = max(2, area // 3)
        major_hi = max(major_lo, area - 2)
        major_count = rng.randint(major_lo, major_hi)
        remaining = area - major_count
        minority_count = rng.randint(1, min(major_count - 1, remaining))
        competitor_pool = [color for color in range(1, 10) if color != major]
        competitor = rng.choice(competitor_pool)
        values = [major] * major_count + [competitor] * minority_count + [0] * (remaining - minority_count)
        rng.shuffle(values)
        # Force at least one visible anti-shortcut cue: across the four
        # quadrants, alternating corners contain a non-major cell.
        corner = quadrant_index % len(cells)
        nonmajor = next((i for i, value in enumerate(values) if value != major), None)
        if nonmajor is not None:
            values[corner], values[nonmajor] = values[nonmajor], values[corner]
        for (row, col), value in zip(cells, values):
            grid[row][col] = value

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"ordinary generator produced invalid grid: {errors}")
    return grid


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty literal list of rows")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular with literal row lists")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact integer ARC colors 0..9")
    return len(grid), width


def _majority_entry(values: list[int]) -> tuple[int, int, int]:
    counts = Counter(value for value in values if value != 0)
    if not counts:
        return 0, 0, 0
    ranked = sorted(counts.items(), key=lambda item: (-item[1], -item[0]))
    winner, count = ranked[0]
    runner_up = ranked[1][1] if len(ranked) > 1 else 0
    return winner, count, runner_up


def quadrant_analysis(grid: Any) -> list[dict[str, Any]]:
    h, w = _validate_grid(grid)
    if h % 2 or w % 2:
        raise ValueError("grid height and width must both be even")
    qh, qw = h // 2, w // 2
    result = []
    for index, (r0, c0) in enumerate(((0, 0), (0, qw), (qh, 0), (qh, qw))):
        values = [grid[row][col] for row in range(r0, r0 + qh) for col in range(c0, c0 + qw)]
        majority, count, runner_up = _majority_entry(values)
        result.append(
            {
                "index": index,
                "origin": (r0, c0),
                "area": len(values),
                "majority_color": majority,
                "majority_count": count,
                "runner_up_count": runner_up,
                "minority_nonzero_count": sum(value != 0 and value != majority for value in values),
                "background_count": values.count(0),
                "distinct_nonzero": len({value for value in values if value != 0}),
            }
        )
    return result


def rule_summary(grid: Any) -> list[list[int]]:
    facts = quadrant_analysis(grid)
    colors = [item["majority_color"] for item in facts]
    return [colors[:2], colors[2:]]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    try:
        h, w = _validate_grid(grid)
    except ValueError as error:
        return [str(error)]
    errors: list[str] = []
    if h % 2:
        errors.append(f"grid height {h} is not even")
    if w % 2:
        errors.append(f"grid width {w} is not even")
    if errors:
        return errors
    facts = quadrant_analysis(grid)
    for item in facts:
        if item["majority_color"] == 0:
            errors.append(f"quadrant {item['index']} has no nonzero cells")
        elif item["majority_count"] <= item["runner_up_count"]:
            errors.append(f"quadrant {item['index']} has no unique nonzero majority")
    colors = [item["majority_color"] for item in facts if item["majority_color"] != 0]
    if len(colors) == 4 and len(set(colors)) != 4:
        errors.append("quadrant majority colors must be distinct")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _draw_from_degenerate(name: str) -> list[list[int]]:
    qh, qw = 3, 4
    grid = full_grid(qh * 2, qw * 2, 0)
    if name == "no_cells":
        return grid
    if name == "single_quadrant_filled":
        for row in range(qh):
            for col in range(qw):
                grid[row][col] = 4
        return grid
    if name == "tied_majority":
        grid[0][0] = 4
        grid[0][1] = 6
        grid[1][0] = 4
        grid[1][1] = 6
        for row in range(qh):
            for col in range(qw):
                grid[row][qw + col] = 7
                grid[qh + row][col] = 8
                grid[qh + row][qw + col] = 9
        return grid
    raise ValueError(name)


def _quadrant_values(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    qh, qw = h // 2, w // 2
    return [
        [grid[row][col] for row in range(r0, r0 + qh) for col in range(c0, c0 + qw)]
        for r0, c0 in ((0, 0), (0, qw), (qh, 0), (qh, qw))
    ]


def _rival_first_nonzero(grid):
    colors = []
    for values in _quadrant_values(grid):
        colors.append(next((value for value in values if value != 0), 0))
    return [colors[:2], colors[2:]]


def _rival_highest_color(grid):
    colors = [max((value for value in values if value != 0), default=0) for values in _quadrant_values(grid)]
    return [colors[:2], colors[2:]]


def _rival_including_zero(grid):
    colors = []
    for values in _quadrant_values(grid):
        counts = Counter(values)
        colors.append(sorted(counts, key=lambda color: (-counts[color], -color))[0])
    return [colors[:2], colors[2:]]


def _rival_global_top_four(grid):
    counts = Counter(value for row in grid for value in row if value != 0)
    colors = sorted(counts, key=lambda color: (-counts[color], -color))[:4]
    colors += [0] * (4 - len(colors))
    return [colors[:2], colors[2:]]


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "first_nonzero_per_quadrant": _rival_first_nonzero,
    "highest_color_per_quadrant": _rival_highest_color,
    "majority_including_background": _rival_including_zero,
    "global_top_four": _rival_global_top_four,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "nonmajor_corner": lambda grid: not self_check(grid)
    or any(values[0] != item["majority_color"] for values, item in zip(_quadrant_values(grid), quadrant_analysis(grid))),
    "minority_present": lambda grid: not self_check(grid)
    or all(item["minority_nonzero_count"] >= 1 for item in quadrant_analysis(grid)),
}


def lesson_identifiable(demos, query) -> list[str]:
    if type(demos) is not list or not demos:
        return ["at least one demonstration is required"]
    try:
        pairs = [
            (pair["input"], pair["output"])
            for pair in demos
            if type(pair) is dict and "input" in pair and "output" in pair
        ]
        query_grid = query["input"]
    except (TypeError, KeyError):
        return ["malformed lesson"]
    if len(pairs) != len(demos):
        return ["malformed demonstration"]
    errors = []
    for index, (grid, output) in enumerate(pairs):
        if self_check(grid):
            errors.append(f"demo {index} input violates grammar")
        if output != rule_summary(grid):
            errors.append(f"demo {index} label differs from canonical rule")
    if self_check(query_grid):
        errors.append("query input violates grammar")
    if errors:
        return errors
    expected_query = rule_summary(query_grid)
    for name, rival in SEMANTIC_RIVALS.items():
        try:
            if all(rival(grid) == output for grid, output in pairs) and rival(query_grid) != expected_query:
                errors.append(f"lesson leaves query-changing rival: {name}")
        except (ValueError, TypeError, IndexError):
            continue
    return errors
