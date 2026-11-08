"""Generate lessons for palette-by-component-size task 28119d6d0e10.

The first row is an ordered color legend.  Below a blank separator row are
isolated monochrome components with distinct cell counts.  The Racket oracle
sorts those components by size and recolors them with the legend colors in
left-to-right order.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "28119d6d0e10"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d1af322b3da3"

SUMMARY = (
    "Read the contiguous nonzero legend in row 0. Find the same number of "
    "isolated monochrome body components, sort them by cell count ascending, "
    "and recolor rank i with legend[i] while preserving the legend row."
)

INVARIANTS = [
    "background is literal color 0",
    "row 0 begins with a contiguous legend of 2..4 distinct nonzero colors",
    "row 1 is a completely blank separator",
    "the body contains exactly one isolated monochrome component per legend color",
    "body component colors are distinct and disjoint from legend colors",
    "body component cell counts are strictly distinct",
    "different body components do not touch, even diagonally",
    "default consecutive sample triplets reverse size rank versus reading order",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
_LAYOUT_STYLES = ("free", "mirror_lr", "mirror_ud", "rotate_180")
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-biased 8..16",
        "valid": "8..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-biased 9..18",
        "valid": "9..18",
    },
    "n_shapes": {
        "type": "int",
        "default": "difficulty-biased 2..4",
        "valid": "2..4",
    },
    "palette_kind": {
        "type": "str",
        "default": "keyed choice among four ordered color schemes",
        "valid": "|".join(PALETTE_KINDS),
    },
}

_PALETTE_ORDERS = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (2, 4, 6, 7, 9, 1, 3, 5, 8),
    "cool": (1, 3, 5, 8, 9, 2, 4, 6, 7),
    "varied": (8, 2, 5, 4, 1, 7, 3, 9, 6),
}
_NEIGHBORS_4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_NEIGHBORS_8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be ARC integers 0..9"]
    return []


def _legend(grid) -> list[int]:
    legend: list[int] = []
    for value in grid[0]:
        if value == 0:
            break
        legend.append(value)
    return legend


def _components(grid) -> list[dict]:
    """Return 4-connected nonzero components in rows 2 onward."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict] = []
    for row in range(2, height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            colors: set[int] = set()
            while queue:
                current = queue.popleft()
                cells.append(current)
                colors.add(grid[current[0]][current[1]])
                for dr, dc in _NEIGHBORS_4:
                    neighbor = (current[0] + dr, current[1] + dc)
                    nr, nc = neighbor
                    if not (2 <= nr < height and 0 <= nc < width):
                        continue
                    if grid[nr][nc] == 0 or neighbor in seen:
                        continue
                    seen.add(neighbor)
                    queue.append(neighbor)
            components.append(
                {
                    "cells": tuple(sorted(cells)),
                    "colors": frozenset(colors),
                    "size": len(cells),
                    "first": min(cells),
                }
            )
    return components


def _analysis(grid) -> dict:
    errors = _grid_errors(grid)
    result = {"errors": errors}
    if errors:
        return result

    height, width = len(grid), len(grid[0])
    legend = _legend(grid)
    legend_set = set(legend)
    components = _components(grid) if height >= 3 else []
    sizes = [component["size"] for component in components]
    body_colors = [
        next(iter(component["colors"]))
        for component in components
        if len(component["colors"]) == 1
    ]

    if not 2 <= len(legend) <= 4:
        errors.append(f"legend length must be 2..4, found {len(legend)}")
    if len(legend_set) != len(legend):
        errors.append("legend colors must be distinct")
    if any(value != 0 for value in grid[0][len(legend) :]):
        errors.append("legend must be a contiguous nonzero prefix of row 0")
    if height < 3:
        errors.append("grid needs a legend, separator, and body")
    elif any(value != 0 for value in grid[1]):
        errors.append("row 1 must be a blank separator")
    if len(components) != len(legend):
        errors.append(
            f"body component count {len(components)} must equal legend length {len(legend)}"
        )
    if any(len(component["colors"]) != 1 for component in components):
        errors.append("every body component must be monochrome")
    if len(body_colors) != len(set(body_colors)):
        errors.append("body component colors must be distinct")
    if legend_set.intersection(body_colors):
        errors.append("body colors must be disjoint from legend colors")
    if len(sizes) != len(set(sizes)):
        errors.append("body component sizes must be strictly distinct")

    owner = {
        cell: index
        for index, component in enumerate(components)
        for cell in component["cells"]
    }
    diagonal_contacts = set()
    for cell, index in owner.items():
        row, col = cell
        for dr, dc in _NEIGHBORS_8:
            neighbor = (row + dr, col + dc)
            other = owner.get(neighbor)
            if other is not None and other != index:
                diagonal_contacts.add(tuple(sorted((index, other))))
    if diagonal_contacts:
        errors.append("different body components may not touch diagonally")

    result.update(
        {
            "errors": errors,
            "height": height,
            "width": width,
            "legend": legend,
            "components": components,
            "sizes": sizes,
            "body_colors": body_colors,
            "n_shapes": len(components),
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-friendly teaching scenes."""
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    requested = ((meta or {}).get("overrides") or {})
    if not errors and requested:
        observed = observe_overrides(grid)
        for key in ("grid_h", "grid_w", "n_shapes", "palette_kind"):
            if key in requested and requested[key] != observed[key]:
                errors.append(
                    f"{key} drifted from requested {requested[key]!r} "
                    f"to {observed[key]!r}"
                )
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    palette_matches = [
        kind
        for kind, order in _PALETTE_ORDERS.items()
        if analysis["legend"] == list(order[: analysis["n_shapes"]])
    ]
    if len(palette_matches) != 1:
        raise ValueError("legend does not identify exactly one palette_kind")
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_shapes": analysis["n_shapes"],
        "palette_kind": palette_matches[0],
    }


def rule_mirror(grid):
    """Test-only Python mirror; Racket remains the production output authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = [list(row) for row in grid]
    ranked = sorted(analysis["components"], key=lambda component: component["size"])
    for color, component in zip(analysis["legend"], ranked):
        for row, col in component["cells"]:
            output[row][col] = color
    return output


def _ordered_palette(kind: str, count: int, rng) -> tuple[list[int], list[int]]:
    order = list(_PALETTE_ORDERS[kind])
    legend = order[:count]
    body = order[count : 2 * count]
    rng.shuffle(body)
    return legend, body


def _available_cells(height: int, width: int, blocked: set[tuple[int, int]]):
    return [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in blocked
    ]


def _grow_component(rng, height: int, width: int, blocked, target_size: int):
    for _ in range(96):
        available = _available_cells(height, width, blocked)
        if not available:
            return None
        start = rng.choice(available)
        cells = {start}
        while len(cells) < target_size:
            frontier = []
            for row, col in cells:
                for dr, dc in _NEIGHBORS_4:
                    candidate = (row + dr, col + dc)
                    cr, cc = candidate
                    if not (0 <= cr < height and 0 <= cc < width):
                        continue
                    if candidate in cells or candidate in blocked:
                        continue
                    frontier.append(candidate)
            if not frontier:
                break
            cells.add(rng.choice(frontier))
        if len(cells) == target_size:
            return cells
    return None


def _halo(cells: Iterable[tuple[int, int]], height: int, width: int):
    blocked = set(cells)
    for row, col in cells:
        for dr, dc in _NEIGHBORS_8:
            neighbor = (row + dr, col + dc)
            if 0 <= neighbor[0] < height and 0 <= neighbor[1] < width:
                blocked.add(neighbor)
    return blocked


def _pack_components(rng, height: int, width: int, sizes: list[int]):
    """Pack largest-first, returning cells in the original size order."""
    indexed_sizes = sorted(enumerate(sizes), key=lambda item: item[1], reverse=True)
    for _ in range(192):
        blocked: set[tuple[int, int]] = set()
        result: dict[int, set[tuple[int, int]]] = {}
        for index, size in indexed_sizes:
            cells = _grow_component(rng, height, width, blocked, size)
            if cells is None:
                break
            result[index] = cells
            blocked.update(_halo(cells, height, width))
        if len(result) == len(sizes):
            return [result[index] for index in range(len(sizes))]
    raise AssertionError(
        f"could not pack {len(sizes)} isolated components in {height}x{width} body"
    )


def _transform_cell(cell, height: int, width: int, style: str):
    row, col = cell
    if style == "mirror_lr":
        return row, width - 1 - col
    if style == "mirror_ud":
        return height - 1 - row, col
    if style == "rotate_180":
        return height - 1 - row, width - 1 - col
    return row, col



def _reading_rank_pattern(components):
    reading = sorted(components, key=lambda cells: min(cells))
    ranked = {frozenset(cells): rank for rank, cells in enumerate(
        sorted(components, key=len)
    )}
    return tuple(ranked[frozenset(cells)] for cells in reading)


def _matches_lesson_phase(components, sample_index: int) -> bool:
    pattern = _reading_rank_pattern(components)
    ascending = tuple(range(len(pattern)))
    descending = tuple(reversed(ascending))
    phase = sample_index % 3
    if len(pattern) == 2:
        return pattern == (descending if phase == 1 else ascending)
    if phase == 0:
        return pattern == ascending
    if phase == 1:
        return pattern == descending
    return pattern not in (ascending, descending)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_diff("grid_h", 8, 16)
    width = ctx.draw_int_diff("grid_w", 9, 18)
    count = ctx.draw_int_diff("n_shapes", 2, 4)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    layout_style = ctx.draw_rng("layout").choice(_LAYOUT_STYLES)

    palette_rng = ctx.draw_rng("palette")
    legend, body_colors = _ordered_palette(palette_kind, count, palette_rng)
    sizes = ctx.draw_rng("sizes").sample(range(1, 8), count)
    body_height = height - 2
    geometry_rng = ctx.draw_rng("geometry")
    components = None
    for _ in range(256):
        candidate = _pack_components(geometry_rng, body_height, width, sizes)
        transformed = [
            {
                _transform_cell(cell, body_height, width, layout_style)
                for cell in cells
            }
            for cells in candidate
        ]
        if overrides or _matches_lesson_phase(transformed, sample_index):
            components = transformed
            break
    if components is None:
        raise AssertionError("could not satisfy the sequential lesson schedule")

    grid = full_grid(height, width, 0)
    for col, color in enumerate(legend):
        grid[0][col] = color
    for cells, color in zip(components, body_colors):
        for row, col in cells:
            grid[row + 2][col] = color

    errors = self_check(grid)
    if errors:
        raise AssertionError("internal generator invariant failure: " + "; ".join(errors))
    return grid
