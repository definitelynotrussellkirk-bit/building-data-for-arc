"""Generator for rectangle outlines inferred from four same-color corners.

For every nonzero color, the input contains exactly the four corners of one
nondegenerate rectangle.  The output is a fresh zero-background grid with each
rectangle's complete outline painted in its marker color.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "64592477ccc8"
TASK_ID = "64592477ccc8"
VERSION = "3.0.0"
RULE_HASH = "fb7ed02e18c2"

SUMMARY = (
    "A zero-background grid contains two or three colors. For each color, "
    "exactly four cells mark the four corners of one axis-aligned rectangle. "
    "Each rectangle spans at least two rows and two columns, is not a 2x2 "
    "identity case, and its eventual outline is disjoint from every other "
    "color's outline. The output is a fresh blank grid of the same size with "
    "the complete bounding-box outline of every color painted in that color."
)

INVARIANTS = [
    "two or three distinct nonzero colors",
    "each color occupies exactly the four corners of its bounding box",
    "each rectangle spans at least 2x2 and has at least one side of length 3+",
    "different colors' rectangle outlines are disjoint",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware draw in 7..12",
        "valid": "7..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware draw in 9..14",
        "valid": "9..14",
    },
    "n_colors": {
        "type": "int",
        "default": "uniform draw in 2..3",
        "valid": "2..3",
    },
}


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    bounds = {"grid_h": (7, 12), "grid_w": (9, 14), "n_colors": (2, 3)}
    for label, (lo, hi) in bounds.items():
        value = overrides.get(label)
        if value is None:
            continue
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{label} must be an integer in [{lo}, {hi}]")


def _partition(total: int, count: int) -> list[tuple[int, int]]:
    """Return count contiguous inclusive bands whose sizes differ by at most one."""
    base, extra = divmod(total, count)
    bands = []
    start = 0
    for index in range(count):
        size = base + (1 if index < extra else 0)
        bands.append((start, start + size - 1))
        start += size
    return bands


def _outline_cells(r0: int, c0: int, r1: int, c1: int) -> set[tuple[int, int]]:
    return (
        {(r0, col) for col in range(c0, c1 + 1)}
        | {(r1, col) for col in range(c0, c1 + 1)}
        | {(row, c0) for row in range(r0, r1 + 1)}
        | {(row, c1) for row in range(r0, r1 + 1)}
    )


def _paint_corners(
    grid: list[list[int]], color: int, r0: int, c0: int, r1: int, c1: int
) -> None:
    for row, col in ((r0, c0), (r0, c1), (r1, c0), (r1, c1)):
        grid[row][col] = color


def _vertical_scene(ctx, grid: list[list[int]], colors: tuple[int, ...], profile: str) -> None:
    height = len(grid)
    width = len(grid[0])
    for index, (color, (band_left, band_right)) in enumerate(
        zip(colors, _partition(width, len(colors)))
    ):
        rng = ctx.draw_rng(f"rectangle_{index}")
        band_width = band_right - band_left + 1
        rect_width = rng.randint(3, band_width)
        rect_height = rng.randint(3, height)
        if profile in ("thin_width", "mixed") and index == 0:
            rect_width = 2
        elif profile == "thin_height" and index == 0:
            rect_height = 2
        elif profile == "mixed" and len(colors) >= 3 and index == 1:
            rect_height = 2
        elif profile not in ("thin_width", "thin_height", "thick", "mixed"):
            raise AssertionError(f"unknown profile: {profile}")
        c0 = rng.randint(band_left, band_right - rect_width + 1)
        r0 = rng.randint(0, height - rect_height)
        _paint_corners(
            grid,
            color,
            r0,
            c0,
            r0 + rect_height - 1,
            c0 + rect_width - 1,
        )


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
    height = ctx.draw_int_diff("grid_h", 7, 12)
    width = ctx.draw_int_diff("grid_w", 9, 14)
    n_colors = ctx.draw_int("n_colors", 2, 3)
    colors = ctx.draw_distinct_colors("colors", n=n_colors, exclude=(0, 1))
    grid = full_grid(height, width, 0)

    # A fixed four-step schedule prevents random lesson batches from omitting
    # the canonical two-cell-wide case or the complementary geometry branches.
    profile = ("thin_width", "thin_height", "thick", "mixed")[sample_index % 4]
    _vertical_scene(ctx, grid, colors, profile)

    errors = self_check(grid)
    if errors:  # fail closed if a future edit breaks the constructive proof
        raise AssertionError("constructed invalid scene: " + "; ".join(errors))
    return grid


def _coerce_grid(grid):
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and len(row) > 0 for row in grid):
        return None, ["grid rows must be non-empty lists or digit strings"]
    coerced = []
    for row in grid:
        values = []
        for value in row:
            if isinstance(value, str) and len(value) == 1 and value.isdigit():
                value = int(value)
            values.append(value)
        coerced.append(values)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return coerced, ["grid must be rectangular"]
    return coerced, []


def _scene_analysis(grid):
    coerced, errors = _coerce_grid(grid)
    if errors:
        return coerced, None, errors
    height = len(coerced)
    width = len(coerced[0])
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in coerced
        for value in row
    ):
        return coerced, None, ["cells must be integer ARC colors 0..9"]

    by_color: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(coerced):
        for col, value in enumerate(values):
            if value != 0:
                by_color.setdefault(value, []).append((row, col))
    if not 2 <= len(by_color) <= 3:
        errors.append(f"expected 2-3 rectangle colors, found {len(by_color)}")

    boxes = []
    for color, points in sorted(by_color.items()):
        if len(points) != 4:
            errors.append(f"color {color} must occur at exactly four corners, found {len(points)}")
            continue
        rows = [row for row, _ in points]
        cols = [col for _, col in points]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)
        expected = {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}
        actual = set(points)
        if actual != expected:
            errors.append(f"color {color} cells are not exactly its four bounding-box corners")
            continue
        rect_height = r1 - r0 + 1
        rect_width = c1 - c0 + 1
        if rect_height < 2 or rect_width < 2:
            errors.append(f"color {color} rectangle must span at least two rows and columns")
            continue
        if rect_height == 2 and rect_width == 2:
            errors.append(f"color {color} 2x2 rectangle is an identity/no-op lesson")
            continue
        boxes.append(
            {
                "color": color,
                "r0": r0,
                "c0": c0,
                "r1": r1,
                "c1": c1,
                "height": rect_height,
                "width": rect_width,
                "outline": _outline_cells(r0, c0, r1, c1),
            }
        )

    for index, first in enumerate(boxes):
        for second in boxes[index + 1 :]:
            if first["outline"] & second["outline"]:
                errors.append(
                    "rectangle outlines for colors "
                    f"{first['color']}/{second['color']} overlap and create overwrite ambiguity"
                )

    if errors:
        return coerced, None, errors
    return coerced, {
        "grid_h": height,
        "grid_w": width,
        "n_colors": len(by_color),
        "boxes": boxes,
        "has_width_2": any(box["width"] == 2 for box in boxes),
        "has_height_2": any(box["height"] == 2 for box in boxes),
        "all_thick": all(box["width"] >= 3 and box["height"] >= 3 for box in boxes),
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    _coerced, _features, errors = _scene_analysis(grid)
    return errors


def observe_overrides(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "grid_h": features["grid_h"],
        "grid_w": features["grid_w"],
        "n_colors": features["n_colors"],
    }


def rule_mirror(grid):
    coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid rectangle-corner scene: " + "; ".join(errors))
    output = full_grid(features["grid_h"], features["grid_w"], 0)
    for box in features["boxes"]:
        for row, col in box["outline"]:
            output[row][col] = box["color"]
    return output


def canonical_profile_signature(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        return None
    return (
        features["grid_h"],
        features["grid_w"],
        tuple(
            sorted(
                (box["height"], box["width"])
                for box in features["boxes"]
            )
        ),
    )


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) is not None
