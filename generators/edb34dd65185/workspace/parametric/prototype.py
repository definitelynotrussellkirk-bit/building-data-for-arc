#!/usr/bin/env python3
"""Native parametric family for edb34dd65185.

The input grammar is shared by both settings.  Every grid contains three
separated, distinct-colour objects with respectively 0, 1, and 2 interior
holes.  The latent setting controls whether their bbox crops are packed from
fewest-to-most holes (the catalog authority) or most-to-fewest holes.
"""
from __future__ import annotations

import hashlib
import random
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "edb34dd65185"
ORDERS = ("ascending", "descending")
DEFAULT_SETTINGS = {"order": "ascending"}
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)

_HOME = Path(__file__).resolve().parent
_CANONICAL_PATH = _HOME / "canonical.rkt"
_DESCENDING_PATH = _HOME / "descending.rkt"

# Fixed count-prefix profiles.  The fourth query is deliberately the lawful
# 30x30 stress case required by the assignment.
_DEMO_PROFILES: tuple[tuple[int, int], ...] = (
    (14, 18),
    (16, 16),
    (17, 20),
    (18, 17),
    (20, 22),
    (22, 20),
)
_QUERY_PROFILES: tuple[tuple[int, int], ...] = (
    (13, 17),
    (19, 23),
    (24, 25),
    (30, 30),
)

# Demonstrations deliberately make scan, area, and colour orders all follow the
# non-monotone hole sequence 1,0,2.  Neither that sequence nor its reverse is
# the taught 0,1,2 / 2,1,0 order, so two demonstrations reject those common
# shortcuts for both settings instead of relying on chance.
_TEACHING_DIMS: tuple[tuple[tuple[int, int], tuple[int, int], tuple[int, int]], ...] = (
    ((3, 4), (3, 3), (5, 4)),
    ((3, 4), (3, 4), (5, 5)),
    ((3, 5), (4, 4), (5, 5)),
    ((4, 4), (4, 4), (6, 5)),
    ((4, 5), (5, 5), (6, 6)),
    ((4, 6), (5, 6), (7, 6)),
)


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _settings(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"order"}:
        raise ValueError("settings must name exactly order")
    order = value["order"]
    if order not in ORDERS:
        raise ValueError("order must be ascending or descending")
    return {"order": order}


def _rng(seed: int, domain: str, index: int, attempt: int = 0) -> random.Random:
    payload = f"{TASK_ID}|v1|{seed}|{domain}|{index}|{attempt}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def program(settings: dict[str, Any]) -> str:
    selected = _settings(settings)
    path = _CANONICAL_PATH if selected["order"] == "ascending" else _DESCENDING_PATH
    return path.read_text(encoding="utf-8")


def _solid(rows: int, cols: int) -> frozenset[tuple[int, int]]:
    return frozenset((r, c) for r in range(rows) for c in range(cols))


def _ring(rows: int, cols: int) -> frozenset[tuple[int, int]]:
    return frozenset(
        (r, c)
        for r in range(rows)
        for c in range(cols)
        if r in (0, rows - 1) or c in (0, cols - 1)
    )


def _double_ring(rows: int, cols: int) -> frozenset[tuple[int, int]]:
    middle = rows // 2
    return frozenset(
        (r, c)
        for r in range(rows)
        for c in range(cols)
        if r in (0, rows - 1, middle) or c in (0, cols - 1)
    )


def _hole_count(cells: Iterable[tuple[int, int]]) -> int:
    occupied = set(cells)
    rows = max(r for r, _ in occupied) + 1
    cols = max(c for _, c in occupied) + 1
    seen: set[tuple[int, int]] = set()
    holes = 0
    for sr in range(rows):
        for sc in range(cols):
            if (sr, sc) in occupied or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            touches_border = False
            while stack:
                r, c = stack.pop()
                if r in (0, rows - 1) or c in (0, cols - 1):
                    touches_border = True
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and (nr, nc) not in occupied
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            holes += not touches_border
    return holes


def _shape_pool(hole_count: int, large: bool) -> tuple[frozenset[tuple[int, int]], ...]:
    if hole_count == 0:
        dims = ((2, 3), (3, 3), (3, 4), (4, 5)) if large else ((2, 2), (2, 3), (3, 3), (3, 4))
        shapes = tuple(_solid(r, c) for r, c in dims)
    elif hole_count == 1:
        dims = ((4, 5), (5, 6), (6, 7)) if large else ((3, 3), (3, 4), (4, 4), (4, 5), (5, 5))
        shapes = tuple(_ring(r, c) for r, c in dims)
    elif hole_count == 2:
        dims = ((6, 5), (7, 6), (8, 7)) if large else ((5, 3), (5, 4), (6, 4), (7, 5))
        shapes = tuple(_double_ring(r, c) for r, c in dims)
    else:
        raise ValueError("unsupported hole count")
    if any(_hole_count(shape) != hole_count for shape in shapes):
        raise RuntimeError("shape pool violates its declared hole count")
    return shapes


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    values = tuple(cells)
    return (
        min(r for r, _ in values),
        min(c for _, c in values),
        max(r for r, _ in values),
        max(c for _, c in values),
    )


def _bbox_with_gap_overlaps(
    a: tuple[int, int, int, int], b: tuple[int, int, int, int]
) -> bool:
    # Padding a by one cell makes touching or one-axis-adjacent boxes illegal.
    padded = (a[0] - 1, a[1] - 1, a[2] + 1, a[3] + 1)
    return not (
        padded[2] < b[0]
        or b[2] < padded[0]
        or padded[3] < b[1]
        or b[3] < padded[1]
    )


def _place_shapes(
    rows: int,
    cols: int,
    shapes: tuple[frozenset[tuple[int, int]], ...],
    rng: random.Random,
) -> list[tuple[int, int]] | None:
    dimensions = [
        (max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1)
        for shape in shapes
    ]
    positions: list[tuple[int, int]] = [(0, 0)] * len(shapes)
    boxes: list[tuple[int, int, int, int]] = []

    # Place the most spatially restrictive shapes first, but preserve their
    # original indices in the returned placements.
    order = sorted(range(len(shapes)), key=lambda i: dimensions[i][0] * dimensions[i][1], reverse=True)

    def search(depth: int) -> bool:
        if depth == len(order):
            return True
        shape_index = order[depth]
        height, width = dimensions[shape_index]
        candidates = [
            (top, left)
            for top in range(rows - height + 1)
            for left in range(cols - width + 1)
        ]
        rng.shuffle(candidates)
        for top, left in candidates:
            box = (top, left, top + height - 1, left + width - 1)
            if any(_bbox_with_gap_overlaps(existing, box) for existing in boxes):
                continue
            positions[shape_index] = (top, left)
            boxes.append(box)
            if search(depth + 1):
                return True
            boxes.pop()
        return False

    return positions if search(0) else None


def _sample_demo_input(seed: int, index: int) -> list[list[int]]:
    rows, cols = _DEMO_PROFILES[index]
    rng = _rng(seed, "demo", index)
    solid_dims, ring_dims, double_dims = _TEACHING_DIMS[index]
    shapes = (
        _solid(*solid_dims),
        _ring(*ring_dims),
        _double_ring(*double_dims),
    )
    assert [_hole_count(shape) for shape in shapes] == [0, 1, 2]
    areas = [len(shape) for shape in shapes]
    assert areas[1] < areas[0] < areas[2]

    heights = [max(r for r, _ in shape) + 1 for shape in shapes]
    widths = [max(c for _, c in shape) + 1 for shape in shapes]
    sequence = (1, 0, 2)
    minimum_height = sum(heights[shape_index] for shape_index in sequence) + 2
    if minimum_height > rows:
        raise RuntimeError("teaching profile exceeds its canvas")
    extra = rows - minimum_height
    slack = [0, 0, 0, 0]
    for _ in range(extra):
        slack[rng.randrange(4)] += 1
    top = slack[0]
    placements: dict[int, tuple[int, int]] = {}
    for position, shape_index in enumerate(sequence):
        left = rng.randrange(cols - widths[shape_index] + 1)
        placements[shape_index] = (top, left)
        top += heights[shape_index]
        if position < len(sequence) - 1:
            top += 1 + slack[position + 1]

    sorted_colors = sorted(rng.sample(range(1, 10), 3))
    colors = {1: sorted_colors[0], 0: sorted_colors[1], 2: sorted_colors[2]}
    grid = [[0 for _ in range(cols)] for _ in range(rows)]
    for shape_index, shape in enumerate(shapes):
        top, left = placements[shape_index]
        for r, c in shape:
            grid[top + r][left + c] = colors[shape_index]
    return grid


def _sample_input(seed: int, domain: str, index: int) -> list[list[int]]:
    if domain == "demo":
        return _sample_demo_input(seed, index)
    if domain == "query":
        rows, cols = _QUERY_PROFILES[index]
    else:
        raise ValueError("domain must be demo or query")

    large = rows >= 24
    for attempt in range(256):
        rng = _rng(seed, domain, index, attempt)
        pools = tuple(_shape_pool(hole_count, large) for hole_count in range(3))
        shapes = tuple(rng.choice(pool) for pool in pools)
        heights = [max(r for r, _ in shape) + 1 for shape in shapes]
        if sum(heights) + 2 > rows:
            continue
        placements = _place_shapes(rows, cols, shapes, rng)
        if placements is None:
            continue
        colors = rng.sample(range(1, 10), 3)
        # Placement coordinates are indexed by the same shape they bound.
        # Random candidate order already varies spatial order, while random
        # colours break any stable palette-to-hole-count shortcut.
        grid = [[0 for _ in range(cols)] for _ in range(rows)]
        for shape_index, (top, left) in enumerate(placements):
            color = colors[shape_index]
            for r, c in shapes[shape_index]:
                grid[top + r][left + c] = color
        return grid
    raise RuntimeError(f"could not construct lawful {domain}[{index}] input")


def _strict_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not grid or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not grid[0] or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact integers 0..9")
    return grid


def _components(grid: list[list[int]]) -> list[tuple[int, list[tuple[int, int]]]]:
    rows, cols = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, list[tuple[int, int]]]] = []
    for sr in range(rows):
        for sc in range(cols):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def _crop(grid: list[list[int]], cells: list[tuple[int, int]]) -> list[list[int]]:
    top, left, bottom, right = _bbox(cells)
    return [row[left : right + 1] for row in grid[top : bottom + 1]]


def _crop_holes(crop: list[list[int]]) -> int:
    rows, cols = len(crop), len(crop[0])
    zeroes = {(r, c) for r in range(rows) for c in range(cols) if crop[r][c] == 0}
    seen: set[tuple[int, int]] = set()
    holes = 0
    for first in sorted(zeroes):
        if first in seen:
            continue
        stack = [first]
        seen.add(first)
        touches_border = False
        while stack:
            r, c = stack.pop()
            if r in (0, rows - 1) or c in (0, cols - 1):
                touches_border = True
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (r + dr, c + dc)
                if neighbor in zeroes and neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        holes += not touches_border
    return holes


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    source = _strict_grid(grid)
    order = _settings(settings)["order"]
    entries: list[tuple[int, int, int, list[list[int]]]] = []
    for _color, cells in _components(source):
        crop = _crop(source, cells)
        nonzero_count = sum(value != 0 for row in crop for value in row)
        minimum_color = min(value for row in crop for value in row if value != 0)
        entries.append((_crop_holes(crop), nonzero_count, minimum_color, crop))
    if not entries:
        raise ValueError("grid must contain at least one non-background object")
    if order == "ascending":
        entries.sort(key=lambda entry: (entry[0], entry[1], entry[2]))
    else:
        # Only the primary hole-count comparator is reversed by the Racket
        # variant.  Canonical tie-breakers remain ascending.
        entries.sort(key=lambda entry: (-entry[0], entry[1], entry[2]))

    output = [[0 for _ in row] for row in source]
    top = 0
    for _holes, _area, _color, crop in entries:
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                if value != 0 and top + r < len(output) and c < len(output[0]):
                    output[top + r][c] = value
        top += len(crop) + 1
    return output


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int,
    queries: int,
) -> dict[str, Any]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    selected = _settings(settings)
    _exact_int(demos, "demos", *DEMO_LIMITS)
    _exact_int(queries, "queries", *QUERY_LIMITS)

    train = []
    for index in range(demos):
        grid = _sample_input(seed, "demo", index)
        train.append({"input": grid, "output": transform(grid, selected)})
    test = []
    for index in range(queries):
        grid = _sample_input(seed, "query", index)
        test.append({"input": grid, "output": transform(grid, selected)})
    return {"train": train, "test": test, "program_solution": program(selected)}
