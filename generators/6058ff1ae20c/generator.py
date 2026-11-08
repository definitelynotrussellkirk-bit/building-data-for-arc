"""Curriculum generator for task 6058ff1ae20c.

The canonical Racket rule scans non-zero seeds in row-major order.  For each
seed it paints that seed's full column and then its full row on a fresh output
grid.  Later seeds therefore overwrite both intersections with earlier crosses.

The official examples contain one seed, so the teaching schedule deliberately
adds two controlled two-seed cases: same-color composition and distinct-color
row-major precedence.  Every consecutive three-demo window contains all three
profiles.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "6058ff1ae20c"
TASK_ID = "6058ff1ae20c"
VERSION = "2.0.0"
RULE_HASH = "95d2eeca4e5d"

SUMMARY = (
    "Place one seed, two same-color seeds, or two distinct-color seeds in "
    "different rows and columns; the rule paints each seed's full row and "
    "column in row-major fold order."
)

INVARIANTS = [
    "the grid is rectangular and each dimension is between 5 and 12",
    "zero is the background and every cell is an integer ARC color 0 through 9",
    "there are one or two non-zero seeds",
    "two seeds occupy different rows and different columns",
    "the three-slot schedule covers single, same-color pair, and distinct-color precedence",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

SCENE_PROFILES = (
    "single",
    "same_color_pair",
    "ordered_distinct_pair",
)
SCHEDULE_PROFILES = SCENE_PROFILES
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_CANONICAL_SHAPES = ((6, 7), (7, 7), (5, 8), (8, 8))
_DIFFICULTIES = (None, "easy", "medium", "hard")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchor or difficulty-aware 5..12",
        "valid": "5..12",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchor or difficulty-aware 5..12",
        "valid": "5..12",
    },
    "scene_profile": {
        "type": "str",
        "default": "three-slot teaching schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the semantic profile assigned to this lesson slot."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in _DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    for label in ("grid_h", "grid_w"):
        value = overrides.get(label)
        if value is not None and (
            type(value) is not int or not 5 <= value <= 12
        ):
            raise ValueError(f"{label} must be an integer in [5, 12]")

    profile = overrides.get("scene_profile")
    if profile is not None and profile not in SCENE_PROFILES:
        raise ValueError(
            "scene_profile must be one of " + ", ".join(SCENE_PROFILES)
        )


def _seed_cells(grid):
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]


def _analyze(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a non-empty list or tuple"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return None, ["rows must be non-empty lists or tuples"]

    height = len(grid)
    width = len(grid[0])
    errors = []
    if any(len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    if not 5 <= height <= 12 or not 5 <= width <= 12:
        errors.append(
            f"grid dimensions {height}x{width} must both be in [5, 12]"
        )
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return None, errors + ["cells must be integer ARC colors 0 through 9"]

    seeds = _seed_cells(grid)
    if not 1 <= len(seeds) <= 2:
        errors.append(f"expected one or two non-zero seeds, found {len(seeds)}")
        return None, errors

    if len({row for row, _, _ in seeds}) != len(seeds):
        errors.append("two seeds must not share a row")
    if len({col for _, col, _ in seeds}) != len(seeds):
        errors.append("two seeds must not share a column")
    if errors:
        return None, errors

    if len(seeds) == 1:
        profile = "single"
    elif seeds[0][2] == seeds[1][2]:
        profile = "same_color_pair"
    else:
        profile = "ordered_distinct_pair"

    return {
        "grid_h": height,
        "grid_w": width,
        "scene_profile": profile,
        "seeds": seeds,
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return structural errors for the reviewed teaching distribution."""
    del difficulty, meta
    _features, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The reviewed distribution is a strict, executable subset of the rule domain."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, object]:
    """Recover all declared exact axes from one generated input."""
    features, errors = _analyze(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "grid_h": features["grid_h"],
        "grid_w": features["grid_w"],
        "scene_profile": features["scene_profile"],
    }


def _paint_seed_sequence(height, width, seeds):
    output = full_grid(height, width, 0)
    for row, col, value in seeds:
        for target_row in range(height):
            output[target_row][col] = value
        for target_col in range(width):
            output[row][target_col] = value
    return output


def rule_mirror(grid):
    """Independent Python mirror of the canonical row-major Racket fold."""
    features, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid cross lesson: " + "; ".join(errors))
    return _paint_seed_sequence(
        features["grid_h"], features["grid_w"], features["seeds"]
    )


def _first_seed_only(grid):
    height = len(grid)
    width = len(grid[0])
    seeds = _seed_cells(grid)
    return _paint_seed_sequence(height, width, seeds[:1])


def _reverse_seed_order(grid):
    height = len(grid)
    width = len(grid[0])
    return _paint_seed_sequence(height, width, list(reversed(_seed_cells(grid))))


def _reuse_first_seed_color(grid):
    height = len(grid)
    width = len(grid[0])
    seeds = _seed_cells(grid)
    if not seeds:
        return full_grid(height, width, 0)
    first_color = seeds[0][2]
    recolored = [(row, col, first_color) for row, col, _value in seeds]
    return _paint_seed_sequence(height, width, recolored)


def _has_multiple_seeds(grid) -> bool:
    return len(_seed_cells(grid)) == 2


def _has_same_color_pair(grid) -> bool:
    seeds = _seed_cells(grid)
    return len(seeds) == 2 and seeds[0][2] == seeds[1][2]


def _has_distinct_color_pair(grid) -> bool:
    seeds = _seed_cells(grid)
    return len(seeds) == 2 and seeds[0][2] != seeds[1][2]


SEMANTIC_RIVALS = {
    "first_seed_only": _first_seed_only,
    "reverse_seed_order": _reverse_seed_order,
    "reuse_first_seed_color": _reuse_first_seed_color,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "multiple_seed_composition": _has_multiple_seeds,
    "same_color_composition": _has_same_color_pair,
    "row_major_color_precedence": _has_distinct_color_pair,
}
WITNESS_RIVALS = {
    "multiple_seed_composition": ["first_seed_only"],
    "same_color_composition": ["first_seed_only"],
    "row_major_color_precedence": [
        "reverse_seed_order",
        "reuse_first_seed_color",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Name any declared competitor that demos fail to distinguish on query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        fits_demos = all(
            rival(example["input"]) == example["output"] for example in demos
        )
        changes_query = rival(query["input"]) != query["output"]
        if fits_demos and changes_query:
            reasons.append(f"competitor {name!r} fits every demo but changes query")
    return reasons


def _draw_profile(ctx, seed, sample_index, difficulty, overrides):
    if overrides.get("scene_profile") is not None:
        return ctx.draw_choice("scene_profile", SCENE_PROFILES)
    scheduled = schedule_profile(seed, sample_index, difficulty)
    return ctx.draw_choice("scene_profile", (scheduled,))


def _draw_dimensions(ctx, profile, difficulty, overrides):
    if profile == "single":
        shape_rng = ctx.draw_rng(f"canonical_shape:{difficulty or 'mixed'}")
        default_height, default_width = shape_rng.choice(_CANONICAL_SHAPES)
    else:
        default_height = default_width = None

    if overrides.get("grid_h") is not None:
        height = ctx.draw_int("grid_h", 5, 12)
    elif default_height is not None:
        height = ctx.draw_choice("grid_h", (default_height,))
    else:
        height = ctx.draw_int_diff("grid_h", 5, 12)

    if overrides.get("grid_w") is not None:
        width = ctx.draw_int("grid_w", 5, 12)
    elif default_width is not None:
        width = ctx.draw_choice("grid_w", (default_width,))
    else:
        width = ctx.draw_int_diff("grid_w", 5, 12)
    return height, width


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile = _draw_profile(ctx, seed, sample_index, difficulty, overrides)
    height, width = _draw_dimensions(ctx, profile, difficulty, overrides)
    count = 1 if profile == "single" else 2

    position_rng = ctx.draw_rng(
        f"seed_positions:{profile}:{difficulty or 'mixed'}"
    )
    rows = sorted(position_rng.sample(range(height), count))
    cols = position_rng.sample(range(width), count)

    color_rng = ctx.draw_rng(f"seed_colors:{profile}:{difficulty or 'mixed'}")
    palette = list(range(2, 10))
    if profile == "ordered_distinct_pair":
        colors = color_rng.sample(palette, 2)
    else:
        color = color_rng.choice(palette)
        colors = [color] * count

    grid = full_grid(height, width, 0)
    for row, col, color in zip(rows, cols, colors):
        grid[row][col] = color

    errors = self_check(grid)
    if errors:
        raise ValueError("internal layout violated self_check: " + "; ".join(errors))
    return grid
