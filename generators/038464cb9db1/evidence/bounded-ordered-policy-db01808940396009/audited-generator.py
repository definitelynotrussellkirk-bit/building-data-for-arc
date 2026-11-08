"""Semantic generator for ARC task 3cd86f4f / 038464cb9db1.

The output is a diagonal row shear.  For an ``h x w`` input, row ``r`` is
copied intact starting at column ``h - 1 - r`` in an ``h x (w + h - 1)``
zero canvas.  Thus the bottom row is anchored at column zero and each row
above it starts one column farther right.

The teaching schedule deliberately interleaves the six public
``(height, width, palette-size)`` profiles with two lawful extrapolations.
Every four consecutive samples contain a narrow tall grid, a two-row grid,
a non-square grid, and multiple heights, so a materialized lesson refutes
identity, opposite-direction shear, constant alignment, and width-controlled
expansion shortcuts.
"""
from __future__ import annotations

from math import ceil
from typing import Any, Callable

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "038464cb9db1"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "608d74db8ac9"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.70

SUMMARY = (
    "Copy every input row into a zero canvas of width w+h-1. Row r begins "
    "at column h-1-r, so the bottom row stays at the left edge, the top row "
    "moves farthest right, and adjacent rows form a one-column staircase."
)

INVARIANTS = [
    "input is a 2..15 by 1..15 rectangular ARC grid",
    "input contains no zero because zero is reserved for output padding",
    "four through nine nonzero colors appear and every declared color is used",
    "h+w-1 is at most 29, so the sheared output remains within ARC bounds",
    "every four consecutive scheduled samples vary height and width and include narrow and two-row controls",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "eight-profile schedule with canonical anchors",
        "valid": "2..15",
    },
    "grid_w": {
        "type": "int",
        "default": "eight-profile schedule with canonical anchors",
        "valid": "1..15",
    },
    "palette_size": {
        "type": "int",
        "default": "canonical 4/5 or difficulty-aware 4..9",
        "valid": "4..9",
    },
}

# A 2x1 grid has only two cells and cannot realize the minimum four-color
# teaching palette.  All other boundary combinations are constructive.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"grid_h": 2, "grid_w": 1},
]

SCHEDULE_PROFILES = tuple(range(8))

# Every public input uses one of these exact (height, width, palette-size)
# profiles.  The schedule emits all six in every difficulty band.
_CANONICAL_PROFILES = {
    (4, 9, 4),
    (6, 6, 5),
    (7, 4, 4),
    (4, 1, 4),
    (10, 2, 5),
    (2, 4, 5),
}

# Slots 0/4 are narrow and slots 1/5 are two-row controls.  Therefore every
# cyclic window of four consecutive samples contains both decisive controls.
_FIXED_PROFILES = {
    0: (4, 1, 4),
    1: (2, 4, 5),
    2: (6, 6, 5),
    3: (7, 4, 4),
    4: (10, 2, 5),
    5: (2, 9, 4),
    6: (4, 9, 4),
}


def schedule_profile(
    seed: int, sample_index: int, difficulty: str | None = None
) -> int:
    """Expose the deterministic eight-slot lesson schedule."""
    del seed, difficulty
    return int(sample_index) % 8


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(
        "difficulty must be None, 'easy', 'medium', or 'hard'"
    )


def _profile_defaults(sample_index: int, band: str) -> tuple[int, int, int]:
    profile = sample_index % 8
    if profile in _FIXED_PROFILES:
        return _FIXED_PROFILES[profile]
    return {
        "easy": (3, 5, 4),
        "medium": (8, 5, 6),
        "hard": (14, 15, 9),
    }[band]


def _incompatible(message: str, *axes: str) -> None:
    exc = ValueError(message)
    exc.incompatible_axes = tuple(axes)
    raise exc


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(
            f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}"
        )
    for name, lo, hi in (
        ("grid_h", 2, 15),
        ("grid_w", 1, 15),
        ("palette_size", 4, 9),
    ):
        value = overrides.get(name)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
    return band


def _resolved_axes(ctx, sample_index: int, band: str, overrides: dict[str, Any]):
    base_h, base_w, base_palette = _profile_defaults(sample_index, band)

    height = (
        ctx.draw_int("grid_h", 2, 15)
        if "grid_h" in overrides and overrides["grid_h"] is not None
        else base_h
    )
    width = (
        ctx.draw_int("grid_w", 1, 15)
        if "grid_w" in overrides and overrides["grid_w"] is not None
        else base_w
    )
    palette_size = (
        ctx.draw_int("palette_size", 4, 9)
        if "palette_size" in overrides
        and overrides["palette_size"] is not None
        else base_palette
    )

    # Preserve every explicit request.  Only unspecified dimensions may grow
    # to make room for an explicitly requested palette.
    if height * width < palette_size:
        if "grid_w" not in overrides or overrides.get("grid_w") is None:
            width = max(width, ceil(palette_size / height))
        elif "grid_h" not in overrides or overrides.get("grid_h") is None:
            height = max(height, ceil(palette_size / width))
        else:
            _incompatible(
                "grid_h * grid_w must have at least palette_size cells",
                "grid_h",
                "grid_w",
                "palette_size",
            )
    if height > 15 or width > 15 or height * width < palette_size:
        _incompatible(
            "requested dimensions cannot realize the requested palette_size",
            "grid_h",
            "grid_w",
            "palette_size",
        )

    # Record scheduled/adjusted defaults through GenCtx as exact keyed draws so
    # ordinary-path provenance can be compared with the returned grid.
    if "grid_h" not in overrides or overrides.get("grid_h") is None:
        height = ctx.draw_int("grid_h", height, height)
    if "grid_w" not in overrides or overrides.get("grid_w") is None:
        width = ctx.draw_int("grid_w", width, width)
    if "palette_size" not in overrides or overrides.get("palette_size") is None:
        palette_size = ctx.draw_int(
            "palette_size", palette_size, palette_size
        )
    return height, width, palette_size


def _draw_grid(
    height: int,
    width: int,
    palette: tuple[int, ...],
    rng,
) -> list[list[int]]:
    """Use every palette color, then fill the remaining cells deterministically."""
    positions = [
        (row, col)
        for row in range(height)
        for col in range(width)
    ]
    rng.shuffle(positions)
    values = list(palette)
    values.extend(
        rng.choice(palette)
        for _ in range(height * width - len(palette))
    )
    rng.shuffle(values)
    grid = [[palette[0] for _ in range(width)] for _ in range(height)]
    for (row, col), value in zip(positions, values):
        grid[row][col] = value
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    height, width, palette_size = _resolved_axes(
        ctx, sample_index, band, overrides
    )
    palette = ctx.draw_distinct_colors(
        "palette", n=palette_size, exclude=(0,)
    )
    return _draw_grid(height, width, palette, ctx.draw_rng("cells"))


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {}, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {}, ["grid rows must be non-empty sequences"]
    height = len(grid)
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return {}, ["grid must be rectangular"]
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 9
            ):
                errors.append(
                    f"cell ({row_index},{col_index}) must be an ARC integer 0..9"
                )
                return {}, errors
    palette = {value for row in grid for value in row}
    if not 2 <= height <= 15:
        errors.append(f"height must be in 2..15, found {height}")
    if not 1 <= width <= 15:
        errors.append(f"width must be in 1..15, found {width}")
    if height + width - 1 > 30:
        errors.append("sheared output width would exceed 30")
    if 0 in palette:
        errors.append("zero is reserved for output padding and may not appear in input")
    if not 4 <= len(palette) <= 9:
        errors.append(
            f"input must use four through nine nonzero colors, found {len(palette)}"
        )
    return {
        "grid_h": height,
        "grid_w": width,
        "palette_size": len(palette),
        "palette": tuple(sorted(palette)),
    }, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task's lawful, shortcut-resistant input grammar."""
    del difficulty, meta
    return _analyse(grid)[1]


def strict_canonical_like(grid) -> list[str]:
    """Accept exactly the six public dimension/palette profiles."""
    info, errors = _analyse(grid)
    if errors:
        return errors
    profile = (
        info["grid_h"],
        info["grid_w"],
        info["palette_size"],
    )
    if profile not in _CANONICAL_PROFILES:
        return [f"profile {profile} is outside the six canonical profiles"]
    return []


def observe_overrides(grid) -> dict[str, int]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    return {name: int(info[name]) for name in AXES}


def _shear(
    grid: Any,
    offsets: list[int],
    output_width: int,
) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(output_width)] for _ in range(height)]
    for row in range(height):
        for col in range(width):
            target = offsets[row] + col
            if 0 <= target < output_width:
                output[row][target] = int(grid[row][col])
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror; canonical Racket remains output authority."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("invalid shear input: " + "; ".join(errors))
    height = info["grid_h"]
    width = info["grid_w"]
    return _shear(
        grid,
        [height - 1 - row for row in range(height)],
        width + height - 1,
    )


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_opposite_shear(grid):
    height = len(grid)
    width = len(grid[0])
    return _shear(grid, list(range(height)), width + height - 1)


def _rival_all_rows_right_aligned(grid):
    height = len(grid)
    width = len(grid[0])
    return _shear(grid, [height - 1] * height, width + height - 1)


def _rival_nonbottom_rows_same_shift(grid):
    height = len(grid)
    width = len(grid[0])
    offsets = [height - 1] * max(0, height - 1) + [0]
    return _shear(grid, offsets, width + height - 1)


def _rival_width_controls_expansion(grid):
    height = len(grid)
    width = len(grid[0])
    offsets = [max(0, width - 1 - row) for row in range(height)]
    return _shear(grid, offsets, width + width - 1)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "identity_no_shear": _rival_identity,
    "top_anchored_opposite_shear": _rival_opposite_shear,
    "all_rows_right_aligned": _rival_all_rows_right_aligned,
    "only_bottom_row_has_distinct_shift": _rival_nonbottom_rows_same_shift,
    "width_controls_expansion": _rival_width_controls_expansion,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _valid_info(grid) -> dict[str, Any] | None:
    info, errors = _analyse(grid)
    return None if errors else info


def _witness_identity_and_direction(grid) -> bool:
    return _valid_info(grid) is not None


def _witness_intermediate_staircase(grid) -> bool:
    info = _valid_info(grid)
    return info is not None and info["grid_h"] >= 3


def _witness_height_controls_width(grid) -> bool:
    info = _valid_info(grid)
    return info is not None and info["grid_h"] != info["grid_w"]


SEMANTIC_WITNESSES = {
    "nonzero_rows_make_identity_and_opposite_direction_observable": (
        _witness_identity_and_direction
    ),
    "intermediate_rows_require_unit_staircase": _witness_intermediate_staircase,
    "non_square_profiles_show_height_controls_expansion": (
        _witness_height_controls_width
    ),
}

WITNESS_RIVALS = {
    "nonzero_rows_make_identity_and_opposite_direction_observable": [
        "identity_no_shear",
        "top_anchored_opposite_shear",
        "all_rows_right_aligned",
    ],
    "intermediate_rows_require_unit_staircase": [
        "only_bottom_row_has_distinct_shift"
    ],
    "non_square_profiles_show_height_controls_expansion": [
        "width_controls_expansion"
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require exact demos that collectively refute every named rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    heights: set[int] = set()
    widths: set[int] = set()
    has_narrow = False
    has_two_rows = False
    has_non_square = False
    refuted = {name: False for name in LESSON_COMPETITORS}

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
            reasons.append(f"demo {index} must contain input and output")
            continue
        info, errors = _analyse(pair["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output is not the exact row shear")
        heights.add(info["grid_h"])
        widths.add(info["grid_w"])
        has_narrow = has_narrow or info["grid_w"] <= 2
        has_two_rows = has_two_rows or info["grid_h"] == 2
        has_non_square = has_non_square or info["grid_h"] != info["grid_w"]
        for name, rival in LESSON_COMPETITORS.items():
            refuted[name] = refuted[name] or rival(pair["input"]) != expected

    if len(heights) < 2:
        reasons.append("demonstrations must vary input height")
    if len(widths) < 2:
        reasons.append("demonstrations must vary input width")
    if not has_narrow:
        reasons.append("demonstrations need a width-1 or width-2 control")
    if not has_two_rows:
        reasons.append("demonstrations need a two-row boundary case")
    if not has_non_square:
        reasons.append("demonstrations need a non-square control")
    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute rival {name}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            reasons.append(f"query input invalid: {query_errors[0]}")
    return reasons
