"""Lawful input sampler for task 1a92a12bac06.

The selected Racket authority finds each 4-connected red (2) object, measures
its vertical extent, and recolors the object's bottom ``floor(height / 2)``
rows cyan (8).  This sampler deliberately keeps every red object a separated,
one-cell-wide vertical bar, matching the canonical task domain, while varying
where bars are anchored so the canonical "all bars touch the floor" shortcut
is not sufficient.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1a92a12bac06"
TASK_ID = GENERATOR_ID
RULE_HASH = "6d628a0b1a7d"
VERSION = "3.0.0"
SUMMARY = (
    "A 0-background grid contains 3-4 separated red(2) vertical bars. "
    "For each bar independently, the bottom floor(height/2) cells become "
    "cyan(8). Bars vary in height and can be bottom-aligned, top-aligned, "
    "floating, or mixed-anchor; output shape is unchanged."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

TEXTURES = (
    "bottom_aligned",
    "floating",
    "mixed_anchors",
    "top_aligned",
)
SCHEDULE_PROFILES = TEXTURES
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-skewed; canonical pulse", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "difficulty-skewed; canonical pulse", "valid": "9..13"},
    "n_bars": {"type": "int", "default": "3..4; canonical pulse uses 4", "valid": "3..4"},
    "texture": {"type": "str", "default": "4-step teaching schedule", "valid": "|".join(TEXTURES)},
}

INVARIANTS = [
    "background is 0 and the only input foreground color is red(2)",
    "3-4 red components are contiguous one-column bars in distinct nonadjacent interior columns",
    "every bar has height 2..grid_h-1; each grid contains both odd and even bar heights",
    "texture exactly describes bottom, top, floating, or mixed top/bottom/floating anchoring",
    "every default four-instance schedule contains one canonical-profile example and three off-floor witnesses",
]

_CANONICAL_HEIGHTS = (7, 8, 9, 11)
_BANDS = {
    None: ((7, 14), (9, 13), (3, 4)),
    "easy": ((7, 11), (9, 11), (3, 4)),
    "medium": ((8, 13), (9, 13), (3, 4)),
    "hard": ((10, 14), (10, 13), (3, 4)),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """The default four-step lesson schedule; independent of Python hashing."""
    del seed, difficulty
    return TEXTURES[int(sample_index) % len(TEXTURES)]


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if type(sample_index) is not int:
        raise TypeError(
            "sample_index must be an integer (not bool, float, or string)"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    _validate_overrides(overrides)


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "n_bars"):
        if name in overrides and overrides[name] is not None and type(overrides[name]) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
    bounds = {"grid_h": (7, 14), "grid_w": (9, 13), "n_bars": (3, 4)}
    for name, (lo, hi) in bounds.items():
        value = overrides.get(name)
        if value is not None and not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
    if "texture" in overrides and overrides["texture"] is not None:
        value = overrides["texture"]
        if type(value) is not str:
            raise TypeError("texture must be a string")
        if value not in TEXTURES:
            raise ValueError(f"texture={value!r} not in {TEXTURES}")


def _draw_int_axis(ctx, overrides, name, lo, hi, default_lo, default_hi):
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int(name, default_lo, default_hi)


def _draw_choice_axis(ctx, overrides, name, options, default):
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    # A singleton choice records the realized exact axis without consuming an
    # unrelated random branch or rejecting any explicit override.
    return ctx.draw_choice(name, (default,))


def _column_sets(width, count):
    return tuple(
        cols
        for cols in combinations(range(1, width - 1), count)
        if all(b - a >= 2 for a, b in zip(cols, cols[1:]))
    )


def _heights(ctx, grid_h, count, *, canonical_pulse, texture):
    max_height = grid_h - 1 if texture == "bottom_aligned" else grid_h - 2
    min_height = 2 if canonical_pulse else max(4, grid_h // 2)
    legal = list(range(min_height, max_height + 1))
    odd = [value for value in legal if value % 2]
    even = [value for value in legal if value % 2 == 0]
    if not odd or not even:
        raise ValueError("grid height cannot realize both odd and even lawful bars")
    rng = ctx.draw_rng("bar_heights")
    values = [rng.choice(odd), rng.choice(even)]
    values.extend(rng.choice(legal) for _ in range(count - 2))
    rng.shuffle(values)
    return values


def _tops(ctx, grid_h, heights, texture):
    rng = ctx.draw_rng("bar_positions")

    def floating_top(height):
        return rng.randint(1, grid_h - height - 1)

    if texture == "bottom_aligned":
        return [grid_h - height for height in heights]
    if texture == "top_aligned":
        return [0 for _ in heights]
    if texture == "floating":
        return [floating_top(height) for height in heights]
    if texture == "mixed_anchors":
        roles = ["bottom", "top"] + ["floating"] * (len(heights) - 2)
        rng.shuffle(roles)
        tops = []
        for role, height in zip(roles, heights):
            if role == "bottom":
                tops.append(grid_h - height)
            elif role == "top":
                tops.append(0)
            else:
                tops.append(floating_top(height))
        return tops
    raise ValueError(f"unknown texture: {texture}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
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
    canonical_pulse = profile == "bottom_aligned" and not overrides

    if canonical_pulse:
        grid_h = _draw_choice_axis(ctx, overrides, "grid_h", tuple(range(7, 15)), ctx.draw_rng("canonical_height").choice(_CANONICAL_HEIGHTS))
        grid_w = _draw_choice_axis(ctx, overrides, "grid_w", tuple(range(9, 14)), 9)
        n_bars = _draw_choice_axis(ctx, overrides, "n_bars", (3, 4), 4)
    else:
        h_band, w_band, n_band = _BANDS.get(difficulty, _BANDS[None])
        grid_h = _draw_int_axis(ctx, overrides, "grid_h", 7, 14, *h_band)
        grid_w = _draw_int_axis(ctx, overrides, "grid_w", 9, 13, *w_band)
        n_bars = _draw_int_axis(ctx, overrides, "n_bars", 3, 4, *n_band)
    texture = _draw_choice_axis(ctx, overrides, "texture", TEXTURES, profile)

    choices = _column_sets(grid_w, n_bars)
    if not choices:
        raise ValueError(f"grid_w={grid_w} cannot fit {n_bars} separated interior bars")
    columns = (1, 3, 5, 7) if canonical_pulse else ctx.draw_rng("bar_columns").choice(choices)
    heights = _heights(ctx, grid_h, n_bars, canonical_pulse=canonical_pulse, texture=texture)
    tops = _tops(ctx, grid_h, heights, texture)

    grid = full_grid(grid_h, grid_w, 0)
    for col, top, height in zip(columns, tops, heights):
        for row in range(top, top + height):
            grid[row][col] = 2
    return grid


def _components_of_color(grid, color=2):
    height, width = len(grid), len(grid[0])
    pending = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    parts = []
    while pending:
        start = min(pending)
        pending.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            row, col = stack.pop()
            for nxt in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if nxt in pending:
                    pending.remove(nxt)
                    cells.add(nxt)
                    stack.append(nxt)
        parts.append(cells)
    return sorted(parts, key=lambda part: (min(col for _, col in part), min(part)))


def _bar_facts(grid):
    parts = _components_of_color(grid, 2)
    facts = []
    for part in parts:
        rows = [row for row, _ in part]
        cols = {col for _, col in part}
        facts.append(
            {
                "part": part,
                "top": min(rows),
                "bottom": max(rows),
                "height": max(rows) - min(rows) + 1,
                "columns": cols,
            }
        )
    return facts


def _classify_texture(grid, facts=None):
    facts = _bar_facts(grid) if facts is None else facts
    height = len(grid)
    if facts and all(fact["bottom"] == height - 1 for fact in facts):
        return "bottom_aligned"
    if facts and all(fact["top"] == 0 for fact in facts):
        return "top_aligned"
    if facts and all(fact["top"] > 0 and fact["bottom"] < height - 1 for fact in facts):
        return "floating"
    if (
        facts
        and any(fact["top"] == 0 for fact in facts)
        and any(fact["bottom"] == height - 1 for fact in facts)
        and any(fact["top"] > 0 and fact["bottom"] < height - 1 for fact in facts)
    ):
        return "mixed_anchors"
    return None


def observe_overrides(grid):
    facts = _bar_facts(grid)
    texture = _classify_texture(grid, facts)
    if texture is None:
        raise ValueError("grid does not have a declared texture")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_bars": len(facts),
        "texture": texture,
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or value not in (0, 2) for row in grid for value in row):
        return ["input cells must be integer colors 0 or 2"]

    height = len(grid)
    errors = []
    if not 7 <= height <= 14:
        errors.append(f"grid_h={height} outside [7,14]")
    if not 9 <= width <= 13:
        errors.append(f"grid_w={width} outside [9,13]")

    facts = _bar_facts(grid)
    if not 3 <= len(facts) <= 4:
        errors.append(f"expected 3-4 red bars, found {len(facts)}")
    columns = []
    heights = []
    for fact in facts:
        if len(fact["columns"]) != 1:
            errors.append("each red component must occupy exactly one column")
            continue
        col = next(iter(fact["columns"]))
        columns.append(col)
        heights.append(fact["height"])
        if not 1 <= col < width - 1:
            errors.append("bars must use interior columns")
        if len(fact["part"]) != fact["height"]:
            errors.append("bar cells must be vertically contiguous")
        if not 2 <= fact["height"] <= height - 1:
            errors.append(f"bar height {fact['height']} outside [2,{height - 1}]")
    if any(b - a < 2 for a, b in zip(sorted(columns), sorted(columns)[1:])):
        errors.append("bars must have at least one zero column between them")
    if heights and not any(value % 2 for value in heights):
        errors.append("at least one odd-height bar is required")
    if heights and not any(value % 2 == 0 for value in heights):
        errors.append("at least one even-height bar is required")
    if facts and _classify_texture(grid, facts) not in TEXTURES:
        errors.append("bar anchors do not match a declared texture")
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    facts = _bar_facts(grid)
    columns = [next(iter(fact["columns"])) for fact in facts]
    strict = []
    if len(grid) not in _CANONICAL_HEIGHTS:
        strict.append("canonical height must be one of 7,8,9,11")
    if len(grid[0]) != 9:
        strict.append("canonical width is 9")
    if len(facts) != 4 or columns != [1, 3, 5, 7]:
        strict.append("canonical profile has four bars in columns 1,3,5,7")
    if any(fact["bottom"] != len(grid) - 1 for fact in facts):
        strict.append("canonical bars are bottom-aligned")
    return strict


def _grid_bottom_anchor_rival(grid):
    """Wrong shortcut: measure each half-fill upward from the canvas floor."""
    output = deepcopy(grid)
    canvas_height = len(grid)
    for fact in _bar_facts(grid):
        cyan_start = canvas_height - (fact["height"] // 2)
        for row, col in fact["part"]:
            if row >= cyan_start:
                output[row][col] = 8
    return output


def _ceil_half_rival(grid):
    """Wrong shortcut: color ceil(height/2) cells instead of floor(height/2)."""
    output = deepcopy(grid)
    for fact in _bar_facts(grid):
        cyan_start = fact["bottom"] - ((fact["height"] + 1) // 2) + 1
        for row, col in fact["part"]:
            if row >= cyan_start:
                output[row][col] = 8
    return output


def _has_off_bottom(grid):
    return any(fact["bottom"] < len(grid) - 1 for fact in _bar_facts(grid))


def _has_odd_height(grid):
    return any(fact["height"] % 2 for fact in _bar_facts(grid))


def lesson_identifiable(demos, query):
    del query
    reasons = []
    inputs = [pair.get("input") for pair in demos if isinstance(pair, dict)]
    if not inputs or not any(_has_off_bottom(grid) for grid in inputs):
        reasons.append("demonstrations do not refute measuring from the grid bottom")
    if not inputs or not any(_has_odd_height(grid) for grid in inputs):
        reasons.append("demonstrations do not distinguish floor(height/2) from ceil(height/2)")
    return reasons


SEMANTIC_WITNESSES = {
    "off_bottom": _has_off_bottom,
    "odd_height": _has_odd_height,
}
SEMANTIC_RIVALS = {
    "grid_bottom_anchor": _grid_bottom_anchor_rival,
    "ceil_half": _ceil_half_rival,
}
WITNESS_RIVALS = {
    "off_bottom": ["grid_bottom_anchor"],
    "odd_height": ["ceil_half"],
}
CANONICAL_SHORTCUTS = {
    "grid_bottom_anchor": _grid_bottom_anchor_rival,
}
LESSON_COMPETITORS = {
    "grid_bottom_anchor": _grid_bottom_anchor_rival,
    "ceil_half": _ceil_half_rival,
}
