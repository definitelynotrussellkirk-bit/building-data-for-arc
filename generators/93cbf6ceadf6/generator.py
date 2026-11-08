"""Generator for canonical ARC task 93cbf6ceadf6.

Rule: find the three separated monochrome objects, normalize every object's
cells by bounding-box translation, identify the one shape that occurs once
while another shape occurs twice, and output the uniquely shaped object cropped
to its bounding box in its original color.

Ordinary scenes deliberately make all three objects equal in area and bounding-
box size.  Colors may all match, partially match, or all differ, and object roles
are shuffled across positions.  Those controls force shape comparison rather
than color, area, bounding box, or reading-order shortcuts.
"""
from __future__ import annotations

from collections import Counter, deque
import hashlib
import random
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "93cbf6ceadf6"
TASK_ID = "93cbf6ceadf6"
VERSION = "2.0.0"

SUMMARY = (
    "Place exactly three separated objects: two translation-identical shapes "
    "and one different shape with matched area and bounding box. The rule "
    "returns the uniquely shaped object cropped in its original color."
)
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0 and all objects are separated by an 8-neighbor moat",
    "there are exactly three 4-connected monochrome objects",
    "translation-normalized shape multiplicities are exactly 2 and 1",
    "ordinary repeated and odd shapes share area and bounding-box size",
    "colors and spatial roles vary independently of shape uniqueness",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware draw",
        "valid": "9..22",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware draw",
        "valid": "9..22",
    },
}

# Every family contains (repeated_shape, odd_shape).  Both members are
# 4-connected, have equal area and equal bounding boxes, and the odd member is
# asymmetric under identity / rotate-cw / flip-left-right.  Common dihedral
# orientation is applied to both members so the controls remain matched.
_SHAPE_FAMILIES: tuple[
    tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]], ...
] = (
    (
        ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1)),
    ),
    (
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
        ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    ),
    (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0)),
    ),
    (
        ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (3, 0)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1), (3, 1)),
    ),
    (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (2, 1), (3, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 2), (1, 3), (2, 2), (3, 2)),
    ),
    (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (2, 1), (3, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (2, 2), (3, 2)),
    ),
)


def _validate_override_names(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(
            "unknown override axis/axes: " + ", ".join(repr(name) for name in unknown)
        )


def _normalize(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(shape)
    if not cells:
        raise ValueError("shape must contain at least one cell")
    r0 = min(row for row, _ in cells)
    c0 = min(col for _, col in cells)
    return tuple(sorted((row - r0, col - c0) for row, col in cells))


def _shape_size(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    normalized = _normalize(shape)
    return (
        1 + max(row for row, _ in normalized),
        1 + max(col for _, col in normalized),
    )


def rotate_cw(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _normalize(shape)
    height, _ = _shape_size(normalized)
    return _normalize((col, height - 1 - row) for row, col in normalized)


def flip_lr(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _normalize(shape)
    _, width = _shape_size(normalized)
    return _normalize((row, width - 1 - col) for row, col in normalized)


def _transform(
    shape: Iterable[tuple[int, int]], transform_index: int
) -> tuple[tuple[int, int], ...]:
    if type(transform_index) is not int or not 0 <= transform_index < 8:
        raise ValueError("transform_index must be an exact integer in 0..7")
    result = _normalize(shape)
    if transform_index >= 4:
        result = flip_lr(result)
    for _ in range(transform_index % 4):
        result = rotate_cw(result)
    return result


def scale_shape(
    shape: Iterable[tuple[int, int]], scale: int
) -> tuple[tuple[int, int], ...]:
    if type(scale) is not int or not 1 <= scale <= 3:
        raise ValueError("scale must be an exact integer in 1..3")
    result = []
    for row, col in _normalize(shape):
        for dr in range(scale):
            for dc in range(scale):
                result.append((scale * row + dr, scale * col + dc))
    return _normalize(result)


def _same_shape_controls(
    repeated: tuple[tuple[int, int], ...],
    odd: tuple[tuple[int, int], ...],
) -> bool:
    return (
        repeated != odd
        and len(repeated) == len(odd)
        and _shape_size(repeated) == _shape_size(odd)
        and len({odd, rotate_cw(odd), flip_lr(odd)}) == 3
    )


def _role_colors(rng: random.Random) -> tuple[int, int, int]:
    colors = list(range(1, 10))
    rng.shuffle(colors)
    first, second, third = colors[:3]
    mode = rng.randrange(4)
    if mode == 0:
        return first, first, first
    if mode == 1:
        return first, first, second
    if mode == 2:
        return first, second, third
    # The odd object shares a color with one repeated object, defeating a
    # unique-color shortcut while the repeated pair itself has different colors.
    return first, second, first


def _shape_cells(
    row: int, col: int, shape: Iterable[tuple[int, int]]
) -> set[tuple[int, int]]:
    return {(row + dr, col + dc) for dr, dc in shape}


def _add_moat(
    forbidden: set[tuple[int, int]],
    cells: Iterable[tuple[int, int]],
    height: int,
    width: int,
) -> None:
    for row, col in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = row + dr, col + dc
                if 0 <= rr < height and 0 <= cc < width:
                    forbidden.add((rr, cc))


def _place_objects(
    height: int,
    width: int,
    objects: list[tuple[int, tuple[tuple[int, int], ...], str]],
    rng: random.Random,
    *,
    span_edges: bool,
) -> list[list[int]] | None:
    grid = full_grid(height, width, 0)
    forbidden: set[tuple[int, int]] = set()
    for index, (color, shape, _) in enumerate(objects):
        shape_h, shape_w = _shape_size(shape)
        if shape_h > height or shape_w > width:
            return None
        if span_edges:
            anchors = (
                (0, 0),
                (0, width - shape_w),
                (height - shape_h, width - shape_w),
            )
            positions = [anchors[index]]
        else:
            positions = [
                (row, col)
                for row in range(height - shape_h + 1)
                for col in range(width - shape_w + 1)
            ]
            rng.shuffle(positions)
        placed = False
        for row, col in positions:
            cells = _shape_cells(row, col, shape)
            if cells & forbidden:
                continue
            for rr, cc in cells:
                grid[rr][cc] = color
            _add_moat(forbidden, cells, height, width)
            placed = True
            break
        if not placed:
            return None
    return grid


def _construct_scene(
    rng: random.Random,
    height: int,
    width: int,
    *,
    scale: int = 1,
    span_edges: bool = False,
) -> list[list[int]] | None:
    family_indices = list(range(len(_SHAPE_FAMILIES)))
    rng.shuffle(family_indices)
    for family_index in family_indices:
        base_repeated, base_odd = _SHAPE_FAMILIES[family_index]
        transforms = list(range(8))
        rng.shuffle(transforms)
        for transform_index in transforms:
            repeated = scale_shape(_transform(base_repeated, transform_index), scale)
            odd = scale_shape(_transform(base_odd, transform_index), scale)
            if not _same_shape_controls(repeated, odd):
                continue
            colors = _role_colors(rng)
            objects = [
                (colors[0], repeated, "repeated"),
                (colors[1], repeated, "repeated"),
                (colors[2], odd, "odd"),
            ]
            rng.shuffle(objects)
            scene = _place_objects(
                height,
                width,
                objects,
                rng,
                span_edges=span_edges,
            )
            if scene is not None:
                return scene
    return None


def build_scene(
    seed: int,
    sample_index: int,
    *,
    height: int,
    width: int,
    scale: int = 1,
    span_edges: bool = False,
) -> list[list[int]]:
    """Deterministic scene constructor reused by the parametric prototype."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative exact integer")
    if type(height) is not int or type(width) is not int or not (9 <= height <= 30 and 9 <= width <= 30):
        raise ValueError("height and width must be exact integers in 9..30")
    digest = hashlib.sha256(
        f"{TASK_ID}:scene:{seed}:{sample_index}:{height}:{width}:{scale}:{int(span_edges)}".encode()
    ).digest()
    rng = random.Random(int.from_bytes(digest[:16], "big"))
    for _ in range(80):
        scene = _construct_scene(
            rng,
            height,
            width,
            scale=scale,
            span_edges=span_edges,
        )
        if scene is not None and not self_check(scene):
            return scene
    raise RuntimeError("could not realize paired-shape/odd-shape scene")


def _draw_dimension(
    ctx,
    name: str,
    overrides: dict[str, Any],
    *,
    easy: tuple[int, int],
    medium: tuple[int, int],
    hard: tuple[int, int],
) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int(name, 9, 22)
    if ctx.difficulty == "easy":
        low, high = easy
    elif ctx.difficulty == "hard":
        low, high = hard
    else:
        low, high = medium
    return ctx.draw_int(name, low, high)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_names(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_dimension(
        ctx,
        "grid_h",
        overrides,
        easy=(9, 12),
        medium=(11, 17),
        hard=(16, 22),
    )
    width = _draw_dimension(
        ctx,
        "grid_w",
        overrides,
        easy=(9, 12),
        medium=(11, 17),
        hard=(16, 22),
    )
    rng = ctx.draw_rng("layout")
    for _ in range(100):
        grid = _construct_scene(rng, height, width)
        if grid is not None and not self_check(grid):
            return grid
    raise RuntimeError("could not realize paired-shape/odd-shape layout")


def _component_items(grid: list[list[int]]) -> list[dict[str, Any]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    items: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            cells: set[tuple[int, int]] = set()
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                rr, cc = queue.popleft()
                cells.add((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            r0 = min(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells)
            r1 = max(rr for rr, _ in cells)
            c1 = max(cc for _, cc in cells)
            shape = tuple(sorted((rr - r0, cc - c0) for rr, cc in cells))
            items.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "shape": shape,
                    "r0": r0,
                    "c0": c0,
                    "r1": r1,
                    "c1": c1,
                    "height": r1 - r0 + 1,
                    "width": c1 - c0 + 1,
                }
            )
    return items


def _objects_have_moat(items: list[dict[str, Any]]) -> bool:
    for index, left in enumerate(items):
        for right in items[index + 1 :]:
            if any(
                max(abs(r1 - r2), abs(c1 - c2)) <= 1
                for r1, c1 in left["cells"]
                for r2, c2 in right["cells"]
            ):
                return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not (1 <= len(grid) <= 30 and 1 <= width <= 30):
        return [f"grid dimensions must lie in 1..30, got {len(grid)}x{width}"]
    invalid = [
        value
        for row in grid
        for value in row
        if type(value) is not int or not 0 <= value <= 9
    ]
    if invalid:
        return ["grid contains non-ARC cell values"]
    if not any(value == 0 for row in grid for value in row):
        return ["background color 0 must be present"]

    items = _component_items(grid)
    errors: list[str] = []
    if len(items) != 3:
        errors.append(f"expected exactly three objects, found {len(items)}")
        return errors
    frequencies = Counter(item["shape"] for item in items)
    if sorted(frequencies.values()) != [1, 2]:
        errors.append(
            "translation-normalized shape multiplicities must be exactly [1,2], "
            f"got {sorted(frequencies.values())}"
        )
    if not _objects_have_moat(items):
        errors.append("objects must be separated by a one-cell 8-neighbor moat")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list:
        raise ValueError("grid must be nonempty and rectangular")
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def _odd_item(grid: list[list[int]]) -> dict[str, Any]:
    items = _component_items(grid)
    frequencies = Counter(item["shape"] for item in items)
    odd = [item for item in items if frequencies[item["shape"]] == 1]
    if len(items) != 3 or len(odd) != 1 or sorted(frequencies.values()) != [1, 2]:
        raise ValueError("grid does not contain one odd normalized shape among a repeated pair")
    return odd[0]


def _odd_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror of the selected canonical Racket rule."""
    odd = _odd_item(grid)
    output = full_grid(odd["height"], odd["width"], 0)
    for row, col in odd["shape"]:
        output[row][col] = odd["color"]
    return output
