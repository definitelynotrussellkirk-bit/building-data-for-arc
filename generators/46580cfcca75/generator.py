"""Constructive input generator for ARC task 46580cfcca75.

Rule authority
--------------
On a fresh zero grid, replace every non-zero same-colour 4-connected object
with the perimeter of its tight bounding box, preserving that object's colour.
For this task's training manifold every object is already a filled rectangle,
so the visible operation is "turn each solid rectangle into a hollow frame".
Outputs remain owned by the repository's pinned Racket authority; ``rule_mirror``
is an executable review oracle, not a second label source.

The public surface is intentionally small.  ``grid_h``, ``grid_w`` and
``n_rects`` are all exact, constructive for their full Cartesian product, and
recoverable from returned pixels by ``observe_overrides``.
"""
from __future__ import annotations

from collections.abc import Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "46580cfcca75"
TASK_ID = "46580cfcca75"
VERSION = "3.0.0"
RULE_HASH = "001f318153f4"

SUMMARY = (
    "A 6..14 by 7..16 zero-background grid contains one or two separated, "
    "distinct-colour filled rectangles. At least one rectangle has height and "
    "width at least 3, so the rule visibly erases an interior. Some scheduled "
    "examples also contain a 2-cell-thick rectangle. On a blank output canvas, "
    "replace every non-zero same-colour object by the perimeter of its tight "
    "bounding box in the same colour."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0 and object colours are distinct integers in 1..9",
    "there are one or two same-colour 4-connected objects",
    "every object exactly fills its rectangular bounding box",
    "at least one rectangle is at least 3x3, making interior erasure visible",
    "rectangular bounding boxes are separated by at least one background row or column",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-sample canonical-profile schedule",
        "valid": "6..14",
    },
    "grid_w": {
        "type": "int",
        "default": "four-sample canonical-profile schedule",
        "valid": "7..16",
    },
    "n_rects": {
        "type": "int",
        "default": "canonical-profile schedule: one or two",
        "valid": "1..2",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, int]] = []

_AXIS_BOUNDS = {
    "grid_h": (6, 14),
    "grid_w": (7, 16),
    "n_rects": (1, 2),
}

# These are exactly the four canonical (height, width, object-count) profiles.
# Two residues carry a thin-object counterexample; three carry multiple objects.
# Therefore every three-demo rotation of four consecutive samples refutes all
# declared lesson competitors.
_CANONICAL_PROFILES = (
    (6, 8, 2),
    (7, 7, 2),
    (7, 9, 2),
    (8, 9, 1),
)
SCHEDULE_PROFILES = (
    "thin_second_horizontal",
    "two_large",
    "thin_second_vertical",
    "single_large",
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic semantic slot for a sequential lesson."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:  # reject bool, float and numeric strings
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _draw_axis(ctx, overrides, name: str, anchor: int) -> int:
    """Draw an exact public axis while keeping defaults on canonical profiles."""
    lo, hi = _AXIS_BOUNDS[name]
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    # A singleton keyed draw records provenance without allowing the default
    # schedule to drift away from its canonical profile.
    return ctx.draw_choice(name, (anchor,))


def _dimension_options(height: int, width: int, *, thin: bool):
    """Candidate rectangle dimensions, bounded for legibility and diversity."""
    max_h = min(5, height)
    max_w = min(6, width)
    if thin:
        return [
            (rh, rw)
            for rh in range(2, max_h + 1)
            for rw in range(2, max_w + 1)
            if min(rh, rw) == 2
        ]
    return [
        (rh, rw)
        for rh in range(3, max_h + 1)
        for rw in range(3, max_w + 1)
    ]


def _choose_layout(
    height: int,
    width: int,
    n_rects: int,
    *,
    thin_second: bool,
    difficulty: str | None,
    rng,
):
    """Construct one or two boxes with a guaranteed one-cell background gap.

    The smallest override canvas is 6x7.  Two 3x3 boxes fit side by side there,
    so the full declared Cartesian product is constructive without retries or
    silent object dropping.
    """
    large = _dimension_options(height, width, thin=False)
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"

    def band_slice(options, area_key):
        ranked = sorted(options, key=area_key)
        width_ = max(1, (len(ranked) + 2) // 3)
        if band == "easy":
            return ranked[:width_]
        if band == "hard":
            return ranked[-width_:]
        return ranked

    if n_rects == 1:
        choices = band_slice(large, lambda dims: dims[0] * dims[1])
        rh, rw = rng.choice(choices)
        row = rng.randint(0, height - rh)
        col = rng.randint(0, width - rw)
        return [(row, col, rh, rw)]

    second_options = _dimension_options(height, width, thin=thin_second)
    dimension_layouts = []
    for rh1, rw1 in large:
        for rh2, rw2 in second_options:
            if rw1 + 1 + rw2 <= width:
                dimension_layouts.append(("horizontal", rh1, rw1, rh2, rw2))
            if rh1 + 1 + rh2 <= height:
                dimension_layouts.append(("vertical", rh1, rw1, rh2, rw2))
    if not dimension_layouts:
        raise RuntimeError(
            f"no constructive layout for {height}x{width}, "
            f"n_rects={n_rects}, thin_second={thin_second}"
        )

    dimension_layouts = band_slice(
        dimension_layouts,
        lambda item: item[1] * item[2] + item[3] * item[4],
    )
    orientation, rh1, rw1, rh2, rw2 = rng.choice(dimension_layouts)
    if orientation == "horizontal":
        # Split free horizontal cells into left padding, an internal gap, and
        # right padding.  The internal gap is always at least one cell.
        spare = width - rw1 - rw2 - 1
        left = rng.randint(0, spare)
        gap_extra = rng.randint(0, spare - left)
        col1 = left
        col2 = col1 + rw1 + 1 + gap_extra
        row1 = rng.randint(0, height - rh1)
        row2 = rng.randint(0, height - rh2)
    else:
        spare = height - rh1 - rh2 - 1
        top = rng.randint(0, spare)
        gap_extra = rng.randint(0, spare - top)
        row1 = top
        row2 = row1 + rh1 + 1 + gap_extra
        col1 = rng.randint(0, width - rw1)
        col2 = rng.randint(0, width - rw2)
    return [(row1, col1, rh1, rw1), (row2, col2, rh2, rw2)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile_index = int(sample_index) % len(_CANONICAL_PROFILES)
    anchor_h, anchor_w, anchor_n = _CANONICAL_PROFILES[profile_index]
    height = _draw_axis(ctx, overrides, "grid_h", anchor_h)
    width = _draw_axis(ctx, overrides, "grid_w", anchor_w)
    n_rects = _draw_axis(ctx, overrides, "n_rects", anchor_n)

    semantic_slot = schedule_profile(seed, sample_index, difficulty)
    thin_second = n_rects == 2 and semantic_slot in {
        "thin_second_horizontal",
        "thin_second_vertical",
    }
    band_key = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"
    layout = _choose_layout(
        height,
        width,
        n_rects,
        thin_second=thin_second,
        difficulty=difficulty,
        rng=ctx.draw_rng(f"rectangle_layout_{band_key}"),
    )
    colors = ctx.draw_rng(f"rectangle_colors_{band_key}").sample(range(1, 10), n_rects)

    grid = full_grid(height, width, 0)
    for (row, col, rect_h, rect_w), color in zip(layout, colors, strict=True):
        draw_rect(grid, row, col, rect_h, rect_w, color)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructive generation violated its contract: {errors}")
    return grid


_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _objects(grid: Sequence[Sequence[int]]) -> list[dict]:
    """Same-colour four-connected components in row-major order."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            pending = [(row, col)]
            seen.add((row, col))
            cells = []
            while pending:
                current = pending.pop()
                cells.append(current)
                cr, cc = current
                for dr, dc in _NEIGHBORS:
                    nxt = cr + dr, cc + dc
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        pending.append(nxt)
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            result.append(
                {
                    "color": color,
                    "cells": tuple(cells),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return result


def _bbox_hw(obj) -> tuple[int, int]:
    r1, c1, r2, c2 = obj["bbox"]
    return r2 - r1 + 1, c2 - c1 + 1


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact public control from visible pixels."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_rects": len(_objects(grid)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the legal solid-rectangle teaching manifold.

    The four canonical inputs pass.  Difficulty and metadata are accepted for
    the shared validator protocol but do not change legality.
    """
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9"]

    height = len(grid)
    errors: list[str] = []
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 is absent")
    if not 6 <= height <= 14:
        errors.append(f"grid_h={height} outside [6,14]")
    if not 7 <= width <= 16:
        errors.append(f"grid_w={width} outside [7,16]")

    objs = _objects(grid)
    if not 1 <= len(objs) <= 2:
        errors.append(f"expected one or two objects, found {len(objs)}")
        return errors
    colors = [obj["color"] for obj in objs]
    if len(set(colors)) != len(colors):
        errors.append("objects must use distinct colors")

    has_visible_interior = False
    for obj in objs:
        rect_h, rect_w = _bbox_hw(obj)
        if len(obj["cells"]) != rect_h * rect_w:
            errors.append(f"color {obj['color']} object does not fill its bounding box")
        if rect_h >= 3 and rect_w >= 3:
            has_visible_interior = True
    if not has_visible_interior:
        errors.append("no rectangle has a visible interior to erase")

    for index, first in enumerate(objs):
        ar1, ac1, ar2, ac2 = first["bbox"]
        for second in objs[index + 1 :]:
            br1, bc1, br2, bc2 = second["bbox"]
            if (
                ar1 <= br2 + 1
                and br1 <= ar2 + 1
                and ac1 <= bc2 + 1
                and bc1 <= ac2 + 1
            ):
                errors.append(
                    f"bboxes of colors {first['color']} and {second['color']} "
                    "overlap or lack a one-cell background gap"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Strict lawful-manifold validator; canonical examples pass unchanged."""
    return self_check(grid)


def _paint_outline(output, obj) -> None:
    r1, c1, r2, c2 = obj["bbox"]
    color = obj["color"]
    for row in range(r1, r2 + 1):
        output[row][c1] = color
        output[row][c2] = color
    for col in range(c1 + 1, c2):
        output[r1][col] = color
        output[r2][col] = color


def rule_mirror(grid):
    """Python mirror of the pinned Racket rule for testing and rival probes."""
    output = [[0 for _ in row] for row in grid]
    for obj in _objects(grid):
        _paint_outline(output, obj)
    return output


def _identity(grid):
    return [list(row) for row in grid]


def _largest_only(grid):
    output = [[0 for _ in row] for row in grid]
    objs = _objects(grid)
    if objs:
        _, largest = max(
            enumerate(objs),
            key=lambda item: (len(item[1]["cells"]), -item[0]),
        )
        _paint_outline(output, largest)
    return output


def _drop_thin(grid):
    output = [[0 for _ in row] for row in grid]
    for obj in _objects(grid):
        rect_h, rect_w = _bbox_hw(obj)
        if rect_h >= 3 and rect_w >= 3:
            _paint_outline(output, obj)
    return output


def _global_bbox(grid):
    output = [[0 for _ in row] for row in grid]
    objs = _objects(grid)
    if not objs:
        return output
    rows = [row for obj in objs for row, _ in obj["cells"]]
    cols = [col for obj in objs for _, col in obj["cells"]]
    fake = {
        "color": objs[0]["color"],
        "bbox": (min(rows), min(cols), max(rows), max(cols)),
    }
    _paint_outline(output, fake)
    return output


def _has_interior_erasure(grid) -> bool:
    return any(rect_h >= 3 and rect_w >= 3 for rect_h, rect_w in map(_bbox_hw, _objects(grid)))


def _has_multiple_objects(grid) -> bool:
    return len(_objects(grid)) >= 2


def _has_thin_rectangle(grid) -> bool:
    return any(min(_bbox_hw(obj)) == 2 for obj in _objects(grid))


def lesson_identifiable(demos, query) -> list[str]:
    """Report declared wrong rules that fit all demos but alter the query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if (
            all(rival(demo["input"]) == demo["output"] for demo in demos)
            and rival(query["input"]) != query["output"]
        ):
            reasons.append(f"rival {name} fits every demo but answers the query differently")
    return reasons


SEMANTIC_RIVALS = {
    "identity": _identity,
    "largest_only": _largest_only,
    "drop_thin": _drop_thin,
    "global_bbox": _global_bbox,
}
SEMANTIC_WITNESSES = {
    "interior_erased": _has_interior_erasure,
    "multiple_objects": _has_multiple_objects,
    "thin_rectangle": _has_thin_rectangle,
}
WITNESS_RIVALS = {
    "interior_erased": ["identity"],
    "multiple_objects": ["largest_only", "global_bbox"],
    "thin_rectangle": ["drop_thin"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
