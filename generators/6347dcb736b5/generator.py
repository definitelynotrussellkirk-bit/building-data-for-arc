"""Constructive sampler for task 6347dcb736b5: outline every object's bbox.

The unchanged Racket authority finds each same-colour 4-connected object and,
on a fresh zero canvas, draws that object's axis-aligned bounding-box perimeter
in the object's colour.  This module generates inputs only; ``rule_mirror`` is a
review/test mirror, not label authority.

Every generated grid includes one decisive object with a bbox at least 3x3 and
an occupied strict-interior cell.  Consequently each individual demonstration
separates the selected rule from both "fill each bbox" and "draw outlines over
the source without erasing interior cells".  A three-slot colour schedule also
places disconnected same-colour components in two slots out of three, refuting
the canonical-fitting shortcut that merges all cells of a colour into one bbox.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6347dcb736b5"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "6bba75bb466d"
SUMMARY = (
    "Two to five separated 4-connected blobs on a 0 background; consecutive "
    "lessons include disconnected blobs sharing a colour. "
    "Every blob is non-rectangular and one has a >=3x3 bbox with a source cell in "
    "its strict interior. The output redraws every object's bbox perimeter on a "
    "fresh zero canvas, adding missing border cells and erasing source interiors."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0; colours are in 1..9 and at most one colour labels two components",
    "2..5 same-colour 4-connected objects, each with a genuinely 2D bbox",
    "objects are non-rectangular and their bboxes are separated by background",
    "every generated grid has a >=3x3 witness object crossing its bbox interior",
    "two of every three sample-index slots repeat one colour across disconnected components",
    "canonical-sized profiles remain a high-probability curriculum component",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchors mixed with difficulty-weighted 6..14",
        "valid": "6..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchors mixed with difficulty-weighted 9..16",
        "valid": "9..16",
    },
    "n_blobs": {
        "type": "int",
        "default": "canonical anchors mixed with difficulty-weighted 2..5",
        "valid": "2..5",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Canonical input profiles represented as (height, width, palette size including
# background).  The object count is derived from the colour-schedule slot so
# both distinct and repeated-colour examples can hit these exact profiles.
_CANONICAL_PROFILES = ((6, 9, 3), (8, 9, 3), (8, 10, 4))
_CORE_MODES = ("core", "broad")
_GAP = 1

_FAVORED = {
    "grid_h": {
        "easy": (6, 7, 8, 9),
        "medium": (6, 7, 8, 9, 10, 11, 12),
        "hard": (9, 10, 11, 12, 13, 14),
    },
    "grid_w": {
        "easy": (9, 10, 11),
        "medium": (9, 10, 11, 12, 13, 14),
        "hard": (12, 13, 14, 15, 16),
    },
    "n_blobs": {
        "easy": (2, 2, 3, 3, 4, 5),
        "medium": (2, 3, 3, 4, 4, 5),
        "hard": (3, 4, 4, 5),
    },
}


def _draw_axis(ctx, name: str, lo: int, hi: int, difficulty, anchor=None) -> int:
    """Draw from the full declared domain while reweighting ordinary defaults."""
    if anchor is not None:
        favored = (anchor,) * 12
    else:
        band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
        favored = _FAVORED[name][band]
    # Overrides remain exact because every documented value is always present.
    choices = list(range(lo, hi + 1)) + [value for value in favored for _ in range(10)]
    return ctx.draw_choice(name, choices)


def _path(rng, start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
    """Random monotone 4-connected lattice path from start to end, inclusive."""
    (row, col), (end_row, end_col) = start, end
    steps = ["row"] * abs(end_row - row) + ["col"] * abs(end_col - col)
    rng.shuffle(steps)
    cells = [(row, col)]
    for step in steps:
        if step == "row":
            row += 1 if end_row > row else -1
        else:
            col += 1 if end_col > col else -1
        cells.append((row, col))
    return cells


def _shape(rng, box_h: int, box_w: int, *, crosses_interior: bool) -> list[tuple[int, int]]:
    """Connected non-rectangle touching all four sides of its local bbox."""
    interior = [
        (row, col)
        for row in range(1, box_h - 1)
        for col in range(1, box_w - 1)
    ]
    for _ in range(32):
        hub = rng.choice(interior) if crosses_interior else (
            rng.randrange(box_h),
            rng.randrange(box_w),
        )
        anchors = [
            (0, rng.randrange(box_w)),
            (box_h - 1, rng.randrange(box_w)),
            (rng.randrange(box_h), 0),
            (rng.randrange(box_h), box_w - 1),
        ]
        cells: set[tuple[int, int]] = set()
        for anchor in anchors:
            cells.update(_path(rng, anchor, hub))
        for _extra in range(rng.randint(0, 2)):
            frontier = sorted(
                {
                    (row + dr, col + dc)
                    for row, col in cells
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if 0 <= row + dr < box_h and 0 <= col + dc < box_w
                }
                - cells
            )
            if frontier and len(cells) + 1 < box_h * box_w:
                cells.add(rng.choice(frontier))
        if len(cells) < box_h * box_w:
            if not crosses_interior or any(
                0 < row < box_h - 1 and 0 < col < box_w - 1
                for row, col in cells
            ):
                return sorted(cells)

    # Deterministic non-solid fallback.  For a witness, both dimensions are >=3,
    # so the crossing cell is strict interior.  For a thin 2xK box this is an L/T.
    middle_row = (box_h - 1) // 2 if crosses_interior else 0
    middle_col = (box_w - 1) // 2
    cells = {(middle_row, col) for col in range(box_w)}
    cells.update((row, middle_col) for row in range(box_h))
    return sorted(cells)


def _place(rng, height: int, width: int, dims: list[tuple[int, int]], *, budget=100_000):
    """Backtracking placement of bboxes with a one-cell background separation."""
    order = sorted(range(len(dims)), key=lambda index: -dims[index][0] * dims[index][1])
    spots: list[tuple[int, int] | None] = [None] * len(dims)
    visited = 0

    def clashes(index: int, row: int, col: int) -> bool:
        box_h, box_w = dims[index]
        for other_index, spot in enumerate(spots):
            if spot is None:
                continue
            other_row, other_col = spot
            other_h, other_w = dims[other_index]
            if (
                row < other_row + other_h + _GAP
                and other_row < row + box_h + _GAP
                and col < other_col + other_w + _GAP
                and other_col < col + box_w + _GAP
            ):
                return True
        return False

    def search(position: int) -> bool:
        nonlocal visited
        if position == len(order):
            return True
        index = order[position]
        box_h, box_w = dims[index]
        options = [
            (row, col)
            for row in range(height - box_h + 1)
            for col in range(width - box_w + 1)
        ]
        rng.shuffle(options)
        for row, col in options:
            visited += 1
            if visited > budget:
                return False
            if clashes(index, row, col):
                continue
            spots[index] = (row, col)
            if search(position + 1):
                return True
            spots[index] = None
        return False

    return spots if search(0) else None


def _dims(rng, n_blobs: int, difficulty, *, core: bool) -> list[tuple[int, int]]:
    """One decisive >=3x3 witness followed by canonical-like thin bboxes."""
    if core:
        witness_h = witness_w = 3
    else:
        maximum = {"easy": 3, "medium": 4, "hard": 5}.get(difficulty, 4)
        witness_h = rng.randint(3, maximum)
        witness_w = rng.randint(3, maximum)
    dims = [(witness_h, witness_w)]
    for _ in range(n_blobs - 1):
        length = rng.randint(2, 4)
        dims.append((2, length) if rng.random() < 0.5 else (length, 2))
    return dims


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    repeat_color = sample_index % 3 != 0
    mode = ctx.draw_choice("curriculum_profile", _CORE_MODES)
    anchor = (
        ctx.draw_choice("canonical_anchor", _CANONICAL_PROFILES)
        if mode == "core"
        else (None, None, None)
    )
    height = _draw_axis(ctx, "grid_h", 6, 14, difficulty, anchor[0])
    width = _draw_axis(ctx, "grid_w", 9, 16, difficulty, anchor[1])
    anchored_count = (
        anchor[2] - 1 + int(repeat_color)
        if anchor[2] is not None
        else None
    )
    n_blobs = _draw_axis(ctx, "n_blobs", 2, 5, difficulty, anchored_count)

    dims = _dims(ctx.draw_rng("object_dims"), n_blobs, difficulty, core=mode == "core")
    spots = _place(ctx.draw_rng("placement"), height, width, dims)
    if spots is None:
        # Every declared axis combination is feasible with these minimal boxes;
        # fallback changes only unadvertised shape texture, never an exact axis.
        dims = [(3, 3)] + [(2, 2)] * (n_blobs - 1)
        spots = _place(ctx.draw_rng("placement_minimal"), height, width, dims, budget=500_000)
    if spots is None:
        raise RuntimeError(f"cannot place {n_blobs} separated objects on {height}x{width}")

    color_rng = ctx.draw_rng("colors")
    if not repeat_color:
        colors = color_rng.sample(range(1, 10), n_blobs)
    else:
        distinct = color_rng.sample(range(1, 10), n_blobs - 1)
        colors = [distinct[0], distinct[0], *distinct[1:]]
        color_rng.shuffle(colors)
    shape_rng = ctx.draw_rng("shapes")
    grid = full_grid(height, width, 0)
    for index, ((box_h, box_w), spot, color) in enumerate(zip(dims, spots, colors)):
        assert spot is not None
        row0, col0 = spot
        cells = _shape(shape_rng, box_h, box_w, crosses_interior=index == 0)
        for row, col in cells:
            grid[row0 + row][col0 + col] = color
    return grid


def _objects(grid) -> list[dict[str, object]]:
    """Same-colour 4-connected components, matching the Racket `objects` intent."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[dict[str, object]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for next_row, next_col in (
                    (current_row + 1, current_col),
                    (current_row - 1, current_col),
                    (current_row, current_col + 1),
                    (current_row, current_col - 1),
                ):
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))
            rows = [position[0] for position in cells]
            cols = [position[1] for position in cells]
            found.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return found


def _bbox_hw(obj) -> tuple[int, int]:
    row1, col1, row2, col2 = obj["bbox"]
    return row2 - row1 + 1, col2 - col1 + 1


def _crosses_interior(obj) -> bool:
    row1, col1, row2, col2 = obj["bbox"]
    return any(
        row1 < row < row2 and col1 < col < col2
        for row, col in obj["cells"]
    )


def observe_overrides(grid) -> dict[str, int]:
    """Recover every advertised exact axis from returned pixels."""
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_blobs": len(_objects(grid))}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the lawful task manifold; canonical pairs are intentionally accepted."""
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    if any(
        not isinstance(row, (list, tuple)) or len(row) != len(grid[0])
        for row in grid
    ):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colours 0..9"]

    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    if not 6 <= height <= 14:
        errors.append(f"grid height {height} outside 6..14")
    if not 9 <= width <= 16:
        errors.append(f"grid width {width} outside 9..16")

    components = _objects(grid)
    if not 2 <= len(components) <= 5:
        errors.append(f"expected 2..5 objects, found {len(components)}")
        return errors

    color_counts: dict[int, int] = {}
    for component in components:
        color = component["color"]
        color_counts[color] = color_counts.get(color, 0) + 1
    repeated = [color for color, count in color_counts.items() if count > 1]
    if len(repeated) > 1 or any(color_counts[color] > 2 for color in repeated):
        errors.append("expected at most one colour shared by exactly two components")

    for obj in components:
        box_h, box_w = _bbox_hw(obj)
        if box_h < 2 or box_w < 2:
            errors.append(f"colour {obj['color']} object lacks a genuinely 2D bbox")
        if len(obj["cells"]) >= box_h * box_w:
            errors.append(f"colour {obj['color']} object is a solid rectangle")

    for index, first in enumerate(components):
        row1, col1, row2, col2 = first["bbox"]
        for second in components[index + 1 :]:
            other_row1, other_col1, other_row2, other_col2 = second["bbox"]
            if (
                row1 <= other_row2 + _GAP
                and other_row1 <= row2 + _GAP
                and col1 <= other_col2 + _GAP
                and other_col1 <= col2 + _GAP
            ):
                errors.append(
                    f"bboxes of colours {first['color']} and {second['color']} overlap or touch"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Lawful inputs in this generator's declared task manifold."""
    return self_check(grid)


def _paint_bboxes(grid, *, fill: bool, keep_input: bool):
    output = [list(row) for row in grid] if keep_input else full_grid(len(grid), len(grid[0]), 0)
    for obj in _objects(grid):
        row1, col1, row2, col2 = obj["bbox"]
        for row in range(row1, row2 + 1):
            for col in range(col1, col2 + 1):
                if fill or row in (row1, row2) or col in (col1, col2):
                    output[row][col] = obj["color"]
    return output


def rule_mirror(grid):
    """Pure Python review mirror; the selected Racket program remains authority."""
    return _paint_bboxes(grid, fill=False, keep_input=False)


def _fill_bbox(grid):
    """Rival: paint each entire bbox rather than only its perimeter."""
    return _paint_bboxes(grid, fill=True, keep_input=False)


def _outline_over_input(grid):
    """Rival: add bbox perimeters but fail to erase source interior cells."""
    return _paint_bboxes(grid, fill=False, keep_input=True)


def _global_color_bbox(grid):
    """Canonical-fitting rival: merge disconnected regions of each colour."""
    output = full_grid(len(grid), len(grid[0]), 0)
    colors = sorted({value for row in grid for value in row if value})
    for color in colors:
        cells = [
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == color
        ]
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        row1, col1, row2, col2 = min(rows), min(cols), max(rows), max(cols)
        for row in range(row1, row2 + 1):
            for col in range(col1, col2 + 1):
                if row in (row1, row2) or col in (col1, col2):
                    output[row][col] = color
    return output


def _has_interior_erasure(grid) -> bool:
    return any(min(_bbox_hw(obj)) >= 3 and _crosses_interior(obj) for obj in _objects(grid))


def _has_repeated_component_color(grid) -> bool:
    components = _objects(grid)
    return len({component["color"] for component in components}) < len(components)


def lesson_identifiable(demos, query) -> list[str]:
    """Report a declared rival that fits every demo but changes the query."""
    reasons: list[str] = []
    if query is None:
        return reasons
    for name, rival in SEMANTIC_RIVALS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"rival {name} fits every demo but changes the query")
    return reasons


SEMANTIC_WITNESSES = {
    "interior_erasure": _has_interior_erasure,
    "repeated_component_color": _has_repeated_component_color,
}
SEMANTIC_RIVALS = {
    "fill_bbox": _fill_bbox,
    "outline_over_input": _outline_over_input,
    "global_color_bbox": _global_color_bbox,
}
WITNESS_RIVALS = {
    "interior_erasure": ["fill_bbox", "outline_over_input"],
    "repeated_component_color": ["global_color_bbox"],
}
# The canonical demonstrations never reuse a colour on disconnected components,
# so this rival fits all of them and needs generated counterexamples.
CANONICAL_SHORTCUTS = {"global_color_bbox": _global_color_bbox}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
