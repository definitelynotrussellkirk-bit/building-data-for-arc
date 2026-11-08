"""Generator for 0c2b397c7f01 — mark tallest and shortest skyline bars.

The input has a zero header row and a bottom-aligned skyline made from one
non-{0, 1, 4, 9} color.  For each column, its height is the contiguous run of
that color rising from the bottom.  Empty columns are ignored when choosing
the minimum.  Paint color 4 above the RIGHTMOST tallest live column and color
9 above the LEFTMOST shortest live column, starting at row 1 and stopping just
before the bar.  The header row is never changed.
"""
from __future__ import annotations

from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0c2b397c7f01"
TASK_ID = "0c2b397c7f01"
VERSION = "3.0.0"
RULE_HASH = "6ce4b6f0d794"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.05

SUMMARY = (
    "A zero header row sits above a bottom-aligned one-color skyline. Count "
    "each contiguous bar upward from the bottom, ignore empty columns for the "
    "minimum, then draw 4 above the RIGHTMOST tallest bar and 9 above the "
    "LEFTMOST shortest live bar. Ordinary four-example lessons always include "
    "a maximum tie, a minimum tie, a zero-column witness, and a unique-extremes "
    "witness; exact linked canonical profiles recur at a controlled rate."
)

INVARIANTS = [
    "grid dimensions are 6..18 in each direction and row 0 is all zero",
    "exactly one bar color outside {0,1,4,9} forms bottom-contiguous columns",
    "at least three live columns exist and tallest and shortest heights differ",
    "the tallest bar leaves at least one paintable cell above it",
    "texture is exactly observable as plain, tie_max, tie_min, or zero_cols",
]

_TEXTURES = ("plain", "tie_max", "tie_min", "zero_cols")
_BAR_COLORS = (2, 3, 5, 6, 7, 8)
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchors at 12; otherwise difficulty-aware 6..18",
        "valid": "6..18",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchors at 12; otherwise difficulty-aware 6..18",
        "valid": "6..18",
    },
    "sky": {
        "type": "int",
        "default": "canonical anchors use 1; zero-column witness uses 0",
        "valid": "0|1",
    },
    "texture": {
        "type": "str",
        "default": "four-step schedule plain|tie_max|tie_min|zero_cols",
        "valid": "plain|tie_max|tie_min|zero_cols",
        "doc": (
            "plain has unique extremes; tie_max has exactly two tallest bars; "
            "tie_min has exactly two shortest live bars; zero_cols has one or "
            "more empty columns and unique live extremes."
        ),
    },
}

# These linked height vectors were extracted from every canonical train and
# held-out test input with the same analyzer used by strict_canonical_like.
# They are input morphology anchors, not answer tables.
_CANONICAL_HEIGHT_PROFILES = (
    (5, 4, 3, 3, 2, 3, 4, 5, 7, 6, 5, 4),
    (1, 2, 3, 2, 2, 3, 4, 5, 4, 3, 4, 5),
    (3, 4, 4, 3, 4, 5, 6, 5, 4, 4, 3, 2),
)
_CANONICAL_HEIGHT_SET = set(_CANONICAL_HEIGHT_PROFILES)

# Every four consecutive default draws visit all four textures.  This is what
# lets lesson_identifiable reject the named tie and zero-column shortcuts for
# every possible four-demo/query start offset.
SCHEDULE_PROFILES = _TEXTURES


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return ("tie_max", "tie_min", "zero_cols", "plain")[sample_index % 4]


def _draw_scheduled_choice(ctx, label, options, scheduled, overrides):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _draw_scheduled_int(ctx, label, lo, hi, scheduled, overrides):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_dimension(ctx, label, difficulty, scheduled, overrides):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, 6, 18)
    if scheduled is not None:
        return ctx.draw_int(label, scheduled, scheduled)
    ranges = {
        "easy": (6, 10),
        "medium": (9, 14),
        "hard": (13, 18),
        None: (8, 16),
    }
    lo, hi = ranges[difficulty]
    return ctx.draw_int(label, lo, hi)


def _paint_input(height, width, heights, bar_color, sky):
    grid = full_grid(height, width, 0)
    for col, bar_height in enumerate(heights):
        for row in range(1, height - bar_height):
            grid[row][col] = sky
        for offset in range(bar_height):
            grid[height - 1 - offset][col] = bar_color
    return grid


def _canonical_profile_for(seed, sample_index, texture):
    # Seed-gate the anchors so a fixed sample_index still has ordinary diversity.
    # Only one draw in five within the two compatible textures is exact, yielding
    # an overall strict-profile rate near 10% without a constant index-0 board.
    key = seed * 1_000_003 + sample_index * 101
    if key % 5 != 0:
        return None
    if texture == "tie_max":
        return _CANONICAL_HEIGHT_PROFILES[1]
    if texture == "plain":
        return _CANONICAL_HEIGHT_PROFILES[0 if (key // 5) % 2 == 0 else 2]
    return None


def _generalized_dimensions(ctx, texture, difficulty, overrides):
    # The zero-column lesson is deliberately a non-canonical size in every
    # band, making fixed-12x12 a falsifiable shortcut in every four-demo block.
    zero_sizes = {
        "easy": (8, 9),
        "medium": (10, 13),
        "hard": (14, 16),
        None: (9, 14),
    }
    scheduled_h = scheduled_w = None
    if texture == "zero_cols" and not any(
        name in overrides and overrides[name] is not None
        for name in ("grid_h", "grid_w")
    ):
        scheduled_h, scheduled_w = zero_sizes[difficulty]
    height = _draw_dimension(
        ctx, "grid_h", difficulty, scheduled_h, overrides
    )
    width = _draw_dimension(
        ctx, "grid_w", difficulty, scheduled_w, overrides
    )
    return height, width


def _generalized_heights(height, width, texture, rng):
    top_height = height - 3
    middle_hi = max(2, top_height - 1)
    heights = [rng.randint(2, middle_hi) for _ in range(width)]

    if texture == "zero_cols":
        zero_count = rng.randint(1, max(1, width // 3))
        for col in rng.sample(range(width), zero_count):
            heights[col] = 0

    live = [col for col, value in enumerate(heights) if value > 0]
    n_top = 2 if texture == "tie_max" else 1
    n_bottom = 2 if texture == "tie_min" else 1
    if len(live) < n_top + n_bottom + 1:
        raise ValueError(
            f"not enough live columns for {texture}: width={width}, live={len(live)}"
        )
    selected = rng.sample(live, n_top + n_bottom)
    for col in selected[:n_top]:
        heights[col] = top_height
    for col in selected[n_top:]:
        heights[col] = 1

    # The middle range excludes both forced extremes, so the multiplicities
    # and therefore the observable texture are exact rather than probabilistic.
    return heights


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled_texture = schedule_profile(seed, sample_index, difficulty)
    texture = _draw_scheduled_choice(
        ctx, "texture", _TEXTURES, scheduled_texture, overrides
    )

    canonical_heights = None
    if not overrides and texture in ("plain", "tie_max"):
        canonical_heights = _canonical_profile_for(seed, sample_index, texture)

    if canonical_heights is not None:
        height = _draw_scheduled_int(ctx, "grid_h", 6, 18, 12, overrides)
        width = _draw_scheduled_int(ctx, "grid_w", 6, 18, 12, overrides)
        sky = _draw_scheduled_choice(ctx, "sky", (0, 1), 1, overrides)
        bar_color = 6
        heights = list(canonical_heights)
    else:
        height, width = _generalized_dimensions(
            ctx, texture, difficulty, overrides
        )
        scheduled_sky = 0 if texture == "zero_cols" else (sample_index % 2)
        sky = _draw_scheduled_choice(
            ctx, "sky", (0, 1), scheduled_sky, overrides
        )
        palette_rng = ctx.draw_rng("palette")
        bar_color = (
            2
            if texture == "zero_cols" and "sky" not in overrides
            else palette_rng.choice(_BAR_COLORS)
        )
        heights = _generalized_heights(
            height, width, texture, ctx.draw_rng("layout")
        )

    grid = _paint_input(height, width, heights, bar_color, sky)
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "sky": sky,
        "texture": texture,
    }
    if observed != expected:
        raise RuntimeError(
            f"constructed grid does not realize keyed axes: {expected} -> {observed}"
        )
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise RuntimeError(f"constructed invalid skyline grid: {errors}")
    return [row[:] for row in grid]


def _analyze(grid):
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return None, ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return None, ["grid is ragged or has zero width"]
    height = len(grid)
    if not (6 <= height <= 18 and 6 <= width <= 18):
        errors.append(f"grid dimensions outside declared grammar: {height}x{width}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return None, errors + ["grid contains a non-integer or color outside 0..9"]
    if any(value != 0 for value in grid[0]):
        errors.append("row 0 must be an all-zero header")

    bar_colors = sorted(
        {value for row in grid for value in row if value not in (0, 1)}
    )
    if len(bar_colors) != 1:
        return None, errors + [
            f"expected exactly one non-0/1 bar color, got {bar_colors}"
        ]
    bar_color = bar_colors[0]
    if bar_color in (4, 9):
        errors.append("input bar color may not collide with output marker colors 4 or 9")

    heights: list[int] = []
    for col in range(width):
        value = 0
        row = height - 1
        while row >= 1 and grid[row][col] == bar_color:
            value += 1
            row -= 1
        heights.append(value)

    sky_values = set()
    for col, bar_height in enumerate(heights):
        bar_top = height - bar_height
        for row in range(1, height):
            value = grid[row][col]
            if row >= bar_top:
                if value != bar_color:
                    errors.append(
                        f"column {col} has a gap/non-bar value at row {row}"
                    )
                    break
            else:
                if value not in (0, 1):
                    errors.append(
                        f"column {col} has non-sky value {value} above its bar"
                    )
                    break
                sky_values.add(value)
    if len(sky_values) != 1:
        errors.append(f"sky must be uniformly 0 or 1 below the header, got {sorted(sky_values)}")
        sky = None
    else:
        sky = next(iter(sky_values))

    live = [value for value in heights if value > 0]
    if len(live) < 3:
        errors.append(f"expected at least three live bars, got {len(live)}")
    if live:
        max_height = max(live)
        min_height = min(live)
        max_count = sum(value == max_height for value in live)
        min_count = sum(value == min_height for value in live)
    else:
        max_height = min_height = max_count = min_count = 0
    if live and max_height == min_height:
        errors.append("tallest and shortest bars must have different heights")
    if max_height > height - 2:
        errors.append("tallest bar must leave at least row 1 paintable above it")

    zero_count = heights.count(0)
    texture = None
    if zero_count:
        if max_count == 1 and min_count == 1:
            texture = "zero_cols"
        else:
            errors.append("zero-column scenes require unique live maximum and minimum")
    elif max_count == 2 and min_count == 1:
        texture = "tie_max"
    elif max_count == 1 and min_count == 2:
        texture = "tie_min"
    elif max_count == 1 and min_count == 1:
        texture = "plain"
    else:
        errors.append(
            "unsupported extreme multiplicities: "
            f"max_count={max_count}, min_count={min_count}, zero_count={zero_count}"
        )

    info = {
        "grid_h": height,
        "grid_w": width,
        "sky": sky,
        "texture": texture,
        "bar_color": bar_color,
        "heights": tuple(heights),
        "live_columns": len(live),
        "zero_columns": zero_count,
        "max_height": max_height,
        "min_height": min_height,
        "max_count": max_count,
        "min_count": min_count,
        "max_columns": tuple(
            col for col, value in enumerate(heights) if value == max_height
        ),
        "min_columns": tuple(
            col for col, value in enumerate(heights)
            if value > 0 and value == min_height
        ),
    }
    return info, errors


def observe_overrides(grid) -> dict[str, object]:
    info, errors = _analyze(grid)
    if info is None or errors:
        raise ValueError("; ".join(errors) or "could not inspect skyline grid")
    return {name: info[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete skyline grammar and any requested exact axes."""
    del difficulty
    info, errors = _analyze(grid)
    if info is None:
        return errors
    requested = None
    if isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        requested = meta["overrides"]
    if requested:
        unknown = set(requested) - set(AXES)
        if unknown:
            errors.append(f"unknown override(s): {sorted(unknown)}")
        if not errors:
            observed = {name: info[name] for name in AXES}
            for axis, expected in requested.items():
                if expected is not None and observed.get(axis) != expected:
                    errors.append(
                        f"requested {axis}={expected!r}, observed {observed.get(axis)!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require one exact empirical canonical input profile."""
    info, errors = _analyze(grid)
    if info is None:
        return errors
    reasons = list(errors)
    if (info["grid_h"], info["grid_w"]) != (12, 12):
        reasons.append("canonical dimensions are exactly 12x12")
    if info["bar_color"] != 6:
        reasons.append("canonical bar color is exactly 6")
    if info["sky"] != 1:
        reasons.append("canonical sky is exactly 1")
    if info["heights"] not in _CANONICAL_HEIGHT_SET:
        reasons.append("height vector is not one of the three linked canonical profiles")
    return reasons


def _solve_policy(
    grid,
    *,
    choose_max: Callable[[tuple[int, ...]], int],
    choose_min: Callable[[tuple[int, ...]], int],
    ignore_zero: bool = True,
):
    info, errors = _analyze(grid)
    if info is None or errors:
        return [row[:] for row in grid]
    heights = info["heights"]
    live_values = tuple(value for value in heights if value > 0)
    max_height = max(live_values)
    min_height = min(live_values) if ignore_zero else min(heights)
    max_columns = tuple(
        col for col, value in enumerate(heights) if value == max_height
    )
    min_columns = tuple(
        col for col, value in enumerate(heights)
        if value == min_height and (not ignore_zero or value > 0)
    )
    max_col = choose_max(max_columns)
    min_col = choose_min(min_columns)
    out = [row[:] for row in grid]
    height = len(grid)
    for row in range(1, height - max_height):
        out[row][max_col] = 4
    for row in range(1, height - min_height):
        out[row][min_col] = 9
    return out


def rule_mirror(grid):
    """Pure Python mirror of the pinned Racket rule for tests and rivals."""
    return _solve_policy(
        grid,
        choose_max=max,
        choose_min=min,
        ignore_zero=True,
    )


def _leftmost_tallest(grid):
    return _solve_policy(grid, choose_max=min, choose_min=min, ignore_zero=True)


def _rightmost_shortest(grid):
    return _solve_policy(grid, choose_max=max, choose_min=max, ignore_zero=True)


def _zero_is_shortest(grid):
    return _solve_policy(grid, choose_max=max, choose_min=min, ignore_zero=False)


def _identity(grid):
    return [row[:] for row in grid]


def _fixed_bar_color_6(grid):
    info, errors = _analyze(grid)
    if info is None or errors or info["bar_color"] != 6:
        return _identity(grid)
    return rule_mirror(grid)


def _fixed_12x12(grid):
    if len(grid) != 12 or len(grid[0]) != 12:
        return _identity(grid)
    return rule_mirror(grid)


def _force_sky_one(grid):
    info, errors = _analyze(grid)
    if info is None or errors:
        return _identity(grid)
    forced = [row[:] for row in grid]
    height = len(grid)
    for col, bar_height in enumerate(info["heights"]):
        for row in range(1, height - bar_height):
            forced[row][col] = 1
    return rule_mirror(forced)


SEMANTIC_RIVALS = {
    "identity": _identity,
    "leftmost_tallest": _leftmost_tallest,
    "rightmost_shortest": _rightmost_shortest,
    "zero_is_shortest": _zero_is_shortest,
    "fixed_bar_color_6": _fixed_bar_color_6,
    "fixed_12x12": _fixed_12x12,
    "force_sky_one": _force_sky_one,
}

LESSON_COMPETITORS = SEMANTIC_RIVALS

CANONICAL_SHORTCUTS = {
    "rightmost_shortest": _rightmost_shortest,
    "zero_is_shortest": _zero_is_shortest,
    "fixed_bar_color_6": _fixed_bar_color_6,
    "fixed_12x12": _fixed_12x12,
    "force_sky_one": _force_sky_one,
}


def _fact(grid, name):
    try:
        info, errors = _analyze(grid)
        return None if info is None or errors else info.get(name)
    except (TypeError, ValueError):
        return None


SEMANTIC_WITNESSES = {
    "canonical_anchor": lambda grid: strict_canonical_like(grid) == [],
    "rightmost_maximum_tie": lambda grid: _fact(grid, "texture") == "tie_max",
    "leftmost_minimum_tie": lambda grid: _fact(grid, "texture") == "tie_min",
    "zero_columns_ignored": lambda grid: _fact(grid, "texture") == "zero_cols",
    "noncanonical_bar_color": lambda grid: _fact(grid, "bar_color") != 6,
    "noncanonical_dimensions": lambda grid: (
        _fact(grid, "grid_h"), _fact(grid, "grid_w")
    ) != (12, 12),
    "zero_sky_preserved": lambda grid: _fact(grid, "sky") == 0,
}

WITNESS_RIVALS = {
    "canonical_anchor": ["identity"],
    "rightmost_maximum_tie": ["leftmost_tallest"],
    "leftmost_minimum_tie": ["rightmost_shortest"],
    "zero_columns_ignored": ["zero_is_shortest"],
    "noncanonical_bar_color": ["fixed_bar_color_6"],
    "noncanonical_dimensions": ["fixed_12x12"],
    "zero_sky_preserved": ["force_sky_one"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named plausible competitor survives its demos."""
    if not isinstance(demos, list) or not demos:
        return ["lesson has no demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query lacks input/output"]

    survivors = set(LESSON_COMPETITORS)
    for demo in demos:
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            return ["a demonstration lacks input/output"]
        survivors = {
            name
            for name in survivors
            if LESSON_COMPETITORS[name](demo["input"]) == demo["output"]
        }
    reasons = []
    for name in sorted(survivors):
        if LESSON_COMPETITORS[name](query["input"]) != query["output"]:
            reasons.append(
                f"shortcut {name!r} fits every demo but changes the query answer"
            )
    return reasons
