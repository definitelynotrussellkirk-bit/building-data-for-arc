"""Constructive generator for ARC task d35dbdf1cfc2 (H63).

The input contains three to five isolated, differently coloured motifs.  The
canonical transformation crops each motif, rotates a crop clockwise when it
is taller than wide, sorts by (cell count descending, colour ascending), and
packs the crops left-to-right with one background column between them.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d35dbdf1cfc2"
TASK_ID = GENERATOR_ID
VERSION = "2.2.0"
RULE_HASH = "0d1461c8b2f0"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Extract the three to five isolated same-colour motifs. Crop each motif; "
    "rotate a crop 90° clockwise only when it is taller than wide. Sort the "
    "resulting crops by motif size descending and colour ascending, then pack "
    "them left-to-right with one zero column between adjacent crops."
)

INVARIANTS = [
    "background is 0 and is strictly modal",
    "3-5 four-connected motifs use distinct non-zero colours",
    "every motif has 3-5 cells and every pair has a one-cell Chebyshev buffer",
    "at least two normalized motif shapes occur",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
PALETTES = {
    "default": (1, 2, 3, 4, 5),
    "warm": (2, 4, 7, 9, 1),
    "cool": (3, 5, 6, 8, 9),
    "varied": (1, 6, 7, 8, 9),
}
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-weighted 9..30", "valid": "9..30"},
    "grid_w": {"type": "int", "default": "difficulty-weighted 9..30", "valid": "9..30"},
    "n": {"type": "int", "default": "difficulty-weighted 3..5", "valid": "3..5"},
    "palette_kind": {"type": "str", "default": "keyed choice", "valid": "default|warm|cool|varied"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"when": {"n": 5}, "requires": {"grid_h": ">=11", "grid_w": ">=11"}},
]

# Every template is 4-connected and has a bounding box no larger than 3x3.
_TEMPLATES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    3: (
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    5: (
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2)),
    ),
}
_SIZE_SCHEDULES = {
    3: (3, 4, 5),
    4: (3, 4, 5, 4),
    5: (3, 4, 5, 3, 5),
}
_CORNER_SLOTS = ("top_left", "top_right", "bottom_left", "bottom_right")


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
    for name, bounds in {"grid_h": (9, 30), "grid_w": (9, 30), "n": (3, 5)}.items():
        if name in overrides and overrides[name] is not None:
            _exact_int(overrides[name], *bounds, name)
    if "palette_kind" in overrides and overrides["palette_kind"] is not None:
        value = overrides["palette_kind"]
        if type(value) is not str or value not in PALETTE_KINDS:
            raise ValueError("palette_kind must be default, warm, cool, or varied")
    return "medium" if difficulty is None else difficulty


def _dimension_options(band: str) -> list[int]:
    if band == "easy":
        return list(range(9, 15))
    if band == "hard":
        return list(range(15, 31))
    return list(range(11, 22))


def _count_options(band: str) -> list[int]:
    if band == "easy":
        return [3, 3, 3, 4]
    if band == "hard":
        return [4, 5, 5]
    return [3, 3, 4, 4, 5]


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    top = min(r for r, _ in points)
    left = min(c for _, c in points)
    return tuple(sorted((r - top, c - left) for r, c in points))


def _transform_template(
    cells: tuple[tuple[int, int], ...], rotations: int, reflect: bool
) -> tuple[tuple[int, int], ...]:
    result = tuple(cells)
    if reflect:
        result = _normalize((r, -c) for r, c in result)
    for _ in range(rotations % 4):
        result = _normalize((c, -r) for r, c in result)
    return _normalize(result)


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    points = tuple(cells)
    return (
        min(r for r, _ in points),
        min(c for _, c in points),
        max(r for r, _ in points),
        max(c for _, c in points),
    )


def _anchor(slot: str, height: int, width: int, shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    _, _, bottom, right = _bbox(shape)
    shape_h, shape_w = bottom + 1, right + 1
    if slot == "top_left":
        return 0, 0
    if slot == "top_right":
        return 0, width - shape_w
    if slot == "bottom_left":
        return height - shape_h, 0
    if slot == "bottom_right":
        return height - shape_h, width - shape_w
    if slot == "center":
        return (height - shape_h) // 2, (width - shape_w) // 2
    raise ValueError(f"unknown placement slot {slot!r}")


def _pair_distance(a: Iterable[tuple[int, int]], b: Iterable[tuple[int, int]]) -> int:
    return min(
        max(abs(ar - br), abs(ac - bc))
        for ar, ac in a
        for br, bc in b
    )


def _build_scene(
    height: int,
    width: int,
    colors: Iterable[int],
    shapes: Iterable[Iterable[tuple[int, int]]],
    slots: Iterable[str],
) -> list[list[int]]:
    """Place exact motifs at named spread slots, raising on any overlap/buffer defect."""
    height = _exact_int(height, 9, 30, "height")
    width = _exact_int(width, 9, 30, "width")
    colors = tuple(colors)
    shapes = tuple(_normalize(shape) for shape in shapes)
    slots = tuple(slots)
    if not (len(colors) == len(shapes) == len(slots)):
        raise ValueError("colors, shapes, and slots must have equal lengths")
    if not 3 <= len(colors) <= 5 or len(set(colors)) != len(colors):
        raise ValueError("scene requires 3-5 distinct motif colors")
    if any(type(color) is not int or not 1 <= color <= 9 for color in colors):
        raise ValueError("motif colors must be exact integers in 1..9")

    grid = full_grid(height, width, 0)
    placed: list[set[tuple[int, int]]] = []
    for color, shape, slot in zip(colors, shapes, slots):
        r0, c0 = _anchor(slot, height, width, shape)
        absolute = {(r0 + r, c0 + c) for r, c in shape}
        if any(not (0 <= r < height and 0 <= c < width) for r, c in absolute):
            raise ValueError("motif placement leaves the grid")
        if any(_pair_distance(absolute, previous) <= 1 for previous in placed):
            raise ValueError("motif placement violates the one-cell buffer")
        for r, c in absolute:
            if grid[r][c] != 0:
                raise ValueError("motif placement overlaps another motif")
            grid[r][c] = color
        placed.append(absolute)
    return grid


def _choose_shapes(ctx, count: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    rng = ctx.draw_rng("motif_shapes")
    shapes = []
    used: set[tuple[tuple[int, int], ...]] = set()
    for index, size in enumerate(_SIZE_SCHEDULES[count]):
        options = _TEMPLATES[size]
        base = options[(rng.randrange(len(options)) + index) % len(options)]
        candidate = _transform_template(base, rng.randrange(4), bool(rng.randrange(2)))
        # Exact duplicates are avoidable for equal-sized schedule entries.
        if candidate in used:
            for option in options:
                for rotation in range(4):
                    alternative = _transform_template(option, rotation, False)
                    if alternative not in used:
                        candidate = alternative
                        break
                if candidate not in used:
                    break
        used.add(candidate)
        shapes.append(candidate)
    return tuple(shapes)


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

    explicit_h = overrides.get("grid_h")
    explicit_w = overrides.get("grid_w")
    count_domain = list(dict.fromkeys(_count_options(band)))
    if (explicit_h is not None and explicit_h < 11) or (explicit_w is not None and explicit_w < 11):
        count_domain = [value for value in count_domain if value != 5]
    if overrides.get("n") is not None and overrides["n"] not in count_domain:
        if overrides["n"] == 5:
            raise ValueError("n=5 requires grid_h and grid_w of at least 11")
        count_domain = [overrides["n"]]
    count = ctx.draw_choice("n", count_domain)

    minimum = 11 if count == 5 else 9
    full_dimensions = list(range(minimum, 31))
    normal_dimensions = [value for value in _dimension_options(band) if value >= minimum]
    height = ctx.draw_choice("grid_h", full_dimensions if explicit_h is not None else normal_dimensions)
    width = ctx.draw_choice("grid_w", full_dimensions if explicit_w is not None else normal_dimensions)
    if count == 5 and (height < 11 or width < 11):
        raise ValueError("n=5 requires grid_h and grid_w of at least 11")

    palette_kind = ctx.draw_choice("palette_kind", list(PALETTE_KINDS))
    colors = list(PALETTES[palette_kind][:count])
    ctx.draw_rng("palette_order").shuffle(colors)
    shapes = list(_choose_shapes(ctx, count))

    placement_rng = ctx.draw_rng("placement_slots")
    if count == 3:
        slots = placement_rng.sample(list(_CORNER_SLOTS), 3)
    elif count == 4:
        slots = list(_CORNER_SLOTS)
        placement_rng.shuffle(slots)
    else:
        slots = list(_CORNER_SLOTS) + ["center"]
        placement_rng.shuffle(slots)

    grid = _build_scene(height, width, colors, shapes, slots)
    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructed invalid motif gallery: " + "; ".join(errors))
    objects = _extract_objects(grid)
    if len({len(obj["cells"]) for obj in objects}) < 2:
        raise RuntimeError("constructed gallery lacks motif-size contrast")
    return grid


def _grid_errors(grid: Any) -> tuple[list[str], int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["empty or non-grid input"], 0, 0
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["ragged grid"], len(grid), width
    errors: list[str] = []
    if len(grid) > 30 or width > 30:
        errors.append("grid exceeds 30x30")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
    return errors, len(grid), width


def _extract_objects(grid: Any) -> list[dict[str, Any]]:
    """Return every non-zero 4-connected component as an object record."""
    errors, height, width = _grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    objects: list[dict[str, Any]] = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        queue = deque([start])
        unseen.remove(start)
        cells: set[tuple[int, int]] = set()
        while queue:
            r, c = queue.popleft()
            cells.add((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    queue.append(point)
        r1, c1, r2, c2 = _bbox(cells)
        objects.append({
            "color": color,
            "cells": frozenset(cells),
            "r1": r1,
            "c1": c1,
            "r2": r2,
            "c2": c2,
        })
    return sorted(objects, key=lambda obj: (obj["r1"], obj["c1"], obj["color"]))


def _analyze(grid: Any) -> dict[str, Any]:
    errors, height, width = _grid_errors(grid)
    if errors and (height == 0 or width == 0 or any("ragged" in error for error in errors)):
        return {"errors": errors}
    try:
        objects = _extract_objects(grid)
    except ValueError as exc:
        return {"errors": errors + [str(exc)]}

    colors = [obj["color"] for obj in objects]
    if not 3 <= len(objects) <= 5:
        errors.append(f"expected 3-5 motifs; found {len(objects)}")
    if len(set(colors)) != len(colors):
        errors.append("motifs must use distinct colors; one color forms multiple components")
    for obj in objects:
        size = len(obj["cells"])
        if not 3 <= size <= 5:
            errors.append(f"motif color {obj['color']} must contain 3-5 cells; found {size}")
    for index, obj in enumerate(objects):
        for other in objects[index + 1:]:
            if _pair_distance(obj["cells"], other["cells"]) <= 1:
                errors.append(
                    f"motifs {obj['color']} and {other['color']} touch or lack a one-cell buffer"
                )
    shapes = {_normalize(obj["cells"]) for obj in objects}
    if len(shapes) < 2:
        errors.append("expected at least two distinct normalized motif shapes")

    zero_count = sum(value == 0 for row in grid for value in row)
    if zero_count * 2 <= height * width:
        errors.append("background 0 must be strictly modal")
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "objects": objects,
        "shapes": shapes,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe overrides: " + "; ".join(analysis["errors"]))
    count = len(analysis["objects"])
    colors = {obj["color"] for obj in analysis["objects"]}
    matches = [
        name
        for name, palette in PALETTES.items()
        if set(palette[:count]) == colors
    ]
    if len(matches) != 1:
        raise ValueError(f"motif colors do not identify one palette_kind: {sorted(colors)}")
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n": count,
        "palette_kind": matches[0],
    }


def _crop(grid: list[list[int]], obj: dict[str, Any]) -> list[list[int]]:
    return [
        row[obj["c1"]:obj["c2"] + 1]
        for row in grid[obj["r1"]:obj["r2"] + 1]
    ]


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _ordered_crops(grid: list[list[int]], *, descending: bool) -> list[list[list[int]]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid motif gallery: " + "; ".join(analysis["errors"]))
    items = []
    for obj in analysis["objects"]:
        crop = _crop(grid, obj)
        if len(crop) > len(crop[0]):
            crop = _rotate_cw(crop)
        items.append((len(obj["cells"]), obj["color"], crop))
    items.sort(key=(lambda item: (-item[0], item[1])) if descending
               else (lambda item: (item[0], item[1])))
    return [crop for _, _, crop in items]


def transform_order(grid: list[list[int]], order: str) -> list[list[int]]:
    if type(order) is not str or order not in ("size_desc", "size_asc"):
        raise ValueError("order must be 'size_desc' or 'size_asc'")
    crops = _ordered_crops(grid, descending=(order == "size_desc"))
    out_height = max(len(crop) for crop in crops)
    out_width = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    output = full_grid(out_height, out_width, 0)
    left = 0
    for crop in crops:
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                if value != 0:
                    output[r][left + c] = value
        left += len(crop[0]) + 1
    return output


def rule_mirror(grid):
    """Python mirror of the canonical size-descending Racket rule."""
    return transform_order(grid, "size_desc")


def semantic_features(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid motif gallery: " + "; ".join(analysis["errors"]))
    occupied = [cell for obj in analysis["objects"] for cell in obj["cells"]]
    return {
        "height": analysis["height"],
        "width": analysis["width"],
        "motif_count": len(analysis["objects"]),
        "colors": tuple(sorted(obj["color"] for obj in analysis["objects"])),
        "sizes": tuple(sorted(len(obj["cells"]) for obj in analysis["objects"])),
        "shape_count": len(analysis["shapes"]),
        "row_span": max(r for r, _ in occupied) - min(r for r, _ in occupied),
        "col_span": max(c for _, c in occupied) - min(c for _, c in occupied),
        "boundary_contact": any(
            r in (0, analysis["height"] - 1) or c in (0, analysis["width"] - 1)
            for r, c in occupied
        ),
    }
