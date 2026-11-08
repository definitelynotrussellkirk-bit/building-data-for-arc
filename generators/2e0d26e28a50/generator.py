"""Generator for 2e0d26e28a50: stamp a reference motif at a marker.

The color-2 reference motif is translated so its bounding-box bottom-right
corner lands on the unique color-1 marker.  The translated motif is painted
color 8 on a fresh background grid.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2e0d26e28a50"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"

SUMMARY = (
    "A zero-background grid contains one connected color-2 reference motif "
    "and one isolated color-1 marker. Translate the motif so the bottom-right "
    "corner of its bounding box lands on the marker, paint the translated "
    "cells color 8 on a fresh grid, and discard the source objects."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
INVARIANTS = [
    "7..30 rows and columns with exact ARC colors",
    "exactly one connected color-2 motif of 3..12 cells and at least 2x2 extent",
    "exactly one color-1 marker",
    "bottom-right-anchored translated motif stays inside the grid",
]
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-banded", "valid": "7..30"},
    "grid_w": {"type": "int", "default": "difficulty-banded", "valid": "7..30"},
    "motif_size": {"type": "int", "default": "difficulty-banded", "valid": "3..12"},
}

_ALLOWED_OVERRIDES = frozenset(AXES)
_DIFFICULTIES = {None, "easy", "medium", "hard"}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _exact_int(value: Any, name: str, *, nonnegative: bool = False) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if nonnegative and value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be a rectangular 1..30 ARC grid")
    return [row[:] for row in value]


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    if not cells:
        raise ValueError("cannot take bounding box of no cells")
    rows, cols = zip(*cells)
    return min(rows), min(cols), max(rows), max(cols)


def _connected(cells: Iterable[tuple[int, int]]) -> bool:
    cells = set(cells)
    if not cells:
        return False
    todo = [next(iter(cells))]
    seen = {todo[0]}
    while todo:
        r, c = todo.pop()
        for dr, dc in _CARDINAL:
            other = (r + dr, c + dc)
            if other in cells and other not in seen:
                seen.add(other)
                todo.append(other)
    return len(seen) == len(cells)


def analyze(grid: Any) -> dict[str, Any]:
    """Validate and expose the source objects and bottom-right offsets."""
    source = _grid(grid)
    height, width = len(source), len(source[0])
    forbidden = sorted({cell for row in source for cell in row} - {0, 1, 2})
    if forbidden:
        raise ValueError(f"base grammar permits only colors 0, 1, and 2; got {forbidden}")

    motif = sorted(
        (r, c)
        for r, row in enumerate(source)
        for c, value in enumerate(row)
        if value == 2
    )
    if not 3 <= len(motif) <= 12:
        raise ValueError(f"expected 3..12 color-2 motif cells, got {len(motif)}")
    if not _connected(motif):
        raise ValueError("color-2 reference motif must be connected")
    top, left, bottom, right = _bbox(motif)
    if bottom == top or right == left:
        raise ValueError("color-2 reference motif must span at least two rows and columns")

    markers = [
        (r, c)
        for r, row in enumerate(source)
        for c, value in enumerate(row)
        if value == 1
    ]
    if len(markers) != 1:
        raise ValueError(f"expected exactly one color-1 marker, got {len(markers)}")
    marker = markers[0]
    offsets = [(r - bottom, c - right) for r, c in motif]
    translated = [(marker[0] + dr, marker[1] + dc) for dr, dc in offsets]
    if any(not (0 <= r < height and 0 <= c < width) for r, c in translated):
        raise ValueError("bottom-right-anchored stamp falls outside grid bounds")

    return {
        "height": height,
        "width": width,
        "motif_cells": motif,
        "motif_size": len(motif),
        "motif_bbox": (top, left, bottom, right),
        "motif_shape": (bottom - top + 1, right - left + 1),
        "marker": marker,
        "bottom_right_offsets": offsets,
        "translated_cells": translated,
    }


def rule_mirror(grid: Any) -> list[list[int]]:
    """Apply the exact labeled rule without mutating ``grid``."""
    info = analyze(grid)
    output = full_grid(info["height"], info["width"], 0)
    for r, c in info["translated_cells"]:
        output[r][c] = 8
    return output


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    del meta
    if difficulty not in _DIFFICULTIES:
        return ["difficulty must be easy, medium, hard, or None"]
    try:
        analyze(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def _motif(rng, size: int) -> list[tuple[int, int]]:
    """Build a compact connected motif with a genuine two-dimensional extent."""
    side = max(2, min(5, int((size - 1) ** 0.5) + 2))
    cells = {(0, 0), (1, 0), (1, 1)}
    while len(cells) < size:
        frontier = sorted({
            (r + dr, c + dc)
            for r, c in cells
            for dr, dc in _CARDINAL
            if 0 <= r + dr < side and 0 <= c + dc < side
            and (r + dr, c + dc) not in cells
        })
        if not frontier:
            side += 1
            continue
        cells.add(rng.choice(frontier))
    top, left, _, _ = _bbox(cells)
    return sorted((r - top, c - left) for r, c in cells)


def _draw_axis(ctx, name: str, valid: tuple[int, int], default: tuple[int, int]) -> int:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, *valid)
    return ctx.draw_int_strict(name, *default)


def _difficulty_bands(difficulty: str | None) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (7, 12), (7, 13), (3, 5)
    if difficulty == "hard":
        return (18, 30), (18, 30), (7, 12)
    return (10, 20), (10, 22), (4, 8)


def _far_enough(marker: tuple[int, int], motif: set[tuple[int, int]]) -> bool:
    mr, mc = marker
    return all(max(abs(mr - r), abs(mc - c)) > 1 for r, c in motif)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate deterministic valid instances with strict, observable controls."""
    _exact_int(seed, "seed")
    _exact_int(sample_index, "sample_index", nonnegative=True)
    if difficulty not in _DIFFICULTIES:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = set(overrides) - _ALLOWED_OVERRIDES
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    hb, wb, kb = _difficulty_bands(difficulty)
    height = _draw_axis(ctx, "grid_h", (7, 30), hb)
    width = _draw_axis(ctx, "grid_w", (7, 30), wb)
    size = _draw_axis(ctx, "motif_size", (3, 12), kb)
    rng = ctx.draw_rng("layout")
    motif_local = _motif(ctx.draw_rng("motif"), size)
    _, _, motif_bottom, motif_right = _bbox(motif_local)
    motif_height, motif_width = motif_bottom + 1, motif_right + 1
    if motif_height > height or motif_width > width:
        raise ValueError("motif_size is incompatible with requested grid dimensions")

    reference_positions = [
        (r, c)
        for r in range(height - motif_height + 1)
        for c in range(width - motif_width + 1)
    ]
    marker_positions = [
        (r, c)
        for r in range(motif_height - 1, height)
        for c in range(motif_width - 1, width)
    ]
    rng.shuffle(reference_positions)
    rng.shuffle(marker_positions)
    for top, left in reference_positions:
        motif = {(top + r, left + c) for r, c in motif_local}
        choices = [p for p in marker_positions if p not in motif and _far_enough(p, motif)]
        if not choices:
            continue
        marker = rng.choice(choices)
        grid = full_grid(height, width, 0)
        for r, c in motif:
            grid[r][c] = 2
        grid[marker[0]][marker[1]] = 1
        if self_check(grid, difficulty=difficulty) == []:
            return grid
    raise ValueError("could not realize a separated reference and valid marker")


def observe_overrides(grid: Any) -> dict[str, int]:
    info = analyze(grid)
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "motif_size": info["motif_size"],
    }
