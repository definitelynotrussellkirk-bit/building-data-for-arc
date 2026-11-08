"""Constructive generator for ARC task d1dab66b0d54 (original 5168d44c).

A regularly spaced green guide marks a positive row or column direction.  A
red 3x3 ring is centred on one green guide point.  The canonical rule erases
the red ring and translates it forward by one guide interval, preserving the
green guide.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d1dab66b0d54"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "76783c197f4d"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Find the equally spaced green guide cells. Infer their positive row/column "
    "interval, erase the red 3x3 ring, and translate every red cell forward by "
    "one guide interval while leaving the green guide unchanged."
)

INVARIANTS = [
    "background is 0 and the only foreground colors are red 2 and green 3",
    "at least three green cells form one equally spaced horizontal or vertical guide",
    "exactly eight red cells form the perimeter of a 3x3 ring around a green guide cell",
    "the ring has a later guide point and its forward translation remains in bounds",
]

ANCHOR_ORIENTATIONS = ("col", "row")
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-weighted 9..30", "valid": "9..30"},
    "grid_w": {"type": "int", "default": "difficulty-weighted 9..30", "valid": "9..30"},
    "anchor_orientation": {"type": "str", "default": "keyed choice", "valid": "col|row"},
    "spacing": {"type": "int", "default": "feasible keyed choice", "valid": "2..5"},
    "guide_count": {"type": "int", "default": "feasible keyed choice", "valid": "4..9"},
    "source_index": {"type": "int", "default": "0..guide_count-3", "valid": "0..6"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _exact_int(value: Any, lower: int, upper: int, name: str) -> int:
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an exact integer in {lower}..{upper}")
    return value


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> str:
    _exact_int(seed, -(2**63), 2**63 - 1, "seed")
    _exact_int(sample_index, 0, 2**63 - 1, "sample_index")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    for name, bounds in {
        "grid_h": (9, 30),
        "grid_w": (9, 30),
        "spacing": (2, 5),
        "guide_count": (4, 9),
        "source_index": (0, 6),
    }.items():
        if name in overrides and overrides[name] is not None:
            _exact_int(overrides[name], *bounds, name)
    if "anchor_orientation" in overrides and overrides["anchor_orientation"] is not None:
        if type(overrides["anchor_orientation"]) is not str or overrides["anchor_orientation"] not in ANCHOR_ORIENTATIONS:
            raise ValueError("anchor_orientation must be 'col' or 'row'")
    return "medium" if difficulty is None else difficulty


def _dimension_options(band: str) -> list[int]:
    if band == "easy":
        return list(range(9, 15))
    if band == "hard":
        return list(range(20, 31))
    return list(range(12, 23))


def _build_scene(
    height: int,
    width: int,
    orientation: str,
    spacing: int,
    guide_count: int,
    source_index: int,
    *,
    start: int,
    cross: int,
) -> list[list[int]]:
    """Build one guide/ring scene from exact geometry controls."""
    height = _exact_int(height, 3, 30, "height")
    width = _exact_int(width, 3, 30, "width")
    spacing = _exact_int(spacing, 1, 29, "spacing")
    guide_count = _exact_int(guide_count, 3, 15, "guide_count")
    source_index = _exact_int(source_index, 0, guide_count - 2, "source_index")
    if orientation not in ANCHOR_ORIENTATIONS:
        raise ValueError("orientation must be 'col' or 'row'")
    axis_length = height if orientation == "col" else width
    cross_length = width if orientation == "col" else height
    last = start + (guide_count - 1) * spacing
    if not (1 <= start <= last <= axis_length - 2):
        raise ValueError("guide must keep a one-cell margin on its movement axis")
    if not 1 <= cross <= cross_length - 2:
        raise ValueError("ring centre must keep a one-cell cross-axis margin")

    grid = full_grid(height, width, 0)
    guides = []
    for index in range(guide_count):
        axis = start + index * spacing
        point = (axis, cross) if orientation == "col" else (cross, axis)
        guides.append(point)
        grid[point[0]][point[1]] = 3
    center_r, center_c = guides[source_index]
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr or dc:
                grid[center_r + dr][center_c + dc] = 2
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    dimension_domain = list(range(9, 31)) if any(k in overrides for k in ("grid_h", "grid_w")) else _dimension_options(band)
    height = ctx.draw_choice("grid_h", dimension_domain)
    width = ctx.draw_choice("grid_w", dimension_domain)
    orientation = ctx.draw_choice("anchor_orientation", list(ANCHOR_ORIENTATIONS))
    axis_length = height if orientation == "col" else width

    feasible = [
        (spacing, count)
        for spacing in range(2, 6)
        for count in range(4, 10)
        if (count - 1) * spacing <= axis_length - 3
    ]
    requested_spacing = overrides.get("spacing")
    requested_count = overrides.get("guide_count")
    if requested_spacing is not None:
        feasible = [pair for pair in feasible if pair[0] == requested_spacing]
    if requested_count is not None:
        feasible = [pair for pair in feasible if pair[1] == requested_count]
    if not feasible:
        raise ValueError("grid/orientation/spacing/guide_count combination is infeasible")

    spacing_options = sorted({pair[0] for pair in feasible})
    spacing = ctx.draw_choice("spacing", spacing_options)
    count_options = sorted({count for sp, count in feasible if sp == spacing})
    guide_count = ctx.draw_choice("guide_count", count_options)
    source_options = list(range(0, guide_count - 2))
    if overrides.get("source_index") is not None and overrides["source_index"] not in source_options:
        raise ValueError("source_index must leave two later guide positions")
    source_index = ctx.draw_choice("source_index", source_options)

    rng = ctx.draw_rng("layout")
    axis_span = (guide_count - 1) * spacing
    start = rng.randint(1, axis_length - axis_span - 2)
    cross_length = width if orientation == "col" else height
    cross = rng.randint(1, cross_length - 2)
    grid = _build_scene(
        height,
        width,
        orientation,
        spacing,
        guide_count,
        source_index,
        start=start,
        cross=cross,
    )
    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructed invalid guide scene: " + "; ".join(errors))
    return grid


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return {"errors": ["empty or non-grid input"]}
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return {"errors": ["ragged grid"]}
    if len(grid) > 30 or width > 30:
        errors.append("grid exceeds 30x30")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return {"errors": errors + ["grid contains non-integer or out-of-range colors"]}
    colors = {value for row in grid for value in row}
    if not colors <= {0, 2, 3}:
        errors.append("only colors 0, 2, and 3 are allowed")

    greens = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    reds = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if len(greens) < 3:
        errors.append("at least three green guide cells are required")
    orientation = None
    spacing = None
    ordered: list[tuple[int, int]] = []
    if greens:
        same_row = len({r for r, _ in greens}) == 1
        same_col = len({c for _, c in greens}) == 1
        if same_row == same_col:
            errors.append("green cells must form exactly one horizontal or vertical guide")
        else:
            orientation = "row" if same_row else "col"
            ordered = sorted(greens, key=(lambda p: p[1]) if same_row else (lambda p: p[0]))
            coordinates = [p[1] if same_row else p[0] for p in ordered]
            gaps = [b - a for a, b in zip(coordinates, coordinates[1:])]
            if not gaps or len(set(gaps)) != 1 or gaps[0] <= 0:
                errors.append("green guide cells must be equally spaced")
            else:
                spacing = gaps[0]

    center = None
    source_index = None
    if len(reds) != 8:
        errors.append(f"red mover must contain exactly eight cells, got {len(reds)}")
    else:
        min_r, max_r = min(r for r, _ in reds), max(r for r, _ in reds)
        min_c, max_c = min(c for _, c in reds), max(c for _, c in reds)
        if max_r - min_r != 2 or max_c - min_c != 2:
            errors.append("red cells must span a 3x3 ring")
        else:
            center = (min_r + 1, min_c + 1)
            expected = {
                (center[0] + dr, center[1] + dc)
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
                if dr or dc
            }
            if set(reds) != expected:
                errors.append("red cells must be the complete 3x3 perimeter")
            if center not in greens:
                errors.append("red ring must be centred on a green guide cell")
            elif ordered:
                source_index = ordered.index(center)
                if source_index >= len(ordered) - 1:
                    errors.append("red ring needs a later guide cell for forward motion")

    if orientation is not None and spacing is not None and reds:
        dr, dc = (spacing, 0) if orientation == "col" else (0, spacing)
        height = len(grid)
        if any(not (0 <= r + dr < height and 0 <= c + dc < width) for r, c in reds):
            errors.append("forward red translation leaves the grid")

    return {
        "errors": errors,
        "height": len(grid),
        "width": width,
        "orientation": orientation,
        "spacing": spacing,
        "guide_count": len(greens),
        "source_index": source_index,
        "greens": ordered,
        "reds": reds,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe controls: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "anchor_orientation": analysis["orientation"],
        "spacing": analysis["spacing"],
        "guide_count": analysis["guide_count"],
        "source_index": analysis["source_index"],
    }


def rule_mirror(grid):
    """Python mirror of the selected canonical Racket program."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid guide scene: " + "; ".join(analysis["errors"]))
    dr, dc = (analysis["spacing"], 0) if analysis["orientation"] == "col" else (0, analysis["spacing"])
    output = [row[:] for row in grid]
    for r, c in analysis["reds"]:
        output[r][c] = 0
    for r, c in analysis["reds"]:
        output[r + dr][c + dc] = 2
    return output


def semantic_features(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid guide scene: " + "; ".join(analysis["errors"]))
    return {
        "height": analysis["height"],
        "width": analysis["width"],
        "orientation": analysis["orientation"],
        "spacing": analysis["spacing"],
        "guide_count": analysis["guide_count"],
        "source_index": analysis["source_index"],
        "red_count": len(analysis["reds"]),
    }
