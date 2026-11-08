"""Constructive inputs for the cell-count sort-and-pack task.

The selected Racket rule extracts every same-color 4-connected object, sorts
objects by occupied-cell count (then top row and left column), crops each
bounding box, and packs the nonzero crop cells left-to-right with one blank
column between crops.

Canonical examples contain only solid rectangles, so sorting by bounding-box
area is an especially strong rival: it agrees on every canonical label.  The
ordinary schedule therefore retains a solid-rectangle slice while emitting a
3x3 five-cell L beside a six-cell rectangle on two of every three draws.  That
pair reverses order under occupied-cell count versus bounding-box area.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.palette import random_palette

GENERATOR_ID = "dfa9d0b2dd41"
TASK_ID = GENERATOR_ID
RULE_HASH = "76c3cefee423"
VERSION = "2.0.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

SUMMARY = (
    "Two to four isolated, differently colored objects with distinct occupied "
    "cell counts. The selected rule sorts by occupied cells and packs bbox crops; "
    "two of every three ordinary samples refute the canonical-fitting bbox-area shortcut."
)

INVARIANTS = [
    "background is 0; grids are 8..14 rows by 10..18 columns",
    "2..4 same-color 4-connected objects use distinct nonzero colors",
    "object occupied-cell counts are distinct",
    "objects have a one-cell eight-neighbor moat",
    "ordinary schedule alternates solid-rectangle anchors with bbox-area counterexamples",
]

# The retired palette_kind/palette_size/position_bias/n_distinct_colors/density/
# texture controls were aliases, constants, or no-ops. Every remaining axis is
# exact, independently observable in returned pixels, and feasible in every band.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "exact canonical-profile anchor; difficulty-sensitive cycle",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "exact canonical-profile anchor; difficulty-sensitive cycle",
        "valid": "10..18",
    },
    "n_objs": {
        "type": "int",
        "default": "3 or 4 from the selected canonical profile",
        "valid": "2..4",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
SCHEDULE_PROFILES = ("solid_rectangles", "bbox_area_witness")
_CANONICAL_PROFILES = (
    (10, 12, 3),
    (11, 13, 3),
    (9, 14, 3),
    (12, 15, 4),
)
_BAND_OFFSET = {None: 0, "easy": 0, "medium": 1, "hard": 2}
_COLORS = tuple(range(1, 10))

# Shapes are normalized (row, column) coordinates. Every generated shape fits a
# 3x3 slot, which makes all declared h/w/n combinations constructively feasible.
_SOLID_SHAPES = {
    2: (((0, 0), (0, 1)), ((0, 0), (1, 0))),
    3: (((0, 0), (0, 1), (0, 2)), ((0, 0), (1, 0), (2, 0))),
    4: (((0, 0), (0, 1), (1, 0), (1, 1)),),
    6: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
    ),
    9: (tuple((row, col) for row in range(3) for col in range(3)),),
}
_L_FIVE = ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """One rectangular anchor followed by two bbox-area counterexamples.

    Any four consecutive materialized pairs therefore leave at least one
    counterexample among the three demonstrations under every query rotation.
    """
    del seed, difficulty
    return "solid_rectangles" if sample_index % 3 == 0 else "bbox_area_witness"


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be an integer, not bool")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in _BAND_OFFSET:
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown or retired override axes: {unknown}")
    bounds = {"grid_h": (8, 14), "grid_w": (10, 18), "n_objs": (2, 4)}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        low, high = bounds[name]
        if not low <= value <= high:
            raise ValueError(f"{name}={value} outside [{low}, {high}]")


def _default_axes(ctx, seed: int, sample_index: int, difficulty):
    index = (sample_index + _BAND_OFFSET[difficulty]) % len(_CANONICAL_PROFILES)
    height, width, count = _CANONICAL_PROFILES[index]
    return (
        ctx.draw_int_strict("grid_h", height, height),
        ctx.draw_int_strict("grid_w", width, width),
        ctx.draw_int_strict("n_objs", count, count),
    )


def _broad_axes(ctx):
    # draw_int_diff keeps full public bounds in provenance while making default
    # partial-override draws difficulty-sensitive. _validate_call already
    # enforces strict override scalar types.
    return (
        int(ctx.draw_int_diff("grid_h", 8, 14)),
        int(ctx.draw_int_diff("grid_w", 10, 18)),
        int(ctx.draw_int_diff("n_objs", 2, 4)),
    )


def _normalize(shape):
    row0 = min(row for row, _ in shape)
    col0 = min(col for _, col in shape)
    return tuple(sorted((row - row0, col - col0) for row, col in shape))


def _dihedral(shape, index: int):
    points = tuple(shape)
    if index >= 4:
        points = tuple((row, -col) for row, col in points)
    for _ in range(index % 4):
        points = tuple((col, -row) for row, col in points)
    return _normalize(points)


def _solid_specs(count: int, rng):
    size_sets = {
        2: (2, 9),
        3: (2, 4, 9),
        4: (2, 3, 6, 9),
    }
    specs = []
    for size in size_sets[count]:
        shape = rng.choice(_SOLID_SHAPES[size])
        specs.append((size, _dihedral(shape, rng.randrange(8))))
    return specs


def _witness_specs(count: int, rng):
    extras = {2: (), 3: (9,), 4: (2, 9)}[count]
    specs = []
    for size in extras:
        shape = rng.choice(_SOLID_SHAPES[size])
        specs.append((size, _dihedral(shape, rng.randrange(8))))
    specs.append((5, _dihedral(_L_FIVE, rng.randrange(8))))
    six = rng.choice(_SOLID_SHAPES[6])
    specs.append((6, _dihedral(six, rng.randrange(8))))
    return specs


def _place_constructively(height: int, width: int, specs, palette, rng):
    """Place at most four <=3x3 shapes in separated 3x3 slots.

    The four slot origins occupy a 7x7 footprint. A random global offset, slot
    permutation, object permutation, orientation, and palette assignment remove
    size/color/position correlations without any rejection loop or silent drop.
    """
    row_offset = rng.randrange(height - 7 + 1)
    col_offset = rng.randrange(width - 7 + 1)
    slots = [
        (row_offset, col_offset),
        (row_offset, col_offset + 4),
        (row_offset + 4, col_offset),
        (row_offset + 4, col_offset + 4),
    ]
    rng.shuffle(slots)
    specs = list(specs)
    rng.shuffle(specs)
    colors = list(palette)
    rng.shuffle(colors)

    grid = full_grid(height, width, 0)
    for (_, shape), color, (row0, col0) in zip(specs, colors, slots):
        for row, col in shape:
            grid[row0 + row][col0 + col] = color
    return grid


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
    effective_overrides = {name: value for name, value in overrides.items() if value is not None}
    if not effective_overrides:
        height, width, count = _default_axes(ctx, seed, sample_index, difficulty)
    else:
        height, width, count = _broad_axes(ctx)

    profile = schedule_profile(seed, sample_index, difficulty)
    shape_rng = ctx.draw_rng(f"shape_recipe:{profile}:{difficulty or 'none'}")
    specs = (
        _solid_specs(count, shape_rng)
        if profile == "solid_rectangles"
        else _witness_specs(count, shape_rng)
    )
    palette = random_palette(ctx.draw_rng(f"palette:{difficulty or 'none'}"), count)
    grid = _place_constructively(
        height,
        width,
        specs,
        palette,
        ctx.draw_rng(f"layout:{profile}:{difficulty or 'none'}"),
    )
    errors = self_check(grid, difficulty=difficulty)
    if errors:  # construction invariant: fail loud rather than return bad data
        raise ValueError(f"constructive rectangle-sort generator defect: {errors}")
    return grid


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal integer ARC colors 0..9"]
    return []


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            todo = [(row, col)]
            seen.add((row, col))
            cells = []
            while todo:
                r, c = todo.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append(tuple(sorted(cells)))
    return result


def _bounds(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def observe_overrides(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_objs": len(_components(grid)) if grid and grid[0] else 0,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not 8 <= height <= 14 or not 10 <= width <= 18:
        errors.append("shape must be within 8..14 rows by 10..18 columns")

    comps = _components(grid)
    if not 2 <= len(comps) <= 4:
        errors.append(f"expected 2..4 objects, found {len(comps)}")
        return errors

    colors = [grid[cells[0][0]][cells[0][1]] for cells in comps]
    if len(colors) != len(set(colors)):
        errors.append("objects must use distinct colors")
    sizes = [len(cells) for cells in comps]
    if len(sizes) != len(set(sizes)):
        errors.append(f"object occupied-cell counts must be distinct, got {sorted(sizes)}")

    owner = {cell: index for index, cells in enumerate(comps) for cell in cells}
    for (row, col), index in owner.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                neighbor = (row + dr, col + dc)
                if neighbor in owner and owner[neighbor] != index:
                    errors.append("distinct objects touch or violate the one-cell moat")
                    return errors
    return errors


def _item(grid, cells):
    row1, col1, row2, col2 = _bounds(cells)
    return {
        "cells": cells,
        "row1": row1,
        "col1": col1,
        "height": row2 - row1 + 1,
        "width": col2 - col1 + 1,
        "crop": [list(row[col1 : col2 + 1]) for row in grid[row1 : row2 + 1]],
    }


def _pack(grid, primary):
    items = [_item(grid, cells) for cells in _components(grid)]
    if not items:
        return deepcopy(grid)
    items.sort(key=lambda item: (primary(item), item["row1"], item["col1"]))
    out_height = max(item["height"] for item in items)
    out_width = sum(item["width"] for item in items) + len(items) - 1
    out = full_grid(out_height, out_width, 0)
    left = 0
    for item in items:
        for row, values in enumerate(item["crop"]):
            for col, value in enumerate(values):
                if value != 0:
                    out[row][left + col] = value
        left += item["width"] + 1
    return out


def _intended_output(grid):
    return _pack(grid, lambda item: len(item["cells"]))


def _bbox_area_sort(grid):
    return _pack(grid, lambda item: item["height"] * item["width"])


def _cell_count_not_bbox_area(grid) -> bool:
    try:
        return _intended_output(grid) != _bbox_area_sort(grid)
    except Exception:
        return False


def strict_canonical_like(grid) -> list[str]:
    """Canonical manifold: lawful inputs whose objects are solid rectangles."""
    errors = self_check(grid)
    if errors:
        return errors
    for cells in _components(grid):
        row1, col1, row2, col2 = _bounds(cells)
        if len(cells) != (row2 - row1 + 1) * (col2 - col1 + 1):
            errors.append("canonical-like objects must fill their bounding rectangles")
            break
    return errors


SEMANTIC_WITNESSES = {
    "cell_count_not_bbox_area": _cell_count_not_bbox_area,
}
SEMANTIC_RIVALS = {
    "bbox_area_sort": _bbox_area_sort,
}
WITNESS_RIVALS = {
    "cell_count_not_bbox_area": ["bbox_area_sort"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query=None) -> list[str]:
    """Finite declared-rival check; not a universal induction proof."""
    del query
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    findings = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        except Exception as exc:
            findings.append(f"declared rival {name} crashed: {type(exc).__name__}: {exc}")
            continue
        if survives:
            findings.append(f"declared rival survives all demonstrations: {name}")
    return findings
