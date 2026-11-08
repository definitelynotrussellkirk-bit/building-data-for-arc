"""Generator for periodic self-tiling task fcac68386147.

For an ``n x n`` input, repeat the complete input tile ``n`` times across
and ``n`` times down, producing an ``n² x n²`` output.
"""
from __future__ import annotations

import math

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "fcac68386147"
VERSION = "2.0.0"
TASK_ID = "fcac68386147"
RULE_HASH = "350a34d04ac2"

SUMMARY = (
    "Build a nontrivial 2x2 through 5x5 source tile with one through three "
    "foreground colors. The output repeats the entire source tile in an "
    "n-by-n array, so every source cell appears at all coordinates with the "
    "same row and column residues modulo n."
)

INVARIANTS = [
    "the input is a square with side two through five",
    "zero is present as background and one through three nonzero colors appear",
    "every declared foreground color occurs in the returned grid",
    "the input is neither all-background nor monochrome",
    "foreground occupancy is between 35 and 75 percent, with integer rounding",
    "the output is n-squared by n-squared and is periodic with row/column period n",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_SIDES = (2, 3, 4, 5)
_PALETTE_SIZES = (1, 2, 3)
_PROFILE_PRIOR = 0.12

AXES = {
    "side": {
        "type": "int",
        "default": "difficulty-aware 2..5",
        "valid": "2..5",
    },
    "palette_size": {
        "type": "int",
        "default": "mostly one; bounded multicolor extrapolation",
        "valid": "1..3",
    },
}

# All six training inputs plus the held-out input, normalized to binary
# occupancy.  Profiles allow D4 transforms and cyclic row/column shifts:
# translating a finite tile on its torus commutes exactly with periodic tiling.
_PROFILE_ROWS = (
    ("001", "111", "100"),
    ("10", "11"),
    ("01", "10"),
    ("0010", "1010", "0101", "1110"),
    ("101", "010", "111"),
    ("0100", "1111", "0100", "0101"),
    ("01100", "11111", "01100", "11111", "01101"),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label, lower, upper in (
        ("side", 2, 5),
        ("palette_size", 1, 3),
    ):
        value = overrides.get(label)
        if value is not None and (
            type(value) is not int or not lower <= value <= upper
        ):
            raise ValueError(
                f"{label} must be an integer in [{lower}, {upper}]"
            )


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _scene_analysis(grid):
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not all(
            isinstance(row, (list, tuple, str)) and bool(row)
            for row in grid
        )
    ):
        return None, None, [
            "grid must be a non-empty list or tuple of non-empty rows"
        ]
    coerced = _coerce_grid(grid)
    side = len(coerced)
    errors = []
    if any(len(row) != side for row in coerced):
        errors.append("input must be square")
    if not 2 <= side <= 5:
        errors.append("side must be between two and five")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in coerced
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0 through 9")
        return coerced, None, errors
    colors = sorted({
        value for row in coerced for value in row if value != 0
    })
    zero_count = sum(
        value == 0 for row in coerced for value in row
    )
    if not 1 <= len(colors) <= 3:
        errors.append("one through three foreground colors must appear")
    if zero_count == 0:
        errors.append("at least one background cell must appear")
    foreground_count = side * side - zero_count
    if foreground_count == 0:
        errors.append("at least one foreground cell must appear")
    minimum_foreground = math.ceil(0.35 * side * side)
    maximum_foreground = math.floor(0.75 * side * side)
    if not minimum_foreground <= foreground_count <= maximum_foreground:
        errors.append(
            "foreground occupancy must be within the clean 35-75 percent range"
        )
    if errors:
        return coerced, None, errors
    return coerced, {
        "side": side,
        "palette": tuple(colors),
        "palette_size": len(colors),
        "foreground_count": foreground_count,
        "background_count": zero_count,
        "density": foreground_count / (side * side),
    }, []


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _coerced, _features, errors = _scene_analysis(grid)
    return errors


def observe_overrides(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "side": features["side"],
        "palette_size": features["palette_size"],
    }


def rule_mirror(grid):
    coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid source tile: " + "; ".join(errors))
    side = features["side"]
    return [
        [
            coerced[row % side][col % side]
            for col in range(side * side)
        ]
        for row in range(side * side)
    ]


def _grid_from_rows(rows):
    return [[int(value) for value in row] for row in rows]


def _rotate_90(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _transform(grid, transform):
    result = [row[:] for row in grid]
    if transform >= 4:
        result = [row[::-1] for row in result]
    for _turn in range(transform % 4):
        result = _rotate_90(result)
    return result


def _cyclic_shift(grid, row_shift, col_shift):
    side = len(grid)
    return [
        [
            grid[(row + row_shift) % side][
                (col + col_shift) % side
            ]
            for col in range(side)
        ]
        for row in range(side)
    ]


def _profile_variants(grid):
    side = len(grid)
    variants = []
    for transform in range(8):
        transformed = _transform(grid, transform)
        for row_shift in range(side):
            for col_shift in range(side):
                variants.append(
                    _cyclic_shift(
                        transformed,
                        row_shift,
                        col_shift,
                    )
                )
    distinct = {
        tuple(tuple(row) for row in variant): variant
        for variant in variants
    }
    return tuple(distinct.values())


_PROFILE_GRIDS = tuple(
    _grid_from_rows(rows) for rows in _PROFILE_ROWS
)
_PROFILE_VARIANTS = tuple(
    _profile_variants(grid) for grid in _PROFILE_GRIDS
)
_PROFILE_SIGNATURE_TO_INDEX = {}
for _profile_index, _variants in enumerate(_PROFILE_VARIANTS):
    for _variant in _variants:
        _signature = tuple(tuple(row) for row in _variant)
        _previous = _PROFILE_SIGNATURE_TO_INDEX.setdefault(
            _signature,
            _profile_index,
        )
        if _previous != _profile_index:
            raise AssertionError("public profile orbits overlap")


def _binary_signature(grid):
    coerced, features, errors = _scene_analysis(grid)
    if errors or features["palette_size"] != 1:
        return None
    return tuple(
        tuple(1 if value != 0 else 0 for value in row)
        for row in coerced
    )


def canonical_profile_index(grid):
    signature = _binary_signature(grid)
    if signature is None:
        return None
    return _PROFILE_SIGNATURE_TO_INDEX.get(signature)


def is_canonical_profile(grid):
    return canonical_profile_index(grid) is not None


def _draw_profile(index, rng):
    binary = rng.choice(_PROFILE_VARIANTS[index])
    color = rng.randint(1, 9)
    return [
        [color if value else 0 for value in row]
        for row in binary
    ]


def _draw_general(side, palette_size, rng):
    area = side * side
    lower = max(palette_size, math.ceil(0.35 * area))
    upper = min(area - 1, math.floor(0.75 * area))
    if lower > upper:
        lower = upper = max(palette_size, area - 1)
    foreground_count = rng.randint(lower, upper)
    positions = [
        (row, col)
        for row in range(side)
        for col in range(side)
    ]
    rng.shuffle(positions)
    occupied = positions[:foreground_count]
    palette = rng.sample(range(1, 10), palette_size)
    assigned = palette[:] + [
        rng.choice(palette)
        for _index in range(foreground_count - palette_size)
    ]
    rng.shuffle(assigned)
    grid = [[0] * side for _row in range(side)]
    for (row, col), color in zip(occupied, assigned):
        grid[row][col] = color
    return grid


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
    band = difficulty or "medium"
    has_override = any(
        overrides.get(label) is not None for label in AXES
    )

    profile_index = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                tuple(range(len(_PROFILE_GRIDS))),
            )

    if profile_index is not None:
        grid = _draw_profile(
            profile_index,
            ctx.draw_rng("profile_transform"),
        )
        observed = observe_overrides(grid)
        for label in AXES:
            ctx.draw_choice(label, (observed[label],))
    else:
        side_options = {
            "easy": (3, 4, 4, 4, 5, 5),
            "medium": (3, 4, 4, 5, 5, 5),
            "hard": (4, 4, 5, 5, 5, 5),
        }[band]
        palette_options = {
            "easy": (1, 1, 1, 1, 2),
            "medium": (1, 1, 1, 2, 2),
            "hard": (1, 1, 1, 2, 2, 3),
        }[band]
        if overrides.get("side") is not None:
            side_options = _SIDES
        if overrides.get("palette_size") is not None:
            palette_options = _PALETTE_SIZES
        side = ctx.draw_choice("side", side_options)
        palette_size = ctx.draw_choice(
            "palette_size",
            palette_options,
        )
        grid = _draw_general(
            side,
            palette_size,
            ctx.draw_rng("tile"),
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
