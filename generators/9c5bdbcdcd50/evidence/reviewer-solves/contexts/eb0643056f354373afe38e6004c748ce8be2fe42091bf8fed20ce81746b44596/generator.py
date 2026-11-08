"""Semantic generator for ARC task 9c5bdbcdcd50 (source e9c9d9a1).

Color 3 forms complete horizontal and vertical divider lines.  Treat the
rectangles between those lines as a region matrix.  Fill its four extreme
corner regions with 2, 4, 1, and 8 (clockwise from top-left); fill strict
interior regions with 7; leave non-corner edge regions 0; preserve dividers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "9c5bdbcdcd50"
TASK_ID = "9c5bdbcdcd50"
VERSION = "3.0.0"
RULE_HASH = "c2cf9830b316"
SUMMARY = "Fill the corner, edge, and interior regions of a color-3 divider lattice by their matrix position."
INVARIANTS = [
    "calibrated inputs contain only background 0 and full color-3 divider lines",
    "every divider-bounded row and column region is nonempty",
    "extreme corners become 2, 4, 1, and 8 in reading order",
    "strict interior regions become 7 while non-corner edge regions stay 0",
    "divider cells remain color 3",
]

PUBLIC_PROFILES = ("public_3x3", "public_4x3", "public_5x5", "public_4x4")
GENERAL_PROFILES = ("wide_3x6", "tall_6x3", "mixed_5x4", "dense_6x6")
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four complete official lattice topologies plus four controlled extrapolations",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PROFILE_SHAPES = {
    "public_3x3": (3, 3),
    "public_4x3": (4, 3),
    "public_5x5": (5, 5),
    "public_4x4": (4, 4),
    "wide_3x6": (3, 6),
    "tall_6x3": (6, 3),
    "mixed_5x4": (5, 4),
    "dense_6x6": (6, 6),
}

_PUBLIC_ROWS = {
    "public_3x3": (
        "000300030000", "000300030000", "000300030000", "333333333333",
        "000300030000", "000300030000", "000300030000", "000300030000",
        "000300030000", "000300030000", "333333333333", "000300030000",
        "000300030000", "000300030000", "000300030000",
    ),
    "public_4x3": (
        "000300300000", "000300300000", "000300300000", "000300300000",
        "333333333333", "000300300000", "000300300000", "333333333333",
        "000300300000", "000300300000", "000300300000", "000300300000",
        "333333333333", "000300300000", "000300300000", "000300300000",
        "000300300000", "000300300000", "000300300000",
    ),
    "public_5x5": (
        "0003000300030030", "0003000300030030", "3333333333333333",
        "0003000300030030", "0003000300030030", "0003000300030030",
        "0003000300030030", "3333333333333333", "0003000300030030",
        "0003000300030030", "3333333333333333", "0003000300030030",
        "0003000300030030", "3333333333333333", "0003000300030030",
        "0003000300030030", "0003000300030030", "0003000300030030",
    ),
    "public_4x4": (
        "003000300300000", "003000300300000", "003000300300000",
        "333333333333333", "003000300300000", "003000300300000",
        "003000300300000", "333333333333333", "003000300300000",
        "003000300300000", "333333333333333", "003000300300000",
        "003000300300000", "003000300300000", "003000300300000",
    ),
}
_PUBLIC_INPUTS = {
    profile: [[int(value) for value in row] for row in rows]
    for profile, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_SIGNATURES = {
    tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()
}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        return ["input must contain one through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 1 <= len(grid[0]) <= 30:
        return ["input must contain one through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _full_dividers(grid):
    height, width = len(grid), len(grid[0])
    rows = [row for row in range(height) if all(grid[row][col] == 3 for col in range(width))]
    cols = [col for col in range(width) if all(grid[row][col] == 3 for row in range(height))]
    return rows, cols


def _ranges(dividers, length):
    bounds = [-1] + list(dividers) + [length]
    return [
        (bounds[index] + 1, bounds[index + 1] - 1)
        for index in range(len(bounds) - 1)
        if bounds[index] + 1 <= bounds[index + 1] - 1
    ]


def rule_mirror(grid):
    """Broad, input-pure mirror of the canonical Racket program."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height, width = len(grid), len(grid[0])
    divider_rows, divider_cols = _full_dividers(grid)
    row_ranges = _ranges(divider_rows, height)
    col_ranges = _ranges(divider_cols, width)
    result = [list(row) for row in grid]
    row_count, col_count = len(row_ranges), len(col_ranges)
    for row_index, (row0, row1) in enumerate(row_ranges):
        for col_index, (col0, col1) in enumerate(col_ranges):
            if row_index == 0 and col_index == 0:
                color = 2
            elif row_index == 0 and col_index == col_count - 1:
                color = 4
            elif row_index == row_count - 1 and col_index == 0:
                color = 1
            elif row_index == row_count - 1 and col_index == col_count - 1:
                color = 8
            elif 0 < row_index < row_count - 1 and 0 < col_index < col_count - 1:
                color = 7
            else:
                color = 0
            for row in range(row0, row1 + 1):
                for col in range(col0, col1 + 1):
                    result[row][col] = color
    return result


def _facts(grid):
    divider_rows, divider_cols = _full_dividers(grid)
    row_ranges = _ranges(divider_rows, len(grid))
    col_ranges = _ranges(divider_cols, len(grid[0]))
    return {
        "divider_rows": divider_rows,
        "divider_cols": divider_cols,
        "row_ranges": row_ranges,
        "col_ranges": col_ranges,
        "row_bands": [end - start + 1 for start, end in row_ranges],
        "col_bands": [end - start + 1 for start, end in col_ranges],
        "region_shape": (len(row_ranges), len(col_ranges)),
    }


def canonical_profile_signature(grid):
    try:
        return _PUBLIC_SIGNATURES.get(tuple(tuple(row) for row in grid))
    except TypeError:
        return None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}
    height, width = len(grid), len(grid[0])
    facts = _facts(grid)
    divider_rows = facts["divider_rows"]
    divider_cols = facts["divider_cols"]
    if not 5 <= height <= 30 or not 5 <= width <= 30:
        errors.append("calibrated lattice dimensions must be five through thirty")
    if any(value not in (0, 3) for row in grid for value in row):
        errors.append("calibrated input palette must be exactly background 0 and divider color 3")
    if not divider_rows or not divider_cols:
        errors.append("both horizontal and vertical divider families are required")
    if divider_rows and (
        divider_rows[0] == 0
        or divider_rows[-1] == height - 1
        or any(right - left == 1 for left, right in zip(divider_rows, divider_rows[1:]))
    ):
        errors.append("horizontal divider lines must be internal and separated by nonempty bands")
    if divider_cols and (
        divider_cols[0] == 0
        or divider_cols[-1] == width - 1
        or any(right - left == 1 for left, right in zip(divider_cols, divider_cols[1:]))
    ):
        errors.append("vertical divider lines must be internal and separated by nonempty bands")
    divider_cells = {
        (row, col)
        for row in range(height) for col in range(width)
        if row in divider_rows or col in divider_cols
    }
    actual_threes = {
        (row, col)
        for row in range(height) for col in range(width)
        if grid[row][col] == 3
    }
    if actual_threes != divider_cells:
        errors.append("every color-3 cell must belong to a complete divider row or column")
    if any(not 1 <= size <= 6 for size in facts["row_bands"] + facts["col_bands"]):
        errors.append("each calibrated region band must be one through six cells wide")
    profile = next(
        (name for name, shape in _PROFILE_SHAPES.items() if shape == facts["region_shape"]),
        None,
    )
    if profile is None:
        errors.append(f"unsupported calibrated region topology {facts['region_shape']!r}")
    output = rule_mirror(grid)
    expected_colors = {0, 1, 2, 3, 4, 7, 8}
    if not errors and {value for row in output for value in row} != expected_colors:
        errors.append("calibrated output must visibly witness corners, edges, interior, and dividers")
    return {
        "errors": errors,
        "scene_profile": profile if not errors else None,
        "facts": facts,
        "output": output,
    }


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    return analysis["scene_profile"] if not analysis["errors"] else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)["errors"]


def _draw_bands(count, difficulty, rng):
    if difficulty == "easy":
        low, high = 1, 4
    elif difficulty == "hard":
        low, high = 2, 6
    else:
        low, high = 1, 5
    for _ in range(200):
        bands = [rng.randint(low, high) for _ in range(count)]
        if sum(bands) + count - 1 <= 30:
            return bands
    raise AssertionError("could not draw bounded divider bands")


def _lattice(row_bands, col_bands):
    height = sum(row_bands) + len(row_bands) - 1
    width = sum(col_bands) + len(col_bands) - 1
    grid = [[0] * width for _ in range(height)]
    divider_rows = []
    cursor = row_bands[0]
    for band in row_bands[1:]:
        divider_rows.append(cursor)
        cursor += 1 + band
    divider_cols = []
    cursor = col_bands[0]
    for band in col_bands[1:]:
        divider_cols.append(cursor)
        cursor += 1 + band
    for row in divider_rows:
        grid[row] = [3] * width
    for col in divider_cols:
        for row in range(height):
            grid[row][col] = 3
    return grid


def _random_scene(profile, difficulty, rng):
    row_count, col_count = _PROFILE_SHAPES[profile]
    minimum_canvas = {"easy": 8, "medium": 9, "hard": 10}.get(difficulty, 8)
    for _ in range(200):
        grid = _lattice(
            _draw_bands(row_count, difficulty, rng),
            _draw_bands(col_count, difficulty, rng),
        )
        if len(grid) < minimum_canvas or len(grid[0]) < minimum_canvas:
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct lattice profile {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice(
        "scene_profile",
        list(PUBLIC_PROFILES) * 3 + list(GENERAL_PROFILES) * 2,
    )
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES and overrides.get("scene_profile") is not None:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    grid = _random_scene(profile, difficulty, ctx.draw_rng("lattice"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid divider-lattice lesson: " + "; ".join(errors))
    return grid
