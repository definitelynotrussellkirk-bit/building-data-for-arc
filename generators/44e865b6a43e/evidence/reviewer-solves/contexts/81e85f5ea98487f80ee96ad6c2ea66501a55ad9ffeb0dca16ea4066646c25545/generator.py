"""Generator for ARC task 44e865b6a43e — rotate bar attributes separately.

The input is an orange (7) canvas containing three to five one-cell-wide,
bottom-aligned bars in every other column.  Bar colors are distinct; heights
may repeat.  The target keeps the bar columns fixed, rotates colors one place
to the right, and independently rotates heights one place to the left.

Ordinary lessons use at least three bars so the independent color/height
rotations cannot collapse into the same two-item swap.
"""
from __future__ import annotations

from itertools import permutations
from typing import Any

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "44e865b6a43e"
TASK_ID = "44e865b6a43e"
VERSION = "2.1.0"
RULE_HASH = "de38c98a1856"  # sha256[:12] of whitespace-normalized canonical rule

SUMMARY = (
    "An orange 7..12 by (2n+1) grid contains 3..5 distinct-colored, "
    "one-cell-wide bars in alternating columns, all bottom-aligned. Heights "
    "may repeat but are not all equal. Rotate colors right and heights left."
)
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "all cells are ARC colors 0..9 and background is color 7",
    "the grid is 7..12 rows high and has width 2*n_bars+1",
    "there are exactly 3..5 bars in columns 1,3,...,2*n_bars-1",
    "each bar is a solid, one-cell-wide, bottom-aligned run shorter than the grid",
    "bar colors are pairwise distinct and may include color 0",
    "bar heights may repeat, but at least two heights differ",
]

HEIGHT_PATTERNS = ("ascending", "descending", "mixed", "repeat")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical square anchors and difficulty-biased rectangles over 7..12",
        "valid": "7..12",
    },
    "n_bars": {
        "type": "int",
        "default": "difficulty-biased 3..5, with 4..5-bar teaching witnesses",
        "valid": "3..5",
    },
    "height_pattern": {
        "type": "str",
        "default": "alternating crossed-repeat witnesses and keyed draws over all patterns",
        "valid": "|".join(HEIGHT_PATTERNS),
    },
}


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    """Return exact scene facts and strict grammar errors."""
    facts: dict[str, Any] = {
        "grid_h": None,
        "grid_w": None,
        "n_bars": None,
        "columns": [],
        "colors": [],
        "heights": [],
    }
    if not isinstance(grid, (list, tuple)) or not grid:
        return facts, ["grid must be a nonempty rectangular sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return facts, ["grid must have at least one column"]

    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return facts, ["grid must be rectangular"]

    errors: list[str] = []
    invalid_cells = sorted(
        {
            repr(value)
            for row in grid
            for value in row
            if isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 9
        }
    )
    if invalid_cells:
        errors.append(
            "all cells must be literal ARC colors 0..9; invalid values: "
            + ", ".join(invalid_cells[:6])
        )
        return facts, errors

    height = len(grid)
    facts["grid_h"], facts["grid_w"] = height, width
    if not 7 <= height <= 12:
        errors.append(f"grid height must be in 7..12, got {height}")
    if width % 2 != 1:
        errors.append(f"grid width must be odd, got {width}")
        return facts, errors

    n_bars = (width - 1) // 2
    facts["n_bars"] = n_bars
    if not 3 <= n_bars <= 5:
        errors.append(
            f"grid width must encode 3..5 alternating bars, got {n_bars}"
        )

    expected_columns = list(range(1, width - 1, 2))
    facts["columns"] = expected_columns

    # All margin/separator columns must be pure orange background.
    for col in range(0, width, 2):
        bad_rows = [row for row in range(height) if grid[row][col] != 7]
        if bad_rows:
            errors.append(
                f"background column {col} must be all 7; non-7 at rows "
                f"{bad_rows[:6]}"
            )

    colors: list[int] = []
    heights: list[int] = []
    for col in expected_columns:
        values = [grid[row][col] for row in range(height)]
        non_bg_rows = [row for row, value in enumerate(values) if value != 7]
        if not non_bg_rows:
            errors.append(f"bar column {col} is empty")
            continue

        first = non_bg_rows[0]
        bar_color = values[first]
        expected_rows = list(range(first, height))
        if non_bg_rows != expected_rows:
            errors.append(
                f"bar column {col} must be a contiguous bottom-aligned run"
            )
        if any(values[row] != bar_color for row in non_bg_rows):
            errors.append(f"bar column {col} must use one color")
        if first == 0:
            errors.append(f"bar column {col} must be shorter than the grid")
        if any(values[row] != 7 for row in range(first)):
            errors.append(f"cells above bar column {col} must be color 7")

        colors.append(bar_color)
        heights.append(height - first)

    facts["colors"] = colors
    facts["heights"] = heights
    if len(colors) == len(expected_columns) and len(set(colors)) != len(colors):
        errors.append("bar colors must be pairwise distinct")
    if len(heights) == len(expected_columns) and len(set(heights)) < 2:
        errors.append("bar heights must not all be equal")
    return facts, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the full task grammar, including canonical repeated heights."""
    del difficulty, meta
    return _analyze(grid)[1]


def observe_overrides(grid) -> dict[str, Any]:
    """Recover semantic controls from the returned grid, not draw metadata."""
    facts, errors = _analyze(grid)
    if errors:
        return {}
    heights = facts["heights"]
    if len(set(heights)) < len(heights):
        pattern = "repeat"
    elif heights == sorted(heights):
        pattern = "ascending"
    elif heights == sorted(heights, reverse=True):
        pattern = "descending"
    else:
        pattern = "mixed"
    return {"n_bars": int(facts["n_bars"]), "height_pattern": pattern}


def bar_profile(grid) -> dict[str, Any]:
    """Return the validated left-to-right bar profile for audits and tests."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n_bars": facts["n_bars"],
        "columns": list(facts["columns"]),
        "colors": list(facts["colors"]),
        "heights": list(facts["heights"]),
    }


def rule_mirror(grid):
    """Input-pure Python mirror of the canonical Racket transformation."""
    profile = bar_profile(grid)
    height = int(profile["grid_h"])
    width = int(profile["grid_w"])
    columns = profile["columns"]
    colors = profile["colors"]
    heights = profile["heights"]

    output = [[7] * width for _ in range(height)]
    output_colors = [colors[-1], *colors[:-1]]
    output_heights = [*heights[1:], heights[0]]
    for col, color, bar_height in zip(columns, output_colors, output_heights):
        for row in range(height - bar_height, height):
            output[row][col] = color
    return output


def _height_sequence(
    ctx, *, grid_h: int, n_bars: int, pattern: str, crossed_repeat: bool = False
) -> list[int]:
    """Give every lawful order/repeat multiplicity positive sampling support."""
    rng = ctx.draw_rng("bar_heights")
    if pattern == "repeat":
        if crossed_repeat:
            # A repeated first/interior height makes nearest-shape association
            # disagree with position-based attribute rotation. Numeric rank is
            # independent of the two repeated positions.
            levels = rng.sample(range(1, grid_h), n_bars - 1)
            second = rng.choice(list(range(2, n_bars - 1)))
            heights = [levels[0]] + [None] * (n_bars - 1)
            heights[second] = levels[0]
            remaining = iter(levels[1:])
            return [next(remaining) if value is None else value for value in heights]
        distinct_count = rng.randint(2, n_bars - 1)
        levels = rng.sample(range(1, grid_h), distinct_count)
        heights = levels + [rng.choice(levels) for _ in range(n_bars - distinct_count)]
        rng.shuffle(heights)
        return heights
    base = sorted(rng.sample(range(1, grid_h), n_bars))
    if pattern == "ascending":
        return base
    if pattern == "descending":
        return list(reversed(base))
    if pattern == "mixed":
        # At most 5! candidates; bounded enumeration avoids rejection loops and
        # gives all nonmonotone orders support, not one rotation of sorted bars.
        orders = [p for p in permutations(base) if list(p) not in (base, base[::-1])]
        return list(rng.choice(orders))
    raise ValueError(f"unknown height pattern {pattern!r}")


def _validate_request(seed, sample_index, difficulty, overrides: dict[str, Any]) -> None:
    for name, value in (("seed", seed), ("sample_index", sample_index)):
        if type(value) is not int:
            raise TypeError(f"{name} must be a literal integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for axis in ("grid_h", "n_bars"):
        value = overrides.get(axis)
        if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
            raise TypeError(f"{axis} override must be an integer")
    value = overrides.get("height_pattern")
    if value is not None and not isinstance(value, str):
        raise TypeError("height_pattern override must be a string")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    witness_slot = sample_index % 2 == 1
    if witness_slot and overrides.get("n_bars") is None:
        choices = (4,) if difficulty in ("easy", "medium") else (4, 5)
        n_bars = ctx.draw_choice("n_bars", choices)
    else:
        n_bars = ctx.draw_int_diff("n_bars", 3, 5)
    if witness_slot and overrides.get("height_pattern") is None:
        height_pattern = ctx.draw_choice("height_pattern", ("repeat",))
    else:
        height_pattern = ctx.draw_choice("height_pattern", HEIGHT_PATTERNS)

    if overrides.get("grid_h") is not None:
        grid_h = ctx.draw_int_diff("grid_h", 7, 12)
    elif sample_index % 4 == 0:
        grid_h = ctx.draw_choice("grid_h", (2 * n_bars + 1,))
    elif witness_slot:
        preferred = {"easy": (7, 8, 9), "medium": (8, 9, 10, 11),
                     "hard": (9, 10, 11, 12)}.get(difficulty, tuple(range(7, 13)))
        grid_h = ctx.draw_choice("grid_h", tuple(h for h in preferred if h != 2 * n_bars + 1))
    else:
        grid_h = ctx.draw_int_diff("grid_h", 7, 12)

    grid_w = 2 * n_bars + 1
    colors = ctx.draw_distinct_colors("bar_colors", n=n_bars, exclude={7})
    heights = _height_sequence(
        ctx,
        grid_h=grid_h,
        n_bars=n_bars,
        pattern=height_pattern,
        crossed_repeat=witness_slot and n_bars >= 4 and height_pattern == "repeat",
    )

    grid = [[7] * grid_w for _ in range(grid_h)]
    for col, color, bar_height in zip(
        range(1, grid_w - 1, 2), colors, heights
    ):
        for row in range(grid_h - bar_height, grid_h):
            grid[row][col] = color
    return grid


# This schedule concerns default production draws. Exact caller overrides win
# and can remove the witnesses; lesson_identifiable then checks that lesson.
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("canonical_square", "crossed_repeat_rectangle", "varied")


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return ("canonical_square", "crossed_repeat_rectangle", "varied",
            "crossed_repeat_rectangle")[sample_index % LESSON_SCHEDULE_PERIOD]


def _render_attributes(grid, colors, heights, *, grid_h=None):
    height = len(grid) if grid_h is None else grid_h
    output = [[7] * len(grid[0]) for _ in range(height)]
    for index, (color, bar_height) in enumerate(zip(colors, heights)):
        for row in range(max(0, height - bar_height), height):
            output[row][2 * index + 1] = color
    return output


def _shift_attributes(grid, color_shift, height_shift):
    profile = bar_profile(grid)
    colors, heights = profile["colors"], profile["heights"]
    n = len(colors)
    return _render_attributes(
        grid, [colors[(i - color_shift) % n] for i in range(n)],
        [heights[(i - height_shift) % n] for i in range(n)],
    )


def nearest_equal_height_association(grid):
    """Plausible but wrong: track equally tall shapes by shortest movement.

    Move heights left, choose a nearest nonstationary one-to-one match to input
    shapes, and recolor each from the source two positions to its left. Unique
    heights force the intended result. Some repeated heights cross identities.
    """
    profile = bar_profile(grid)
    colors, heights = profile["colors"], profile["heights"]
    n = len(colors)
    moved = heights[1:] + heights[:1]
    candidates = (
        p for p in permutations(range(n))
        if all(p[i] != i and heights[p[i]] == moved[i] for i in range(n))
    )
    donors = min(candidates, key=lambda p: (sum(abs(p[i] - i) for i in range(n)), p))
    return _render_attributes(grid, [colors[(j - 2) % n] for j in donors], moved)


def square_canvas(grid):
    """Plausible but wrong: infer square output geometry from canonical pairs."""
    profile = bar_profile(grid)
    colors, heights = profile["colors"], profile["heights"]
    return _render_attributes(grid, colors[-1:] + colors[:-1], heights[1:] + heights[:1],
                              grid_h=len(grid[0]))


def _crossed_repeat(grid):
    heights = bar_profile(grid)["heights"]
    n = len(heights)
    return (n >= 4 and len(set(heights)) == n - 1
            and heights.count(heights[0]) == 2
            and any(heights[i] == heights[0] for i in range(2, n - 1)))


def strict_canonical_like(grid):
    return self_check(grid)


SEMANTIC_RIVALS = {
    "nearest_equal_height_association": nearest_equal_height_association,
    "square_canvas": square_canvas,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = {
    **SEMANTIC_RIVALS,
    "colors_left_heights_left": lambda g: _shift_attributes(g, -1, -1),
    "colors_left_heights_fixed": lambda g: _shift_attributes(g, -1, 0),
    "colors_left_heights_right": lambda g: _shift_attributes(g, -1, 1),
    "colors_fixed_heights_left": lambda g: _shift_attributes(g, 0, -1),
    "identity": lambda g: _shift_attributes(g, 0, 0),
    "colors_fixed_heights_right": lambda g: _shift_attributes(g, 0, 1),
    "colors_right_heights_fixed": lambda g: _shift_attributes(g, 1, 0),
    "whole_bars_right": lambda g: _shift_attributes(g, 1, 1),
}
SEMANTIC_WITNESSES = {
    "crossed_repeat": _crossed_repeat,
    "rectangular_canvas": lambda g: len(g) != len(g[0]),
}
WITNESS_RIVALS = {
    "crossed_repeat": ["nearest_equal_height_association"],
    "rectangular_canvas": ["square_canvas"],
}


def lesson_identifiable(demos, query):
    """Finite declared-rival check; not a claim of universal induction."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["a lesson needs labeled demonstrations"]
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return [f"pair {index} must contain input and output"]
        errors = self_check(pair["input"])
        if errors:
            return [f"pair {index}: {error}" for error in errors]
        if rule_mirror(pair["input"]) != pair["output"]:
            return [f"pair {index} label does not match canonical attribute rotation"]
    return [
        f"{name} fits every demonstration but changes the query"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
        and rival(query["input"]) != query["output"]
    ]
