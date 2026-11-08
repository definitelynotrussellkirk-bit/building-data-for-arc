"""Generator for ``arc_additional_puzzles_21_set19_bundle:E128``.

Rule: four equal-colored cells mark the corners of an axis-aligned rectangle;
fill the complete rectangle, border and interior, with that color.

The default curriculum mixes canonical-scale scenes with larger extrapolations.
Every normal draw contains exactly four markers, the rectangle is nontrivial,
and the markers remain strictly inside the canvas so the intended bbox rule is
visible rather than confounded with clipping or border behavior.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "c9db537b5068"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "3ae37aff2b7c"  # whitespace-normalized canonical program_solution
SUMMARY = (
    "Exactly four same-color cells occupy the corners of an interior rectangle; "
    "the rule fills that rectangle solid."
)
EXAMPLES_NEEDED = 3

COLORS = tuple(range(2, 10))
CANONICAL_BBOXES = ((4, 5), (5, 5), (5, 4), (4, 6))
CANONICAL_FAMILY_RATE = 0.35

INVARIANTS = [
    "the grid is 6..13 rows by 8..14 columns",
    "exactly four non-background cells use one color in 2..9",
    "the four cells are exactly the corners of one axis-aligned bbox",
    "the bbox is at least 4x4 and has at least one background row/column on every side",
]

# Only exact, independently observable controls are public axes.  Geometry
# inside the canvas remains a sampled curriculum variable rather than a false
# override promise.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted; canonical-family draws use 6..9",
        "valid": "6..13",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted; canonical-family draws use 8..10",
        "valid": "8..14",
    },
    "color": {
        "type": "color",
        "default": "rng",
        "valid": "2..9",
    },
}


def _difficulty_ranges(difficulty: Any) -> tuple[tuple[int, int], tuple[int, int]]:
    """Return the extrapolative canvas envelope for one difficulty setting."""
    if difficulty == "easy":
        return (6, 9), (8, 10)
    if difficulty == "medium":
        return (8, 11), (9, 12)
    if difficulty == "hard":
        return (10, 13), (11, 14)
    return (6, 10), (8, 11)


def _draw_axis_int(
    ctx,
    label: str,
    *,
    valid: tuple[int, int],
    default: tuple[int, int],
) -> int:
    """Honor every declared boundary while retaining narrower default bands."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, *valid)
    return ctx.draw_int(label, *default)


def _choose_bbox_dims(ctx, h: int, w: int, *, canonical_family: bool) -> tuple[int, int]:
    """Choose a nontrivial bbox with square, wide, and tall witnesses."""
    max_h = h - 2  # preserve at least one background row above and below
    max_w = w - 2  # preserve at least one background column left and right
    rng = ctx.draw_rng("bbox_geometry")

    if canonical_family:
        choices = [
            dims
            for dims in CANONICAL_BBOXES
            if dims[0] <= max_h and dims[1] <= max_w
        ]
        if not choices:  # impossible under the public axis minima; defensive only
            raise ValueError(
                f"canvas {h}x{w} cannot fit any canonical bbox with an interior margin"
            )
        return rng.choice(choices)

    # Difficulty controls the extrapolation envelope but never weakens the
    # four-corner grammar.  The profile is selected only from feasible shapes,
    # so no recorded choice is silently clamped or replaced.
    if ctx.difficulty == "easy":
        max_h = min(max_h, 5)
        max_w = min(max_w, 6)
    elif ctx.difficulty == "medium":
        max_h = min(max_h, 7)
        max_w = min(max_w, 8)

    profiles = ["square"]
    if max_w >= 5:
        profiles.append("wide")
    if max_h >= 5:
        profiles.append("tall")
    profile = rng.choice(profiles)

    if profile == "square":
        side = rng.randint(4, min(max_h, max_w))
        return side, side
    if profile == "wide":
        bbox_h = rng.randint(4, min(max_h, max_w - 1))
        bbox_w = rng.randint(bbox_h + 1, max_w)
        return bbox_h, bbox_w

    bbox_w = rng.randint(4, min(max_w, max_h - 1))
    bbox_h = rng.randint(bbox_w + 1, max_h)
    return bbox_h, bbox_w


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unsupported override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    canonical_family = (
        ctx.draw_rng("distribution_family").random() < CANONICAL_FAMILY_RATE
    )
    if canonical_family:
        default_h = (6, 9)
        default_w = (8, 10)
    else:
        default_h, default_w = _difficulty_ranges(difficulty)

    h = _draw_axis_int(ctx, "grid_h", valid=(6, 13), default=default_h)
    w = _draw_axis_int(ctx, "grid_w", valid=(8, 14), default=default_w)
    color = ctx.draw_int("color", 2, 9)
    bbox_h, bbox_w = _choose_bbox_dims(
        ctx, h, w, canonical_family=canonical_family
    )

    position_rng = ctx.draw_rng("bbox_position")
    top = position_rng.randint(1, h - bbox_h - 1)
    left = position_rng.randint(1, w - bbox_w - 1)
    bottom = top + bbox_h - 1
    right = left + bbox_w - 1

    grid = full_grid(h, w, 0)
    for row, col in (
        (top, left),
        (top, right),
        (bottom, left),
        (bottom, right),
    ):
        grid[row][col] = color
    return grid


def _analyze(grid) -> tuple[dict[str, Any], list[str]]:
    """Recover structural facts without mutating the supplied grid."""
    facts: dict[str, Any] = {}
    errors: list[str] = []

    if not isinstance(grid, list) or not grid:
        return facts, ["grid must be a non-empty list of rows"]
    if not all(isinstance(row, list) for row in grid):
        return facts, ["every row must be a list"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return facts, ["grid must be non-ragged and have positive width"]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return facts, ["all cells must be integer ARC colors 0..9"]

    height = len(grid)
    facts.update(grid_h=height, grid_w=width)
    if not 6 <= height <= 13:
        errors.append("grid height must be in the declared range 6..13")
    if not 8 <= width <= 14:
        errors.append("grid width must be in the declared range 8..14")

    points = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    facts["nonbg_count"] = len(points)
    if len(points) != 4:
        errors.append("expected exactly four non-background corner markers")
    if not points:
        return facts, errors

    colors = {value for _, _, value in points}
    facts["colors"] = tuple(sorted(colors))
    if len(colors) != 1:
        errors.append("all four corner markers must use one color")
    color = points[0][2]
    facts["color"] = color
    if any(value not in COLORS for _, _, value in points):
        errors.append("marker color must be in the declared range 2..9")

    rows = [row for row, _, _ in points]
    cols = [col for _, col, _ in points]
    top, bottom = min(rows), max(rows)
    left, right = min(cols), max(cols)
    bbox_h = bottom - top + 1
    bbox_w = right - left + 1
    margins = (top, height - 1 - bottom, left, width - 1 - right)
    facts.update(
        bbox=(top, left, bottom, right),
        bbox_h=bbox_h,
        bbox_w=bbox_w,
        margins=margins,
    )

    if bbox_h < 4 or bbox_w < 4:
        errors.append("corner bbox must be at least 4x4")
    expected = {
        (top, left),
        (top, right),
        (bottom, left),
        (bottom, right),
    }
    actual = {(row, col) for row, col, _ in points}
    if len(points) != 4 or actual != expected:
        errors.append("non-background cells must be exactly the four bbox corners")
    if any(margin < 1 for margin in margins):
        errors.append("bbox must have at least one background row/column on every side")
    return facts, errors


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty  # structure is difficulty-independent
    facts, errors = _analyze(grid)

    if isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            for axis in ("grid_h", "grid_w", "color"):
                if axis in requested and facts.get(axis) != requested[axis]:
                    errors.append(
                        f"override {axis}={requested[axis]!r} realized as "
                        f"{facts.get(axis)!r}"
                    )
    return errors


def observe_overrides(grid):
    """Return exact public-axis values recovered from the returned grid."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "color": facts["color"],
    }
