"""Generator for ARC task 4e05481a2c21, "Pack the hole patterns".

The selected rule extracts every *enclosed* zero region from each colored
object, recolors the union with that object's color, crops it, and packs the
patterns left-to-right.  This sampler keeps the canonical two-object scale but
adds three topology profiles that distinguish the rule from canonical-fitting
shortcuts:

* rectangle: one rectangular hole per object;
* notched: a connected, nonrectangular hole plus an exterior bbox corner;
* split: two enclosed regions plus an exterior bbox corner.

Four demonstrations are used.  The five-pair schedule
``notched, split, notched, split, rectangle`` makes every query rotation retain
at least one notched and one split demonstration.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4e05481a2c21"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "e13b35a51ff4"
SUMMARY = (
    "Canonical-scale 5..8 x 10..16 grids with two separated, distinctly "
    "colored hollow objects. Enclosed hole unions can be rectangular, "
    "nonrectangular, or split into multiple regions; complex profiles also "
    "include an exterior bbox corner. The rule extracts only enclosed zero "
    "regions, crops each union, recolors it by its object, and packs patterns "
    "left-to-right with one background column."
)

INVARIANTS = [
    "background is color 0",
    "there are exactly two separated 4-connected objects in distinct colors",
    "each object has at least one enclosed zero region",
    "object bboxes are 3..5 cells per side and may omit at most one corner",
    "the output order is determined by each object's leftmost column",
]

PALETTE_KINDS = ("canonical", "warm", "cool", "varied")
PATTERN_KINDS = ("rectangle", "notched", "split")
PALETTES = {
    "canonical": (2, 3),
    "warm": (4, 6),
    "cool": (1, 8),
    "varied": (5, 9),
}
PALETTE_BY_COLORS = {frozenset(colors): name for name, colors in PALETTES.items()}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted",
        "valid": "5..8",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted with canonical 12/14 anchors",
        "valid": "10..16",
    },
    "palette_kind": {
        "type": "str",
        "default": "rng",
        "valid": "canonical|warm|cool|varied",
    },
    "pattern_kind": {
        "type": "str",
        "default": "five-pair teaching schedule",
        "valid": "rectangle|notched|split",
    },
}

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
_PATTERN_SCHEDULE = ("notched", "split", "notched", "split", "rectangle")
SCHEDULE_PROFILES = PATTERN_KINDS

_HEIGHT_OPTIONS = {
    None: (5, 6, 6, 6, 7, 8),
    "easy": (5, 5, 5, 6, 6, 7, 8),
    "medium": (5, 6, 6, 6, 7, 7, 8),
    "hard": (5, 6, 7, 7, 8, 8, 8),
}
_WIDTH_OPTIONS = {
    None: (10, 11, 12, 12, 12, 13, 14, 14, 15, 16),
    "easy": (10, 11, 12, 12, 12, 12, 13, 14, 15, 16),
    "medium": (10, 11, 12, 12, 13, 14, 14, 15, 16),
    "hard": (10, 11, 12, 13, 14, 14, 15, 16, 16),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the topology branch selected by the deterministic lesson schedule."""
    del seed, difficulty
    return _PATTERN_SCHEDULE[sample_index % len(_PATTERN_SCHEDULE)]


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for key in ("grid_h", "grid_w"):
        value = overrides.get(key)
        if value is not None and type(value) is not int:
            raise TypeError(f"{key} override must be an integer (not bool)")
    for key in ("palette_kind", "pattern_kind"):
        value = overrides.get(key)
        if value is not None and type(value) is not str:
            raise TypeError(f"{key} override must be a string")


def _draw_scheduled_pattern(ctx, seed, sample_index, difficulty, overrides):
    if overrides.get("pattern_kind") is not None:
        return ctx.draw_choice("pattern_kind", PATTERN_KINDS)
    scheduled = schedule_profile(seed, sample_index, difficulty)
    return ctx.draw_choice("pattern_kind", (scheduled,))


def _draw_frame(grid, top, left, height, width, color):
    for row in range(top, top + height):
        for col in range(left, left + width):
            grid[row][col] = color
    for row in range(top + 1, top + height - 1):
        for col in range(left + 1, left + width - 1):
            grid[row][col] = 0


def _apply_complex_profile(grid, top, left, color, pattern_kind, rng):
    """Modify a 5x5 ring while preserving its enclosed topology."""
    if pattern_kind == "notched":
        stem = (
            (top + 1, left + 2),
            (top + 2, left + 3),
            (top + 3, left + 2),
            (top + 2, left + 1),
        )[rng.randrange(4)]
        grid[stem[0]][stem[1]] = color
    elif pattern_kind == "split":
        if rng.randrange(2):
            for row in range(top + 1, top + 4):
                grid[row][left + 2] = color
        else:
            for col in range(left + 1, left + 4):
                grid[top + 2][col] = color
    else:
        return

    # Removing a corner creates an exterior bbox zero without opening the
    # interior under 4-connectivity.  This distinguishes enclosed-region
    # extraction from the canonical-fitting "all bbox zeros" shortcut.
    corner = (
        (top, left),
        (top, left + 4),
        (top + 4, left),
        (top + 4, left + 4),
    )[rng.randrange(4)]
    grid[corner[0]][corner[1]] = 0


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

    band = difficulty if difficulty in ("easy", "medium", "hard") else None
    height = ctx.draw_choice("grid_h", _HEIGHT_OPTIONS[band])
    width = ctx.draw_choice("grid_w", _WIDTH_OPTIONS[band])
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    pattern_kind = _draw_scheduled_pattern(
        ctx, seed, sample_index, difficulty, overrides
    )

    layout_rng = ctx.draw_rng("layout")
    pattern_rng = ctx.draw_rng("pattern_geometry")
    colors = list(PALETTES[palette_kind])
    if ctx.draw_rng("color_order").randrange(2):
        colors.reverse()

    if pattern_kind == "rectangle":
        first_h = layout_rng.randint(3, min(5, height))
        first_w = layout_rng.randint(3, 5)
    else:
        first_h = first_w = 5

    max_second_w = min(5, width - first_w - 1)
    if max_second_w < 3:  # Defensive: declared dimensions make this unreachable.
        raise ValueError("grid width cannot fit two separated frames")
    second_h = layout_rng.randint(3, min(5, height))
    second_w = layout_rng.randint(3, max_second_w)

    max_gap = width - first_w - second_w
    gap = layout_rng.randint(1, min(3, max_gap))
    slack = width - first_w - second_w - gap
    first_left = layout_rng.randint(0, slack)
    second_left = first_left + first_w + gap
    first_top = layout_rng.randint(0, height - first_h)
    second_top = layout_rng.randint(0, height - second_h)

    grid = full_grid(height, width, 0)
    _draw_frame(grid, first_top, first_left, first_h, first_w, colors[0])
    _apply_complex_profile(
        grid, first_top, first_left, colors[0], pattern_kind, pattern_rng
    )
    _draw_frame(grid, second_top, second_left, second_h, second_w, colors[1])
    return grid


def _grid_error(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected a nonempty rectangular grid"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "grid must be rectangular"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "cells must be integer ARC colors 0..9"
    return None


def _bbox(cells: Iterable[tuple[int, int]]):
    cells = tuple(cells)
    if not cells:
        raise ValueError("empty cell collection")
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = [(row, col)]
            seen.add((row, col))
            cells = []
            for rr, cc in queue:
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append((color, frozenset(cells)))
    return result


def _enclosed_regions(component_cells):
    occupied = set(component_cells)
    r0, c0, r1, c1 = _bbox(occupied)
    zeros = {
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if (row, col) not in occupied
    }
    seen = set()
    regions = []
    for start in sorted(zeros):
        if start in seen:
            continue
        queue = [start]
        seen.add(start)
        region = []
        touches_boundary = False
        for row, col in queue:
            region.append((row, col))
            touches_boundary |= row in (r0, r1) or col in (c0, c1)
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = row + dr, col + dc
                if nxt in zeros and nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        if not touches_boundary:
            regions.append(frozenset(region))
    return regions


def _object_records(grid):
    records = []
    for color, cells in _components(grid):
        records.append({
            "color": color,
            "cells": cells,
            "bbox": _bbox(cells),
            "regions": _enclosed_regions(cells),
        })
    return sorted(records, key=lambda record: record["bbox"][1])


def _normalized(cells):
    r0, c0, r1, c1 = _bbox(cells)
    shape = frozenset((row - r0, col - c0) for row, col in cells)
    return shape, r1 - r0 + 1, c1 - c0 + 1


def _pack(items):
    if not items:
        return []
    height = max(item[1] for item in items)
    width = sum(item[2] for item in items) + len(items) - 1
    output = full_grid(height, width, 0)
    left = 0
    for shape, shape_h, shape_w, color in items:
        del shape_h
        for row, col in shape:
            output[row][left + col] = color
        left += shape_w + 1
    return output


def _reference_output(grid):
    """Pure Python mirror used only for rivals, hooks, and regression probes."""
    items = []
    for record in _object_records(grid):
        holes = (
            frozenset().union(*record["regions"])
            if record["regions"] else frozenset()
        )
        if not holes:
            continue
        shape, height, width = _normalized(holes)
        items.append((shape, height, width, record["color"]))
    return _pack(items)


def _fill_hole_bbox(grid):
    items = []
    for record in _object_records(grid):
        holes = (
            frozenset().union(*record["regions"])
            if record["regions"] else frozenset()
        )
        if not holes:
            continue
        _, height, width = _normalized(holes)
        shape = frozenset(
            (row, col) for row in range(height) for col in range(width)
        )
        items.append((shape, height, width, record["color"]))
    return _pack(items)


def _largest_region_only(grid):
    items = []
    for record in _object_records(grid):
        if not record["regions"]:
            continue
        region = sorted(
            record["regions"], key=lambda cells: (-len(cells), sorted(cells))
        )[0]
        shape, height, width = _normalized(region)
        items.append((shape, height, width, record["color"]))
    return _pack(items)


def _all_bbox_zeros(grid):
    items = []
    for record in _object_records(grid):
        r0, c0, r1, c1 = record["bbox"]
        zeros = frozenset(
            (row, col)
            for row in range(r0, r1 + 1)
            for col in range(c0, c1 + 1)
            if grid[row][col] == 0
        )
        if not zeros:
            continue
        shape, height, width = _normalized(zeros)
        items.append((shape, height, width, record["color"]))
    return _pack(items)


def _has_nonrectangular_hole(grid):
    for record in _object_records(grid):
        holes = (
            frozenset().union(*record["regions"])
            if record["regions"] else frozenset()
        )
        if not holes:
            continue
        _, height, width = _normalized(holes)
        if len(holes) != height * width:
            return True
    return False


def _has_multiple_hole_regions(grid):
    return any(len(record["regions"]) > 1 for record in _object_records(grid))


def _has_exterior_bbox_zero(grid):
    for record in _object_records(grid):
        r0, c0, r1, c1 = record["bbox"]
        cells = record["cells"]
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                if ((row in (r0, r1) or col in (c0, c1))
                        and (row, col) not in cells):
                    return True
    return False


def _classify_pattern(records):
    if any(len(record["regions"]) > 1 for record in records):
        return "split"
    for record in records:
        holes = (
            frozenset().union(*record["regions"])
            if record["regions"] else frozenset()
        )
        if holes:
            _, height, width = _normalized(holes)
            if len(holes) != height * width:
                return "notched"
    return "rectangle"


def observe_overrides(grid):
    error = _grid_error(grid)
    if error:
        raise ValueError(error)
    records = _object_records(grid)
    colors = frozenset(record["color"] for record in records)
    if colors not in PALETTE_BY_COLORS:
        raise ValueError(f"unrecognized generated palette {sorted(colors)}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette_kind": PALETTE_BY_COLORS[colors],
        "pattern_kind": _classify_pattern(records),
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the documented two-object topology without using draw metadata."""
    del difficulty, meta
    error = _grid_error(grid)
    if error:
        return [error]
    height, width = len(grid), len(grid[0])
    errors = []
    if not (5 <= height <= 8 and 10 <= width <= 16):
        errors.append(
            f"grid size {height}x{width} outside declared 5..8 x 10..16"
        )

    records = _object_records(grid)
    if len(records) != 2:
        errors.append(f"expected exactly two colored objects, found {len(records)}")
        return errors
    if len({record["color"] for record in records}) != 2:
        errors.append("objects must use distinct colors")

    left, right = records
    if right["bbox"][1] - left["bbox"][3] < 2:
        errors.append("objects must have at least one background column between them")

    for record in records:
        color = record["color"]
        r0, c0, r1, c1 = record["bbox"]
        obj_h, obj_w = r1 - r0 + 1, c1 - c0 + 1
        if not (3 <= obj_h <= 5 and 3 <= obj_w <= 5):
            errors.append(
                f"color {color} bbox {obj_h}x{obj_w} outside declared 3..5 range"
            )
        if any(
            grid[row][col] not in (0, color)
            for row in range(r0, r1 + 1)
            for col in range(c0, c1 + 1)
        ):
            errors.append(f"color {color} bbox contains another object's color")
        boundary_zeros = [
            (row, col)
            for row in range(r0, r1 + 1)
            for col in range(c0, c1 + 1)
            if (row in (r0, r1) or col in (c0, c1))
            and (row, col) not in record["cells"]
        ]
        corners = {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}
        if len(boundary_zeros) > 1 or any(cell not in corners for cell in boundary_zeros):
            errors.append(
                f"color {color} may omit at most one bbox corner, not {boundary_zeros}"
            )
        if not record["regions"]:
            errors.append(f"color {color} has no enclosed zero region")
        elif len(record["regions"]) > 2:
            errors.append(f"color {color} has more than two enclosed regions")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


SEMANTIC_WITNESSES = {
    "nonrectangular_hole": _has_nonrectangular_hole,
    "multiple_hole_regions": _has_multiple_hole_regions,
    "exterior_bbox_zero": _has_exterior_bbox_zero,
}
SEMANTIC_RIVALS = {
    "fill_hole_bbox": _fill_hole_bbox,
    "largest_region_only": _largest_region_only,
    "all_bbox_zeros": _all_bbox_zeros,
}
WITNESS_RIVALS = {
    "nonrectangular_hole": ["fill_hole_bbox"],
    "multiple_hole_regions": ["largest_region_only"],
    "exterior_bbox_zero": ["all_bbox_zeros"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Report declared rivals that fit every demo but alter the query answer."""
    if not isinstance(demos, list) or not isinstance(query, dict):
        return ["expected a list of demonstrations and one query pair"]
    if len(demos) < EXAMPLES_NEEDED:
        return [
            f"need {EXAMPLES_NEEDED} demonstrations for the declared schedule; "
            f"received {len(demos)}"
        ]
    reasons = []
    for name, rival in sorted(LESSON_COMPETITORS.items()):
        try:
            fits_demos = all(
                rival(deepcopy(pair["input"])) == pair["output"]
                for pair in demos
            )
            changes_query = (
                rival(deepcopy(query["input"])) != query["output"]
            )
        except Exception as exc:
            reasons.append(f"rival {name!r} could not be scored: {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(
                f"declared rival {name!r} fits every demonstration but changes the query"
            )
    return reasons
