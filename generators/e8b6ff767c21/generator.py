"""Generator for ARC training task 28e73c20 / e8b6ff767c21.

The input is a completely blank rectangle.  Its height and width are the only
signals.  The rule returns a clockwise green spiral beginning at the top-left.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "e8b6ff767c21"
VERSION = "4.0.0"
TASK_ID = "e8b6ff767c21"
RULE_HASH = "144daeb8750a"

SUMMARY = (
    "Return a completely blank 5..28 by 5..28 canvas. Height and width "
    "are the only semantic inputs; the rule draws the corresponding "
    "clockwise green spiral from the top-left. A controlled default prior "
    "covers every exact public square size in every difficulty band, while "
    "the general path also teaches lawful rectangular extrapolations."
)

INVARIANTS = [
    "the input is a rectangular 5..28 by 5..28 grid",
    "every input cell is background 0",
    "height and width are the only varying semantic features",
    "the output is the deterministic green spiral for that exact shape",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 5..28",
        "valid": "5..28",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 5..28",
        "valid": "5..28",
    },
}

_VALID_DIM = (5, 28)
_CANONICAL_SIZES = frozenset((6, 8, 10, 13, 15, 18))
_PROFILE_PRIOR = 0.10
_BAND_BOUNDS = {
    "easy": (5, 14),
    "medium": (9, 22),
    "hard": (14, 28),
}

# Each blank input and output is determined exactly by its (height, width).
EXPECTED_OUTPUT_CODOMAIN = (
    (_VALID_DIM[1] - _VALID_DIM[0] + 1) ** 2
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in AXES:
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")


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


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return ["grid rows must be non-empty lists or digit strings"]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return ["grid must be rectangular"]

    errors = []
    height = len(coerced)
    if not _VALID_DIM[0] <= height <= _VALID_DIM[1]:
        errors.append("grid height must be in 5..28")
    if not _VALID_DIM[0] <= width <= _VALID_DIM[1]:
        errors.append("grid width must be in 5..28")
    if any(
        type(value) is not int or value != 0
        for row in coerced
        for value in row
    ):
        errors.append("every input cell must be integer background 0")
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def _spiral(height, width):
    output = full_grid(height, width, 0)
    directions = ((0, 1), (1, 0), (0, -1), (-1, 0))
    row = 0
    col = 0
    output[0][0] = 3
    segment = 0
    while True:
        base = width - 1 if segment % 2 == 0 else height - 1
        shrink = (
            0
            if segment < 3
            else 2 * ((segment - 1) // 2)
        )
        length = base - shrink
        if length <= 0:
            return output
        dr, dc = directions[segment % 4]
        for _ in range(length):
            row += dr
            col += dc
            if 0 <= row < height and 0 <= col < width:
                output[row][col] = 3
        segment += 1


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    return _spiral(len(grid), len(grid[0]))


def canonical_profile_signature(grid):
    if self_check(grid):
        return None
    height = len(grid)
    width = len(grid[0])
    if height == width and height in _CANONICAL_SIZES:
        return height, width
    return None


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    (size, size) for size in _CANONICAL_SIZES
)


def is_canonical_profile(grid):
    return (
        canonical_profile_signature(grid)
        in _CANONICAL_PROFILE_SIGNATURES
    )


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
    profile_size = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_size = ctx.draw_choice(
                f"canonical_size|{band}",
                tuple(sorted(_CANONICAL_SIZES)),
            )

    if profile_size is not None:
        height = ctx.draw_int("grid_h", profile_size, profile_size)
        width = ctx.draw_int("grid_w", profile_size, profile_size)
    else:
        bounds = _BAND_BOUNDS[band]
        height = ctx.draw_int(
            "grid_h",
            *_VALID_DIM
            if overrides.get("grid_h") is not None
            else bounds,
        )
        width = ctx.draw_int(
            "grid_w",
            *_VALID_DIM
            if overrides.get("grid_w") is not None
            else bounds,
        )

    grid = full_grid(height, width, 0)
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
