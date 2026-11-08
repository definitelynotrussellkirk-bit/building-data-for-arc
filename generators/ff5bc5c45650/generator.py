"""Generator for fe9bb13a9b18:S14_M5 — profile intersection.

The selected object is the unique largest monochrome component.  Its row and
column occupancy profiles are converted to left- and top-justified histograms;
the cyan output is their cellwise intersection.  Ordinary draws deliberately
mix exact one-object canonical anchors with multi-object counterexamples so a
lesson cannot collapse to cropping the shape, using only one profile, or
blindly choosing the first component.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ff5bc5c45650"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "62c6ec846105"

SUMMARY = (
    "A 0-background grid contains one to five separated monochrome components. "
    "Choose the unique largest object by cell count.  Build its left-justified "
    "row histogram and top-justified column histogram, intersect them, and "
    "paint the resulting object cyan(8).  One quarter of ordinary draws are "
    "exact canonical-scale one-object anchors; the rest add lawful distractors."
)

INVARIANTS = [
    "the input is 8..24 by 10..24 with background 0",
    "there are 1..5 separated 4-connected monochrome components",
    "exactly one object is largest by cell count and has 6..16 cells",
    "every distractor is strictly smaller than the selected object",
    "the selected object's row/column-profile intersection is nontrivial",
    "ordinary draws include exact canonical anchors and multi-object shortcut rebuttals",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled/difficulty-aware", "valid": "8..24"},
    "grid_w": {"type": "int", "default": "scheduled/difficulty-aware", "valid": "10..24"},
    "n_shapes": {"type": "int", "default": "scheduled/difficulty-aware", "valid": "1..5"},
    "max_size": {"type": "int", "default": "scheduled/difficulty-aware", "valid": "6..16"},
    "palette_size": {"type": "int", "default": "1..n_shapes", "valid": "1..5"},
    "position_bias": {"type": "str", "default": "scheduled", "valid": "left|center|right"},
    "vertical_bias": {"type": "str", "default": "scheduled", "valid": "top|middle|bottom"},
}

# The boundary matrix probes only extrema.  This is the one incompatible
# extrema pair; arbitrary palette_size > n_shapes requests are rejected with a
# structured ValueError carrying both axis names.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n_shapes": 1, "palette_size": 5},
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20
SCHEDULE_PROFILES = (0, 1, 2, 3)

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_COLORS = (1, 2, 3, 4, 5, 6, 7, 8, 9)

# Exact normalized masks from the three canonical inputs.  Translation and
# object color are nuisance variables; orientation is answer-bearing because
# it changes the row/column profiles.
_CANONICAL_MASKS = (
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
    ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3), (2, 0), (2, 3)),
)
_CANONICAL_PROFILES = (
    (8, 10, _CANONICAL_MASKS[0]),
    (8, 10, _CANONICAL_MASKS[1]),
    (9, 12, _CANONICAL_MASKS[2]),
)

# One nontrivial connected base mask per supported selected-object size.  Their
# profile intersection differs from the crop, row-only histogram, column-only
# histogram, and solid bounding box.  D4 variants supply lawful morphology and
# orientation breadth without changing size.
_BASE_MASK_FAMILIES = {
    6: (
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 1)),
    ),
    7: (
        ((0, 2), (0, 3), (1, 2), (2, 0), (2, 1), (2, 2), (3, 0)),
        ((0, 2), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (3, 1)),
        ((0, 2), (0, 3), (1, 2), (2, 0), (2, 1), (2, 2), (3, 1)),
    ),
    8: (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (2, 0), (3, 0)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (2, 1), (3, 0), (3, 1)),
        ((0, 1), (1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (3, 0), (3, 1)),
    ),
    9: (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (1, 3), (2, 0), (3, 0)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (2, 1), (3, 0), (3, 1)),
    ),
    10: (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2), (3, 0)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 1), (3, 0), (3, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2), (3, 0)),
    ),
    11: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1), (2, 3), (3, 0), (3, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2), (3, 1), (3, 2)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2), (3, 0), (3, 1)),
    ),
    12: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 3), (3, 1), (3, 2)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2), (3, 0), (3, 1), (3, 2)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3), (3, 0)),
    ),
    13: (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (3, 0), (3, 1), (3, 2)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 2), (3, 0), (3, 1), (3, 2)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 3), (3, 0), (3, 1)),
    ),
    14: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2), (3, 3)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2), (3, 3)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2), (2, 3), (3, 0), (3, 2), (3, 3)),
    ),
    15: (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 3), (3, 0), (3, 1), (3, 2), (3, 3)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2), (3, 3)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3), (3, 0), (3, 1), (3, 3)),
    ),
    16: (
        ((0, 0), (0, 1), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (3, 0), (3, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (3, 0), (3, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 0), (2, 1), (2, 2), (2, 4), (3, 1), (3, 2), (3, 3)),
    ),
}



def schedule_profile(seed, sample_index, difficulty=None):
    """Four consecutive samples cover anchors, target-first, and target-late."""
    del seed, difficulty
    return int(sample_index) % 4


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _rotate(mask: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    return _normalize((col, -row) for row, col in mask)


def _reflect(mask: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    return _normalize((row, -col) for row, col in mask)


def _d4(mask: tuple[tuple[int, int], ...]) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants: set[tuple[tuple[int, int], ...]] = set()
    current = _normalize(mask)
    for _ in range(4):
        variants.add(current)
        variants.add(_reflect(current))
        current = _rotate(current)
    return tuple(sorted(variants))


def _teaching_shape(mask: tuple[tuple[int, int], ...]) -> bool:
    """Keep only morphologies that force both occupancy profiles to matter."""
    height = max(row for row, _ in mask) + 1
    width = max(col for _, col in mask) + 1
    rows = tuple(sum(row == current for row, _ in mask) for current in range(height))
    cols = tuple(sum(col == current for _, col in mask) for current in range(width))
    intersection = tuple(
        tuple(8 if col < rows[row] and row < cols[col] else 0 for col in range(width))
        for row in range(height)
    )
    row_only = tuple(
        tuple(8 if col < rows[row] else 0 for col in range(width))
        for row in range(height)
    )
    col_only = tuple(
        tuple(8 if row < cols[col] else 0 for col in range(width))
        for row in range(height)
    )
    crop = tuple(
        tuple(8 if (row, col) in mask else 0 for col in range(width))
        for row in range(height)
    )
    values = {value for row in intersection for value in row}
    return values == {0, 8} and intersection not in {row_only, col_only, crop}


_SHAPES_BY_SIZE = {
    size: tuple(
        sorted(
            variant
            for mask in masks
            for variant in _d4(mask)
            if _teaching_shape(variant)
        )
    )
    for size, masks in _BASE_MASK_FAMILIES.items()
}
assert all(_SHAPES_BY_SIZE.values()), "every selected-object size needs a teaching morphology"


def _incompatible(*axes: str, detail: str) -> None:
    exc = ValueError(detail)
    exc.incompatible_axes = tuple(axes)
    raise exc


def _draw_int(ctx, label: str, default_lo: int, default_hi: int, global_lo: int, global_hi: int) -> int:
    if label in ctx.overrides:
        return ctx.draw_int(label, global_lo, global_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _draw_choice(ctx, label: str, options: tuple[Any, ...], scheduled: Any | None = None):
    if label in ctx.overrides or scheduled is None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _component_cells(grid: list[list[int]]) -> list[dict[str, Any]]:
    height = len(grid)
    width = len(grid[0]) if grid else 0
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                cell = queue.popleft()
                cells.append(cell)
                for drow, dcol in _CARD:
                    neighbor = (cell[0] + drow, cell[1] + dcol)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            components.append({"color": color, "cells": tuple(sorted(cells))})
    return sorted(
        components,
        key=lambda obj: (
            min(row for row, _ in obj["cells"]),
            min(col for _, col in obj["cells"]),
        ),
    )


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _profiles(cells: Iterable[tuple[int, int]]) -> tuple[list[int], list[int]]:
    cells = tuple(cells)
    row1, col1, row2, col2 = _bbox(cells)
    rows = [sum(row == current for row, _ in cells) for current in range(row1, row2 + 1)]
    cols = [sum(col == current for _, col in cells) for current in range(col1, col2 + 1)]
    return rows, cols


def _intersection_for_cells(cells: Iterable[tuple[int, int]], color: int = 8) -> list[list[int]]:
    rows, cols = _profiles(cells)
    return [
        [color if col < rows[row] and row < cols[col] else 0 for col in range(len(cols))]
        for row in range(len(rows))
    ]


def _largest(components: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not components:
        return None
    return max(components, key=lambda obj: len(obj["cells"]))


def _anchor(value: str, total: int, span: int) -> int:
    if value in {"left", "top"}:
        return 0
    if value in {"right", "bottom"}:
        return total - span
    return (total - span) // 2


def _place_target(
    grid: list[list[int]],
    mask: tuple[tuple[int, int], ...],
    color: int,
    horizontal: str,
    vertical: str,
) -> set[tuple[int, int]]:
    height = len(grid)
    width = len(grid[0])
    shape_h = max(row for row, _ in mask) + 1
    shape_w = max(col for _, col in mask) + 1
    top = _anchor(vertical, height, shape_h)
    left = _anchor(horizontal, width, shape_w)
    placed = {(top + row, left + col) for row, col in mask}
    for row, col in placed:
        grid[row][col] = color
    return placed


def _candidate_distractors(
    height: int,
    width: int,
    occupied: set[tuple[int, int]],
    *,
    prefer_before_target: bool,
    rng,
) -> list[tuple[int, int]]:
    def clear(cell: tuple[int, int]) -> bool:
        row, col = cell
        if cell in occupied:
            return False
        return all((row + drow, col + dcol) not in occupied for drow, dcol in _CARD)

    candidates = [(row, col) for row in range(height) for col in range(width) if clear((row, col))]
    rng.shuffle(candidates)
    candidates.sort(
        key=(
            (lambda cell: (cell[0], cell[1]))
            if prefer_before_target
            else (lambda cell: (-cell[0], -cell[1]))
        )
    )
    return candidates


def _place_distractors(
    grid: list[list[int]],
    occupied: set[tuple[int, int]],
    count: int,
    colors: tuple[int, ...],
    *,
    prefer_before_target: bool,
    rng,
) -> None:
    candidates = _candidate_distractors(
        len(grid), len(grid[0]), occupied,
        prefer_before_target=prefer_before_target,
        rng=rng,
    )
    placed = 0
    for cell in candidates:
        if placed >= count:
            break
        row, col = cell
        if cell in occupied:
            continue
        if any((row + drow, col + dcol) in occupied for drow, dcol in _CARD):
            continue
        grid[row][col] = colors[placed]
        occupied.add(cell)
        placed += 1
    if placed != count:
        raise ValueError(f"could place only {placed}/{count} separated distractors")


def _palette(ctx, palette_size: int) -> tuple[int, ...]:
    rng = ctx.draw_rng("palette")
    colors = list(_COLORS)
    rng.shuffle(colors)
    return tuple(colors[:palette_size])


def _canonical_anchor(ctx, seed: int, sample_index: int) -> list[list[int]]:
    index = (int(seed) + int(sample_index) // 4) % len(_CANONICAL_PROFILES)
    canonical_h, canonical_w, mask = _CANONICAL_PROFILES[index]
    grid_h = ctx.draw_int("grid_h", canonical_h, canonical_h)
    grid_w = ctx.draw_int("grid_w", canonical_w, canonical_w)
    n_shapes = ctx.draw_int("n_shapes", 1, 1)
    max_size = ctx.draw_int("max_size", len(mask), len(mask))
    palette_size = ctx.draw_int("palette_size", 1, 1)
    horizontal = ctx.draw_choice("position_bias", ("center",))
    vertical = ctx.draw_choice("vertical_bias", ("middle",))
    assert n_shapes == palette_size == 1 and max_size == len(mask)
    grid = full_grid(grid_h, grid_w, 0)
    color = _palette(ctx, palette_size)[0]
    _place_target(grid, mask, color, horizontal, vertical)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)

    # Overrides always exercise the general constructor.  Without overrides,
    # profile 0 is an exact canonical anchor in every difficulty band.
    if not overrides and profile == 0:
        return _canonical_anchor(ctx, seed, sample_index)

    if difficulty == "easy":
        h_bounds, w_bounds = (8, 12), (10, 14)
        n_bounds, size_bounds = (1, 2), (6, 8)
        palette_cap = 2
    elif difficulty == "hard":
        h_bounds, w_bounds = (16, 24), (16, 24)
        n_bounds, size_bounds = (3, 5), (11, 16)
        palette_cap = 5
    else:
        h_bounds, w_bounds = (10, 18), (12, 20)
        n_bounds, size_bounds = (2, 4), (8, 12)
        palette_cap = 4

    requested_palette = overrides.get("palette_size")
    if requested_palette is not None and "n_shapes" not in overrides:
        requested_palette = int(requested_palette)
        n_bounds = (max(n_bounds[0], requested_palette), max(n_bounds[1], requested_palette))

    grid_h = _draw_int(ctx, "grid_h", *h_bounds, 8, 24)
    grid_w = _draw_int(ctx, "grid_w", *w_bounds, 10, 24)
    if not overrides and profile in {2, 3}:
        # Every four-example lesson contains profiles 0,1,2,3.  Profiles 2/3
        # must therefore be genuine target-late counterexamples rather than
        # occasionally collapsing to a one-object scene in the easy band.
        scheduled_count = max(2, n_bounds[0])
        n_shapes = ctx.draw_int("n_shapes", scheduled_count, scheduled_count)
    else:
        n_shapes = _draw_int(ctx, "n_shapes", *n_bounds, 1, 5)
    max_size = _draw_int(ctx, "max_size", *size_bounds, 6, 16)

    if "palette_size" in overrides:
        palette_size = ctx.draw_int("palette_size", 1, 5)
    else:
        palette_size = ctx.draw_int("palette_size", 1, min(palette_cap, n_shapes))
    if palette_size > n_shapes:
        _incompatible(
            "n_shapes", "palette_size",
            detail=(
                f"n_shapes={n_shapes} cannot realize palette_size={palette_size}; "
                "palette_size must be <= n_shapes"
            ),
        )

    horizontal_schedule = ("left", "center", "right", "left")[profile]
    vertical_schedule = ("middle", "top", "bottom", "bottom")[profile]
    horizontal = _draw_choice(
        ctx, "position_bias", ("left", "center", "right"), horizontal_schedule
    )
    vertical = _draw_choice(
        ctx, "vertical_bias", ("top", "middle", "bottom"), vertical_schedule
    )

    shape_rng = ctx.draw_rng("target_shape")
    mask = shape_rng.choice(_SHAPES_BY_SIZE[max_size])
    palette = _palette(ctx, palette_size)
    component_colors = tuple(
        palette[index] if index < palette_size else palette[index % palette_size]
        for index in range(n_shapes)
    )

    grid = full_grid(grid_h, grid_w, 0)
    occupied = _place_target(grid, mask, component_colors[0], horizontal, vertical)
    _place_distractors(
        grid,
        occupied,
        n_shapes - 1,
        component_colors[1:],
        prefer_before_target=profile in {2, 3},
        rng=ctx.draw_rng("distractor_positions"),
    )

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid generator instance: {errors}")
    return [row[:] for row in grid]


def _bias_from_bbox(start: int, total: int, span: int, names: tuple[str, str, str]) -> str:
    positions = (0, (total - span) // 2, total - span)
    return names[min(range(3), key=lambda index: (abs(start - positions[index]), index))]


def observe_overrides(grid) -> dict[str, Any]:
    components = _component_cells(grid)
    target = _largest(components)
    if target is None:
        return {
            "grid_h": len(grid),
            "grid_w": len(grid[0]) if grid else 0,
            "n_shapes": 0,
            "max_size": 0,
            "palette_size": 0,
            "position_bias": None,
            "vertical_bias": None,
        }
    row1, col1, row2, col2 = _bbox(target["cells"])
    height = len(grid)
    width = len(grid[0])
    return {
        "grid_h": height,
        "grid_w": width,
        "n_shapes": len(components),
        "max_size": len(target["cells"]),
        "palette_size": len({obj["color"] for obj in components}),
        "position_bias": _bias_from_bbox(col1, width, col2 - col1 + 1, ("left", "center", "right")),
        "vertical_bias": _bias_from_bbox(row1, height, row2 - row1 + 1, ("top", "middle", "bottom")),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]
    height = len(grid)
    if not (8 <= height <= 24 and 10 <= width <= 24):
        errors.append(f"grid dimensions must be within 8..24 by 10..24, found {height}x{width}")
    if any(not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid values must be ARC colors 0..9")
        return errors

    components = _component_cells(grid)
    if not (1 <= len(components) <= 5):
        errors.append(f"expected 1..5 non-background components, found {len(components)}")
    if not components:
        return errors

    sizes = [len(obj["cells"]) for obj in components]
    largest_size = max(sizes)
    if sizes.count(largest_size) != 1:
        errors.append("largest object must be unique by cell count")
    if not (6 <= largest_size <= 16):
        errors.append(f"largest object must have 6..16 cells, found {largest_size}")
    if any(size >= largest_size for size in sizes if size != largest_size):
        errors.append("every distractor must be strictly smaller than the target")

    cell_owner: dict[tuple[int, int], int] = {}
    for index, obj in enumerate(components):
        for cell in obj["cells"]:
            cell_owner[cell] = index
    for cell, owner in cell_owner.items():
        for drow, dcol in _CARD:
            neighbor = (cell[0] + drow, cell[1] + dcol)
            if neighbor in cell_owner and cell_owner[neighbor] != owner:
                errors.append("different components must have at least one-cell cardinal clearance")
                break
        if errors and errors[-1].startswith("different components"):
            break

    target = _largest(components)
    assert target is not None
    row1, col1, row2, col2 = _bbox(target["cells"])
    if row2 - row1 + 1 < 3 or col2 - col1 + 1 < 3:
        errors.append("target bounding box must be at least 3x3")
    intersection = _intersection_for_cells(target["cells"])
    values = {value for row in intersection for value in row}
    if values != {0, 8}:
        errors.append("profile intersection must contain both cyan and background")

    requested = ((meta or {}).get("overrides") or {}) if isinstance(meta, dict) else {}
    if requested and not errors:
        observed = observe_overrides(grid)
        for axis, value in requested.items():
            if axis in observed and observed[axis] != value:
                errors.append(f"override {axis} requested {value!r}, observed {observed[axis]!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    components = _component_cells(grid)
    if len(components) != 1:
        reasons.append(f"canonical inputs contain one object, found {len(components)}")
        return reasons
    dimensions = (len(grid), len(grid[0]))
    if dimensions not in {(8, 10), (9, 12)}:
        reasons.append(f"canonical dimensions are 8x10 or 9x12, found {dimensions[0]}x{dimensions[1]}")
    mask = _normalize(components[0]["cells"])
    if mask not in _CANONICAL_MASKS:
        reasons.append("selected-object morphology is not one of the three canonical masks")
    return reasons


def _target_and_output(grid):
    components = _component_cells(grid)
    target = _largest(components)
    if target is None:
        return None, []
    return target, _intersection_for_cells(target["cells"])


def _rival_crop_largest(grid):
    target, _ = _target_and_output(grid)
    if target is None:
        return []
    mask = set(_normalize(target["cells"]))
    height = max(row for row, _ in mask) + 1
    width = max(col for _, col in mask) + 1
    return [[8 if (row, col) in mask else 0 for col in range(width)] for row in range(height)]


def _rival_row_histogram(grid):
    target, _ = _target_and_output(grid)
    if target is None:
        return []
    rows, cols = _profiles(target["cells"])
    return [[8 if col < rows[row] else 0 for col in range(len(cols))] for row in range(len(rows))]


def _rival_col_histogram(grid):
    target, _ = _target_and_output(grid)
    if target is None:
        return []
    rows, cols = _profiles(target["cells"])
    return [[8 if row < cols[col] else 0 for col in range(len(cols))] for row in range(len(rows))]


def _rival_solid_bbox(grid):
    target, _ = _target_and_output(grid)
    if target is None:
        return []
    rows, cols = _profiles(target["cells"])
    return [[8 for _ in cols] for _ in rows]


def _rival_first_component(grid):
    components = _component_cells(grid)
    return _intersection_for_cells(components[0]["cells"]) if components else []


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "crop_largest": _rival_crop_largest,
    "row_histogram_only": _rival_row_histogram,
    "column_histogram_only": _rival_col_histogram,
    "solid_largest_bbox": _rival_solid_bbox,
    "first_component_intersection": _rival_first_component,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _valid(grid) -> bool:
    return not self_check(grid)


def _first_component_is_not_target(grid) -> bool:
    if not _valid(grid):
        return False
    components = _component_cells(grid)
    target = _largest(components)
    return len(components) > 1 and target is not None and components[0]["cells"] != target["cells"]


def _rival_differs(grid, rival: Callable[[list[list[int]]], list[list[int]]]) -> bool:
    if not _valid(grid):
        return False
    _, output = _target_and_output(grid)
    return rival(grid) != output


SEMANTIC_WITNESSES = {
    "exact_canonical_anchor": lambda grid: not strict_canonical_like(grid),
    "single_object": lambda grid: _valid(grid) and len(_component_cells(grid)) == 1,
    "multiple_objects": lambda grid: _valid(grid) and len(_component_cells(grid)) >= 2,
    "intersection_not_crop": lambda grid: _rival_differs(grid, _rival_crop_largest),
    "both_profiles_decisive": lambda grid: (
        _rival_differs(grid, _rival_row_histogram)
        and _rival_differs(grid, _rival_col_histogram)
    ),
    "non_solid_output": lambda grid: _rival_differs(grid, _rival_solid_bbox),
    "distractor_precedes_target": _first_component_is_not_target,
}

WITNESS_RIVALS = {
    "exact_canonical_anchor": ["crop_largest", "row_histogram_only", "column_histogram_only"],
    "single_object": ["crop_largest"],
    "multiple_objects": ["solid_largest_bbox"],
    "intersection_not_crop": ["crop_largest"],
    "both_profiles_decisive": ["row_histogram_only", "column_histogram_only"],
    "non_solid_output": ["solid_largest_bbox"],
    "distractor_precedes_target": ["first_component_intersection"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    for name, competitor in LESSON_COMPETITORS.items():
        fits_demos = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if not fits_demos:
            continue
        if competitor(query["input"]) == query["output"]:
            reasons.append(f"{name} survives every demo and the query")
        else:
            reasons.append(f"{name} fits every demo but changes the query answer")
    return reasons


def mutation_fixtures():
    blank = full_grid(8, 10, 0)

    tied = full_grid(8, 10, 0)
    for row, col in ((1, 1), (1, 2), (2, 1), (2, 2), (3, 1), (3, 2)):
        tied[row][col] = 2
        tied[row + 3][col + 5] = 3

    tiny = full_grid(8, 10, 0)
    for row, col in ((1, 1), (1, 2), (2, 1), (2, 2), (3, 1)):
        tiny[row][col] = 4

    touching = full_grid(8, 10, 0)
    for row, col in _CANONICAL_MASKS[1]:
        touching[1 + row][1 + col] = 5
    touching[3][4] = 6

    solid = full_grid(8, 10, 0)
    for row in range(3):
        for col in range(3):
            solid[2 + row][3 + col] = 7

    narrow = full_grid(8, 10, 0)
    for col in range(6):
        narrow[3][2 + col] = 9

    return [
        ("blank_grid", blank),
        ("two_equal_largest_objects", tied),
        ("largest_object_too_small", tiny),
        ("different_color_object_touches_target", touching),
        ("solid_bbox_hides_intersection", solid),
        ("one_row_target_has_no_two_profile_structure", narrow),
    ]
