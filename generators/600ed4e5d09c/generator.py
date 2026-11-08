"""Truthful generator for ARC task 600ed4e5d09c.

The input uses exactly two corner controls: the top-left cell selects a body
object color and the top-right cell is transform key 1..4.  The body contains
one hollow rectangular frame and one selected, non-outline object.  The rule
clears both controls, transforms the selected object's tight crop, and centers
that crop inside the frame.  There is deliberately no bottom-left frame-color
anchor: the canonical rule never reads one, and a colored singleton there is
itself a rectangular-outline object under the canonical predicate.
"""
from __future__ import annotations

import copy
import hashlib
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = TASK_ID = "600ed4e5d09c"
VERSION = "2.2.0"
RULE_HASH = "f96ec5618f89"

SUMMARY = (
    "Top corners hold selected color and transform key; the body contains one "
    "hollow frame and one asymmetric selected object."
)

PALETTES = {
    "default": (2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (2, 4, 6, 7, 9),
    "cool": (1, 3, 5, 8),
    "varied": (1, 2, 3, 4, 5, 6, 7, 8, 9),
}
PALETTE_KINDS = tuple(PALETTES)
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 10..30", "valid": "10..30"},
    "grid_w": {"type": "int", "default": "difficulty-aware 10..30", "valid": "10..30"},
    "palette_kind": {
        "type": "str",
        "default": "rng",
        "valid": "|".join(PALETTE_KINDS),
    },
}

INVARIANTS = [
    "background is 0",
    "(0,0) is a nonzero selected color and (0,w-1) is transform key 1..4",
    "(h-1,0) remains background; there is no frame-color control",
    "after clearing the two controls there is exactly one hollow frame",
    "there is exactly one selected-color non-outline target",
    "every keyed transform of the target crop fits inside the frame interior",
]

_BASE_SHAPE = ((0, 0), (0, 1), (0, 2), (1, 0))  # asymmetric L tetromino; D4 orbit size 8


def _exact_int(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _validate_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    result: list[list[int]] = []
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            raise ValueError("grid cells must be exact ARC colors 0..9")
        result.append(list(row))
    return result


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _rotate_cells_cw(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize((c, -r) for r, c in cells)


def _flip_cells_lr(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize((r, -c) for r, c in cells)


def _shape_orientations(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    current = _normalize(cells)
    result: list[tuple[tuple[int, int], ...]] = []
    for _ in range(4):
        for candidate in (current, _flip_cells_lr(current)):
            if candidate not in result:
                result.append(candidate)
        current = _rotate_cells_cw(current)
    return tuple(result)


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _is_rect_outline_shape(cells: Iterable[tuple[int, int]]) -> bool:
    norm = set(_normalize(cells))
    if not norm:
        return False
    r2 = max(r for r, _ in norm)
    c2 = max(c for _, c in norm)
    outline = {
        (r, c)
        for r in range(r2 + 1)
        for c in range(c2 + 1)
        if r in (0, r2) or c in (0, c2)
    }
    return norm == outline


def _objects(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    objects: list[dict[str, Any]] = []
    for sr in range(height):
        for sc in range(width):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and (rr, cc) not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            ordered = tuple(sorted(cells))
            objects.append({"color": color, "cells": ordered, "bbox": _bbox(ordered)})
    return objects


def _crop(grid: list[list[int]], obj: dict[str, Any]) -> list[list[int]]:
    r0, c0, r1, c1 = obj["bbox"]
    output = [[0 for _ in range(c1 - c0 + 1)] for _ in range(r1 - r0 + 1)]
    for r, c in obj["cells"]:
        output[r - r0][c - c0] = grid[r][c]
    return output


def rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid[::-1]]


def transform_crop(grid: list[list[int]], key: int, *, codebook: str = "canonical") -> list[list[int]]:
    if codebook == "canonical":
        fn = {1: rotate_cw, 2: rotate_180, 3: flip_lr, 4: flip_ud}.get(key, lambda x: copy.deepcopy(x))
    elif codebook == "inverse":
        fn = {1: rotate_ccw, 2: rotate_180, 3: flip_ud, 4: flip_lr}.get(key, lambda x: copy.deepcopy(x))
    elif codebook == "identity":
        fn = lambda x: copy.deepcopy(x)
    elif codebook == "shifted":
        fn = {1: rotate_180, 2: flip_lr, 3: flip_ud, 4: rotate_cw}.get(key, lambda x: copy.deepcopy(x))
    else:
        raise ValueError(f"unknown codebook {codebook!r}")
    return fn(grid)


def _paste_centered(
    base: list[list[int]], crop: list[list[int]], frame_bbox: tuple[int, int, int, int]
) -> list[list[int]]:
    r0, c0, r1, c1 = frame_bbox
    top, bottom, left, right = r0 + 1, r1 - 1, c0 + 1, c1 - 1
    interior_h, interior_w = bottom - top + 1, right - left + 1
    if len(crop) > interior_h or len(crop[0]) > interior_w:
        raise ValueError("transformed crop does not fit frame interior")
    sr = top + (interior_h - len(crop)) // 2
    sc = left + (interior_w - len(crop[0])) // 2
    output = copy.deepcopy(base)
    for r, row in enumerate(crop):
        for c, value in enumerate(row):
            if value:
                output[sr + r][sc + c] = value
    return output


def _semantic_parts(grid: Any) -> tuple[list[list[int]], int, int, list[dict[str, Any]], list[dict[str, Any]]]:
    rows = _validate_grid(grid)
    height, width = len(rows), len(rows[0])
    selected = rows[0][0]
    key = rows[0][width - 1]
    work = copy.deepcopy(rows)
    work[0][0] = 0
    work[0][width - 1] = 0
    objects = _objects(work)
    frames = [obj for obj in objects if _is_rect_outline_shape(obj["cells"])]
    targets = [
        obj
        for obj in objects
        if obj["color"] == selected and not _is_rect_outline_shape(obj["cells"])
    ]
    return work, selected, key, frames, targets


def rule_mirror(grid: Any, *, codebook: str = "canonical") -> list[list[int]]:
    rows = _validate_grid(grid)
    height, width = len(rows), len(rows[0])
    work, _selected, key, frames, targets = _semantic_parts(rows)
    if not frames or not targets:
        return full_grid(height, width, 0)
    frame = frames[-1]
    target = sorted(
        targets,
        key=lambda obj: (
            -len(obj["cells"]),
            obj["bbox"][0],
            obj["bbox"][2],
            obj["bbox"][1],
            obj["bbox"][3],
        ),
    )[0]
    base = full_grid(height, width, 0)
    for r, c in frame["cells"]:
        base[r][c] = frame["color"]
    transformed = transform_crop(_crop(work, target), key, codebook=codebook)
    return _paste_centered(base, transformed, frame["bbox"])


def frame_color(grid: Any) -> int:
    _work, _selected, _key, frames, _targets = _semantic_parts(grid)
    if len(frames) != 1:
        raise ValueError(f"expected exactly one frame, found {len(frames)}")
    return int(frames[0]["color"])


def generate(seed: int, sample_index: int, *, difficulty: str | None = None, **overrides: Any) -> list[list[int]]:
    _exact_int(seed, 0, 2**63 - 1, "seed")
    _exact_int(sample_index, 0, 2**31 - 1, "sample_index")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown overrides: {sorted(unknown)}")
    for name in ("grid_h", "grid_w"):
        if name in overrides and overrides[name] is not None:
            _exact_int(overrides[name], 10, 30, name)
    if "palette_kind" in overrides and overrides["palette_kind"] is not None:
        value = overrides["palette_kind"]
        if type(value) is not str or value not in PALETTES:
            raise ValueError(f"palette_kind must be one of {tuple(PALETTES)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_diff("grid_h", 10, 30)
    width = ctx.draw_int_diff("grid_w", 10, 30)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    palette = PALETTES[palette_kind]
    rng = ctx.draw_rng("layout")
    selected, frame = rng.sample(list(palette), 2)
    key = rng.randint(1, 4)

    grid = full_grid(height, width, 0)
    grid[0][0] = selected
    grid[0][width - 1] = key

    max_fh = min(14, height - 4)
    max_fw = min(16, width - 4)
    fh = rng.randint(5, max_fh)
    fw = rng.randint(5, max_fw)
    fr0 = height - fh - 1
    fc0 = width - fw - 1
    draw_frame(grid, fr0, fc0, fr0 + fh - 1, fc0 + fw - 1, frame)

    orientations = _shape_orientations(_BASE_SHAPE)
    shape = orientations[rng.randrange(len(orientations))]
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    # The reserved band above/left of the frame always has room at minimum size.
    max_tr = max(1, fr0 - sh - 1)
    max_tc = max(1, fc0 - sw - 1)
    tr0 = rng.randint(1, max_tr)
    tc0 = rng.randint(1, max_tc)
    for r, c in shape:
        grid[tr0 + r][tc0 + c] = selected

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructed invalid {TASK_ID} scene: {errors}")
    return grid


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del meta
    errors: list[str] = []
    if difficulty not in (None, "easy", "medium", "hard"):
        errors.append("difficulty must be None, easy, medium, or hard")
    try:
        rows = _validate_grid(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    height, width = len(rows), len(rows[0])
    if not (10 <= height <= 30 and 10 <= width <= 30):
        errors.append("generated grid dimensions must each be in 10..30")
    selected = rows[0][0]
    key = rows[0][width - 1]
    if selected == 0:
        errors.append("top-left selected-color control must be nonzero")
    if type(key) is not int or not 1 <= key <= 4:
        errors.append("top-right transform key must be 1..4")
    if rows[-1][0] != 0:
        errors.append("bottom-left must remain background; no frame-color control exists")
    try:
        work, _selected, _key, frames, targets = _semantic_parts(rows)
    except (TypeError, ValueError) as exc:
        errors.append(str(exc))
        return errors
    if len(frames) != 1:
        errors.append(f"expected exactly one hollow rectangular frame, found {len(frames)}")
    if len(targets) != 1:
        errors.append(f"expected exactly one selected non-outline target, found {len(targets)}")
    if len(frames) == 1 and len(targets) == 1:
        frame = frames[0]
        target_crop = _crop(work, targets[0])
        r0, c0, r1, c1 = frame["bbox"]
        ih, iw = r1 - r0 - 1, c1 - c0 - 1
        for transform_key in range(1, 5):
            transformed = transform_crop(target_crop, transform_key)
            if len(transformed) > ih or len(transformed[0]) > iw:
                errors.append(f"target transform {transform_key} does not fit frame interior")
        if frame["color"] == selected:
            errors.append("frame and selected target colors must differ")
    return errors
