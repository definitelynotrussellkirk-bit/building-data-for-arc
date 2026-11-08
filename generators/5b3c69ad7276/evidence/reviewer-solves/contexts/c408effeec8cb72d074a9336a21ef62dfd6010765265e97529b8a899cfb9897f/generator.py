"""Generator for bank task E145 / 5b3c69ad7276.

A lawful input contains exactly one non-zero seed.  The Racket oracle paints
that seed's color across the complete row and column through the seed.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "5b3c69ad7276"
TASK_ID = "5b3c69ad7276"
VERSION = "2.0.0"
RULE_HASH = "2ee7e1a5f677"

SUMMARY = (
    "Place exactly one colored seed on a zero-background grid. The output "
    "keeps the grid size and paints the seed's full row and full column in "
    "the same color."
)

INVARIANTS = [
    "the grid is rectangular, 4 through 12 cells on each side",
    "zero is the only background color",
    "exactly one cell is non-zero",
    "the seed color is an integer from 1 through 9",
    "corner, non-corner edge, and interior seed positions are all lawful",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

ANCHOR_KINDS = ("corner", "edge", "interior")
_FULL_DIMENSION_RANGE = (4, 12)
_BAND_HEIGHT = {
    None: (4, 10),
    "easy": (4, 6),
    "medium": (5, 9),
    "hard": (8, 12),
}
_BAND_WIDTH = {
    None: (4, 10),
    "easy": (4, 7),
    "medium": (5, 10),
    "hard": (8, 12),
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 4..12",
        "valid": "4..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 4..12",
        "valid": "4..12",
    },
    "anchor_kind": {
        "type": "str",
        "default": "balanced corner|edge|interior",
        "valid": "corner|edge|interior",
    },
    "color": {
        "type": "color",
        "default": "uniform non-zero ARC color",
        "valid": "1..9",
    },
}


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in _BAND_HEIGHT:
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    for label in ("grid_h", "grid_w"):
        value = overrides.get(label)
        if value is not None and (
            type(value) is not int or not 4 <= value <= 12
        ):
            raise ValueError(f"{label} must be an integer in [4, 12]")

    anchor_kind = overrides.get("anchor_kind")
    if anchor_kind is not None and anchor_kind not in ANCHOR_KINDS:
        raise ValueError(
            "anchor_kind must be 'corner', 'edge', or 'interior'"
        )

    color = overrides.get("color")
    if color is not None and (
        type(color) is not int or not 1 <= color <= 9
    ):
        raise ValueError("color must be an integer in [1, 9]")


def _position_candidates(height: int, width: int, anchor_kind: str):
    if anchor_kind == "corner":
        return (
            (0, 0),
            (0, width - 1),
            (height - 1, 0),
            (height - 1, width - 1),
        )
    if anchor_kind == "edge":
        return tuple(
            [(0, col) for col in range(1, width - 1)]
            + [(height - 1, col) for col in range(1, width - 1)]
            + [(row, 0) for row in range(1, height - 1)]
            + [(row, width - 1) for row in range(1, height - 1)]
        )
    return tuple(
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    )


def _scene_analysis(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a non-empty list or tuple"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return None, ["rows must be non-empty lists or tuples"]

    height = len(grid)
    width = len(grid[0])
    errors = []
    if any(len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return None, errors
    if not 4 <= height <= 12 or not 4 <= width <= 12:
        errors.append(
            f"grid dimensions {height}x{width} must both be in [4, 12]"
        )
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0 through 9")
        return None, errors

    nonzero = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    ]
    if len(nonzero) != 1:
        errors.append(
            f"expected exactly one non-zero seed, found {len(nonzero)}"
        )
        return None, errors

    seed_row, seed_col, color = nonzero[0]
    if seed_row in (0, height - 1) and seed_col in (0, width - 1):
        anchor_kind = "corner"
    elif seed_row in (0, height - 1) or seed_col in (0, width - 1):
        anchor_kind = "edge"
    else:
        anchor_kind = "interior"

    return {
        "grid_h": height,
        "grid_w": width,
        "seed_row": seed_row,
        "seed_col": seed_col,
        "anchor_kind": anchor_kind,
        "color": color,
    }, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return structural errors for the normal teaching distribution."""
    del difficulty, meta
    _features, errors = _scene_analysis(grid)
    return errors


def observe_overrides(grid) -> dict[str, object]:
    """Recover every declared exact axis from the returned grid."""
    features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "grid_h": features["grid_h"],
        "grid_w": features["grid_w"],
        "anchor_kind": features["anchor_kind"],
        "color": features["color"],
    }


def rule_mirror(grid):
    """Small Python test oracle; production output remains Racket-authoritative."""
    features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid cross lesson: " + "; ".join(errors))
    return [
        [
            features["color"]
            if row == features["seed_row"]
            or col == features["seed_col"]
            else 0
            for col in range(features["grid_w"])
        ]
        for row in range(features["grid_h"])
    ]


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

    height_bounds = (
        _FULL_DIMENSION_RANGE
        if overrides.get("grid_h") is not None
        else _BAND_HEIGHT[difficulty]
    )
    width_bounds = (
        _FULL_DIMENSION_RANGE
        if overrides.get("grid_w") is not None
        else _BAND_WIDTH[difficulty]
    )
    height = ctx.draw_int("grid_h", *height_bounds)
    width = ctx.draw_int("grid_w", *width_bounds)
    anchor_kind = ctx.draw_choice("anchor_kind", ANCHOR_KINDS)
    color = ctx.draw_color("color", exclude=(0,))

    position_rng = ctx.draw_rng("seed_position")
    seed_row, seed_col = position_rng.choice(
        _position_candidates(height, width, anchor_kind)
    )
    grid = full_grid(height, width, 0)
    grid[seed_row][seed_col] = color

    errors = self_check(grid)
    if errors:
        raise ValueError("internal layout violated self_check: " + "; ".join(errors))
    return grid
