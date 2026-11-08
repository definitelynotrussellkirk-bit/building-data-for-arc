"""Generator for ``stamp_the_smallest_object_at_every_marker``.

The input contains several colored objects and isolated color-9 marker cells.
The uniquely smallest non-9 object is the template.  The oracle normalizes that
object and stamps it, in its own color, with its top-left cell anchored at every
marker on an otherwise blank output grid.

The teaching distribution deliberately includes one or two larger distractor
objects.  This makes the answer depend on the *smallest-object* relation rather
than on the only colored object, the modal color, a fixed position, or a fixed
shape.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "947a1d9ca8f5"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "6e780392649f"

SUMMARY = (
    "A square 0-background grid contains a uniquely smallest colored template "
    "object, one or two larger differently colored distractor objects, and "
    "isolated color-9 markers. Stamp the normalized smallest-object shape in "
    "its color at every marker on a fresh blank grid."
)

INVARIANTS = [
    "background is 0 and marker color is 9",
    "there are two or three non-marker objects; one larger distractor may reuse the template color",
    "the template is the unique smallest non-marker object",
    "every distractor has at least two more cells than the template",
    "there are two to five isolated markers and every full stamp fits in bounds",
    "marker stamp footprints are pairwise disjoint and contain no source object cells or other markers",
]

# Repeated values intentionally bias ordinary draws toward the linked canonical
# manifold while exact overrides still cover every declared boundary.
_CHOICES_BY_DIFFICULTY = {
    "easy": {
        "grid_size": (10, 10, 11, 11, 12, 12, 13, 14, 15, 16),
        "template_cells": (3, 3, 3, 3, 4, 5),
        "marker_count": (3, 3, 3, 3, 2, 4, 5),
        "distractor_count": (1, 1, 1, 1, 2),
        "color_relation": ("distinct", "distinct", "distinct", "template_reused"),
    },
    "medium": {
        "grid_size": (10, 10, 11, 11, 12, 12, 13, 14, 15, 16),
        "template_cells": (3, 3, 3, 4, 5),
        "marker_count": (3, 3, 3, 2, 4, 5),
        "distractor_count": (1, 1, 1, 2),
        "color_relation": ("distinct", "distinct", "distinct", "template_reused"),
    },
    "hard": {
        # Same canonical-manifold mass as medium, but reversed option order
        # and harder non-canonical tails make the band observationally distinct.
        "grid_size": (16, 15, 14, 13, 12, 12, 12, 12, 11, 10),
        "template_cells": (5, 4, 3, 3, 3),
        "marker_count": (5, 4, 2, 3, 3, 3),
        "distractor_count": (2, 1, 1, 1),
        "color_relation": ("template_reused", "distinct", "distinct", "distinct"),
    },
}

AXES = {
    "grid_size": {
        "type": "int",
        "default": "weighted rng over 10..16",
        "valid": "10..16",
    },
    "template_cells": {
        "type": "int",
        "default": "weighted rng over 3..5",
        "valid": "3..5",
    },
    "marker_count": {
        "type": "int",
        "default": "weighted rng over 2..5",
        "valid": "2..5",
    },
    "distractor_count": {
        "type": "int",
        "default": "weighted rng over 1..2",
        "valid": "1..2",
    },
    "color_relation": {
        "type": "str",
        "default": "weighted rng",
        "valid": "distinct|template_reused",
    },
}

_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_NEIGHBORS_8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)

_TEMPLATE_SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    3: (
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (1, 1)),
        ((0, 1), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 1), (0, 2), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
    ),
    5: (
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
    ),
}

_CANONICAL_DISTRACTOR_SHAPES = (
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    ((0, 2), (1, 2), (2, 0), (2, 1), (2, 2)),
)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _shape_dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    shape = tuple(shape)
    return (
        max(row for row, _ in shape) + 1,
        max(col for _, col in shape) + 1,
    )


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Return same-color 4-connected components excluding 0 and 9."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color in (0, 9) or (start_row, start_col) in seen:
                continue
            queue = deque([(start_row, start_col)])
            seen.add((start_row, start_col))
            cells: list[tuple[int, int]] = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for dr, dc in _CARDINALS:
                    neighbor = row + dr, col + dc
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            normalized = _normalize(cells)
            shape_h, shape_w = _shape_dims(normalized)
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "normalized": normalized,
                    "size": len(cells),
                    "height": shape_h,
                    "width": shape_w,
                }
            )
    return components


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["empty or non-list grid"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid is not rectangular"]}
    height = len(grid)
    if height != width or not 10 <= height <= 16:
        errors.append("grid must be square with size 10..16")
    if any(not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid contains a value outside integer colors 0..9")

    markers = tuple(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 9
    )
    if not 2 <= len(markers) <= 5:
        errors.append("marker count must be 2..5")
    marker_set = set(markers)
    if any(
        (row + dr, col + dc) in marker_set
        for row, col in markers
        for dr, dc in _CARDINALS
    ):
        errors.append("markers must be 4-neighbor isolated")

    components = _components(grid)
    if not 2 <= len(components) <= 3:
        errors.append("expected one template and one or two distractor objects")
    template = None
    distractors: list[dict[str, Any]] = []
    if components:
        minimum = min(obj["size"] for obj in components)
        smallest = [obj for obj in components if obj["size"] == minimum]
        if len(smallest) != 1:
            errors.append("the smallest non-marker object must be unique")
        else:
            template = smallest[0]
            distractors = [obj for obj in components if obj is not template]
            if not 3 <= template["size"] <= 5:
                errors.append("template size must be 3..5 cells")
            if any(obj["size"] < template["size"] + 2 for obj in distractors):
                errors.append("every distractor must exceed template size by at least two cells")
            reused = [obj for obj in distractors if obj["color"] == template["color"]]
            other_colors = [obj["color"] for obj in distractors if obj["color"] != template["color"]]
            if len(reused) > 1 or len(other_colors) != len(set(other_colors)):
                errors.append("at most one distractor may reuse the template color")

    if template is not None:
        shape = template["normalized"]
        shape_h, shape_w = _shape_dims(shape)
        object_cells = {
            cell
            for obj in components
            for cell in obj["cells"]
        }
        stamp_footprints: list[set[tuple[int, int]]] = []
        for marker in markers:
            footprint = {
                (marker[0] + dr, marker[1] + dc)
                for dr, dc in shape
            }
            if any(
                row < 0 or row >= height or col < 0 or col >= width
                for row, col in footprint
            ):
                errors.append("a marker places part of the template out of bounds")
                continue
            if footprint & object_cells:
                errors.append("a marker stamp footprint intersects a source object")
            if (footprint - {marker}) & marker_set:
                errors.append("a marker stamp footprint contains another marker")
            if any(footprint & prior for prior in stamp_footprints):
                errors.append("marker stamp footprints must be pairwise disjoint")
            stamp_footprints.append(footprint)
        for row, col in markers:
            if any(
                (row + dr, col + dc) in object_cells
                for dr, dc in _NEIGHBORS_8
            ):
                errors.append("markers must be separated from source objects")
                break
    else:
        shape_h = shape_w = 0
        stamp_footprints = []

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "components": components,
        "markers": markers,
        "template": template,
        "distractors": distractors,
        "color_relation": (
            "template_reused"
            if template is not None
            and any(obj["color"] == template["color"] for obj in distractors)
            else "distinct"
        ),
        "stamp_footprints": stamp_footprints,
        "shape_height": shape_h,
        "shape_width": shape_w,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-prone teaching inputs structurally."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact semantic axis from a valid returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["template"] is None:
        return {}
    return {
        "grid_size": analysis["height"],
        "template_cells": analysis["template"]["size"],
        "marker_count": len(analysis["markers"]),
        "distractor_count": len(analysis["distractors"]),
        "color_relation": analysis["color_relation"],
    }


def _halo_is_free(
    grid: list[list[int]],
    cells: set[tuple[int, int]],
) -> bool:
    height, width = len(grid), len(grid[0])
    for row, col in cells:
        if grid[row][col] != 0:
            return False
        for dr, dc in _NEIGHBORS_8:
            neighbor = row + dr, col + dc
            if 0 <= neighbor[0] < height and 0 <= neighbor[1] < width:
                if neighbor not in cells and grid[neighbor[0]][neighbor[1]] != 0:
                    return False
    return True


def _place_shape(
    grid: list[list[int]],
    shape: tuple[tuple[int, int], ...],
    color: int,
    rng,
) -> bool:
    height, width = len(grid), len(grid[0])
    shape_h, shape_w = _shape_dims(shape)
    positions = [
        (top, left)
        for top in range(height - shape_h + 1)
        for left in range(width - shape_w + 1)
    ]
    rng.shuffle(positions)
    for top, left in positions:
        cells = {(top + dr, left + dc) for dr, dc in shape}
        if not _halo_is_free(grid, cells):
            continue
        for row, col in cells:
            grid[row][col] = color
        return True
    return False


def _random_polyomino(rng, size: int) -> tuple[tuple[int, int], ...]:
    """Build a compact connected polyomino with the requested cell count."""
    for _ in range(200):
        cells = {(0, 0)}
        while len(cells) < size:
            row, col = rng.choice(tuple(cells))
            dr, dc = rng.choice(_CARDINALS)
            cells.add((row + dr, col + dc))
        shape = _normalize(cells)
        shape_h, shape_w = _shape_dims(shape)
        if shape_h <= 4 and shape_w <= 4:
            return shape
    raise ValueError(f"could not construct a compact {size}-cell polyomino")


def _place_markers(
    grid: list[list[int]],
    shape: tuple[tuple[int, int], ...],
    count: int,
    rng,
) -> bool:
    height, width = len(grid), len(grid[0])
    shape_h, shape_w = _shape_dims(shape)
    object_cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 9)
    }
    positions = [
        (row, col)
        for row in range(height - shape_h + 1)
        for col in range(width - shape_w + 1)
    ]
    rng.shuffle(positions)
    markers: list[tuple[int, int]] = []
    footprints: list[set[tuple[int, int]]] = []
    for marker in positions:
        if len(markers) >= count:
            break
        footprint = {
            (marker[0] + dr, marker[1] + dc)
            for dr, dc in shape
        }
        if footprint & object_cells:
            continue
        if any(
            (marker[0] + dr, marker[1] + dc) in object_cells
            for dr, dc in _NEIGHBORS_8
        ):
            continue
        if any(
            abs(marker[0] - other[0]) + abs(marker[1] - other[1]) == 1
            for other in markers
        ):
            continue
        if any(marker in old_footprint for old_footprint in footprints):
            continue
        if any(other in footprint for other in markers):
            continue
        if any(footprint & old_footprint for old_footprint in footprints):
            continue
        grid[marker[0]][marker[1]] = 9
        markers.append(marker)
        footprints.append(footprint)
    return len(markers) == count


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty if difficulty in _CHOICES_BY_DIFFICULTY else "medium"
    choices = _CHOICES_BY_DIFFICULTY[band]
    grid_size = ctx.draw_choice("grid_size", choices["grid_size"])
    template_cells = ctx.draw_choice(
        "template_cells", choices["template_cells"]
    )
    marker_count = ctx.draw_choice("marker_count", choices["marker_count"])
    distractor_count = ctx.draw_choice(
        "distractor_count", choices["distractor_count"]
    )
    color_relation = ctx.draw_choice(
        "color_relation", choices["color_relation"]
    )

    layout_rng = ctx.draw_rng("layout")
    template_rng = ctx.draw_rng("template_shape")
    distractor_rng = ctx.draw_rng("distractor_shapes")
    color_rng = ctx.draw_rng("colors")

    template_shape = template_rng.choice(_TEMPLATE_SHAPES[template_cells])
    colors = list(range(1, 9))
    color_rng.shuffle(colors)
    template_color = colors[0]
    if color_relation == "template_reused":
        distractor_colors = [template_color] + colors[1:distractor_count]
    else:
        distractor_colors = colors[1 : 1 + distractor_count]

    for _ in range(80):
        grid = full_grid(grid_size, grid_size, 0)
        shapes = []
        for index in range(distractor_count):
            if template_cells == 3 and index == 0:
                shapes.append(
                    distractor_rng.choice(_CANONICAL_DISTRACTOR_SHAPES)
                )
            else:
                shapes.append(
                    _random_polyomino(
                        distractor_rng,
                        template_cells + 2 + index,
                    )
                )
        # Randomize source-object reading order; size, not position, identifies
        # the template.  All distractors are placed before the template often
        # enough to defeat a first-object shortcut.
        items = list(zip(shapes, distractor_colors)) + [
            (template_shape, template_color)
        ]
        layout_rng.shuffle(items)
        if not all(
            _place_shape(grid, shape, color, layout_rng)
            for shape, color in items
        ):
            continue
        if not _place_markers(
            grid,
            template_shape,
            marker_count,
            layout_rng,
        ):
            continue
        if not self_check(grid):
            return grid
    raise ValueError("could not realize a valid smallest-template stamp scene")
