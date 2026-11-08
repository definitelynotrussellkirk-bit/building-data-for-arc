"""Generator for training task c1990cce / e84a374b51f2.

The input is a clean 1xN row with one centered red marker.  The rule uses only
N: it draws an NxN red V followed by phase-aligned blue diagonal stripes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "e84a374b51f2"
VERSION = "3.0.0"
TASK_ID = "e84a374b51f2"
RULE_HASH = "df069703121f"

SUMMARY = (
    "Return a clean odd-width 1xN row with one centered red marker. The "
    "output is the rule-intrinsic NxN red V and phase-aligned blue stripe "
    "pattern, so width is the only varying semantic feature."
)

INVARIANTS = [
    "the input is exactly one row with odd width 5..29",
    "the only nonzero input cell is red 2 at the unique center column",
    "the output is NxN and is a deterministic function of input width N",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_ODD_WIDTHS = tuple(range(5, 30, 2))
_CANONICAL_WIDTHS = frozenset((5, 7, 13, 17))
_BAND_WIDTHS = {
    "easy": (5, 7, 9, 11, 13, 15, 17, 19),
    "medium": _ODD_WIDTHS,
    "hard": (5, 7, 13, 15, 17, 19, 21, 23, 25, 27, 29),
}

# The rule ignores cell content and is completely determined by one of the
# thirteen lawful odd widths.  Duplicate outputs beyond this exact ceiling are
# intrinsic rather than evidence of a collapsed sampler.
EXPECTED_OUTPUT_CODOMAIN = len(_ODD_WIDTHS)

AXES = {
    "grid_n": {
        "type": "int",
        "default": "difficulty-aware odd width",
        "valid": "5|7|9|11|13|15|17|19|21|23|25|27|29",
    },
}


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    value = overrides.get("grid_n")
    if value is not None:
        if type(value) is not int:
            raise ValueError("grid_n must be an integer")
        if value not in _ODD_WIDTHS:
            raise ValueError("grid_n must be an odd integer in 5..29")


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
    if not isinstance(grid, list) or len(grid) != 1:
        return ["grid must contain exactly one row"]
    if not isinstance(grid[0], (list, str)) or not grid[0]:
        return ["the single row must be a non-empty list or digit string"]
    row = _coerce_grid(grid)[0]
    errors = []
    n = len(row)
    if n not in _ODD_WIDTHS:
        errors.append("row width must be an odd integer in 5..29")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for value in row
    ):
        errors.append("row values must be integer ARC colors 0..9")
        return errors
    if n in _ODD_WIDTHS:
        center = n // 2
        if row[center] != 2:
            errors.append("the center cell must be red 2")
        if any(value != 0 for c, value in enumerate(row) if c != center):
            errors.append("every non-center cell must be background 0")
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {"grid_n": len(grid[0])}


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    n = len(grid[0])
    mid = n // 2
    output = full_grid(n, n, 0)
    for r in range(n):
        for c in range(n):
            if r <= mid and c in (mid - r, mid + r):
                output[r][c] = 2
            elif (
                r >= 3
                and c % 4 == (r + mid) % 4
                and (
                    r > mid
                    or mid - r < c < mid + r
                )
            ):
                output[r][c] = 1
    return output


def canonical_profile_signature(grid):
    if self_check(grid):
        return None
    width = len(grid[0])
    return width if width in _CANONICAL_WIDTHS else None


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) is not None


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
    options = (
        _ODD_WIDTHS
        if overrides.get("grid_n") is not None
        else _BAND_WIDTHS[band]
    )
    n = ctx.draw_choice("grid_n", options)
    grid = full_grid(1, n, 0)
    grid[0][n // 2] = 2
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
