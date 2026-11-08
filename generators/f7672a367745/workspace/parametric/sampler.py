"""Constructive, label-free banks of disjoint colored rectangle corner pairs.

Every sampled color occurs at exactly two diagonal corners.  All inferred
boxes have visible interiors.  The first three examples teach area ranking,
the singleton case, and selection of all tied extrema respectively.
"""

from __future__ import annotations

import hashlib
import json
import random


MAX_SEED = 2**63 - 1
MAX_DUPLICATE_ATTEMPTS = 64
_RNG_DOMAIN = "f7672a367745-native-input-banks-v1"
Box = tuple[int, int, int, int]


def _local_rng(seed: int, split: str, slot: int, retry: int) -> random.Random:
    material = f"{_RNG_DOMAIN}|{seed}|{split}|{slot}|{retry}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _dihedral(grid: list[list[int]], transform: int) -> list[list[int]]:
    if transform >= 4:
        grid = [list(reversed(row)) for row in grid]
    for _ in range(transform % 4):
        grid = [list(row) for row in zip(*reversed(grid))]
    return grid


def _render(
    height: int,
    width: int,
    boxes: list[Box],
    rng: random.Random,
    *,
    interleave_tie_colors: bool = False,
) -> list[list[int]]:
    palette = list(range(1, 10))
    rng.shuffle(palette)
    colors = palette[:len(boxes)]
    if interleave_tie_colors:
        # D2 stores two large, two small, then two middle-area boxes.  Pair
        # numeric ranks 0/3, 1/4 and 2/5, then assign those interleaved pairs
        # to the three groups.  No group is a monotone color threshold.
        if len(boxes) != 6:
            raise ValueError("the interleaved tie palette requires six boxes")
        ordered = sorted(colors)
        groups = [[ordered[index], ordered[index + 3]] for index in range(3)]
        rng.shuffle(groups)
        for group in groups:
            rng.shuffle(group)
        colors = [color for group in groups for color in group]
    grid = [[0] * width for _ in range(height)]
    for color, (top, left, bottom, right) in zip(colors, boxes):
        corners = ((top, left), (bottom, right)) if rng.randrange(2) else ((top, right), (bottom, left))
        for row, column in corners:
            if grid[row][column] != 0:
                raise AssertionError("sampled corner markers must not collide")
            grid[row][column] = color
    return _dihedral(grid, rng.randrange(8))


def _segments(length: int, count: int) -> list[tuple[int, int]]:
    quotient, remainder = divmod(length, count)
    result = []
    start = 0
    for index in range(count):
        size = quotient + (index < remainder)
        result.append((start, start + size - 1))
        start += size
    return result


def _partitioned_boxes(
    height: int,
    width: int,
    row_parts: int,
    col_parts: int,
    shapes: tuple[tuple[int, int], ...],
    rng: random.Random,
    *,
    touch_boundaries: bool = False,
) -> list[Box]:
    regions = [(top, left, bottom, right)
               for top, bottom in _segments(height, row_parts)
               for left, right in _segments(width, col_parts)]
    shapes = list(shapes)
    rng.shuffle(shapes)
    if len(shapes) > len(regions):
        raise ValueError("one disjoint region is required for each rectangle")
    boxes = []
    for (box_height, box_width), (top, left, bottom, right) in zip(shapes, regions):
        if box_height > bottom - top + 1 or box_width > right - left + 1:
            raise ValueError("rectangle does not fit its assigned region")
        row0 = rng.randint(top, bottom - box_height + 1)
        col0 = rng.randint(left, right - box_width + 1)
        if touch_boundaries:
            if top == 0:
                row0 = 0
            if bottom == height - 1:
                row0 = height - box_height
            if left == 0:
                col0 = 0
            if right == width - 1:
                col0 = width - box_width
        boxes.append((row0, col0, row0 + box_height - 1, col0 + box_width - 1))
    return boxes


def _teaching_template(slot: int, rng: random.Random) -> list[list[int]]:
    if slot == 0:
        # Areas 40 < 42 but perimeters 28 > 26.  Together with D1 area 35
        # and D2 areas 24/36, these also rule out a fixed monotone area cutoff.
        return _render(12, 21, [(8, 1, 11, 10), (0, 13, 5, 19)], rng)
    if slot == 1:
        # Both ranking policies must fill even when there is no competitor.
        top, left = rng.randrange(5), rng.randrange(5)
        return _render(9, 11, [(top, left, top + 4, left + 6)], rng)
    if slot == 2:
        # Large: 6x6 and 4x9, area 36.  Small: 3x8 and 4x6, area 24.
        # Middle: 4x7 and 4x8, areas 28 and 32, so taking every box except
        # the opposite extreme or splitting at the mean/median adds interiors
        # that true extremum selection leaves empty.  Unequal span/interior
        # areas within both ties teach inclusive area.  The extreme groups
        # occupy opposite diagonal corners of a 2x3 region layout under D4.
        boxes = [(0, 1, 5, 6), (20, 21, 23, 29),
                 (4, 22, 6, 29), (17, 0, 20, 5),
                 (2, 11, 5, 17), (15, 11, 18, 18)]
        return _render(24, 30, boxes, rng, interleave_tie_colors=True)
    if slot == 3:
        return _render(12, 24, [(1, 1, 5, 5), (4, 9, 9, 12), (0, 16, 2, 22)], rng)
    if slot == 4:
        # One smallest, one largest, and three rectangles tied in the middle.
        shapes = ((5, 5), (3, 8), (6, 4), (4, 6), (3, 4))
        return _render(18, 26, _partitioned_boxes(18, 26, 2, 3, shapes, rng), rng)
    if slot == 5:
        return _query_profile(2, rng)
    raise ValueError("unknown training slot")


def _query_profile(slot: int, rng: random.Random) -> list[list[int]]:
    if slot == 0:
        return _render(3, 3, [(0, 0, 2, 2)], rng)
    if slot == 1:
        return _render(8, 11, [(1, 1, 5, 4), (0, 7, 6, 9)], rng)
    if slot == 2:
        shapes = ((9, 3), (3, 8), (6, 6), (4, 7), (8, 4), (5, 5))
        return _render(24, 26, _partitioned_boxes(24, 26, 2, 3, shapes, rng), rng)
    if slot == 3:
        # Nine pairs are the natural maximum with ARC's nine nonzero colors.
        # Their boxes occupy every 10x10 region and touch all four grid edges.
        # Sparse input is intrinsic to the task; the 242-cell outline carries
        # substantial geometry over the full canvas rather than padded content.
        shapes = ((10, 9), (6, 10), (8, 7), (7, 5), (9, 9),
                  (4, 10), (10, 6), (3, 8), (8, 10))
        boxes = _partitioned_boxes(30, 30, 3, 3, shapes, rng, touch_boundaries=True)
        return _render(30, 30, boxes, rng)
    raise ValueError("unknown query slot")


def _validate_grid(grid: list[list[int]]) -> None:
    if not grid or not grid[0] or not 1 <= len(grid) <= 30 or not 1 <= len(grid[0]) <= 30:
        raise AssertionError("sampled grid dimensions must be in 1..30")
    width = len(grid[0])
    positions: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(grid):
        if len(values) != width:
            raise AssertionError("sampled grids must be rectangular")
        for column, color in enumerate(values):
            if type(color) is not int or not 0 <= color <= 9:
                raise AssertionError("sampled cells must be literal ARC integers")
            if color:
                positions.setdefault(color, []).append((row, column))
    if not 1 <= len(positions) <= 9:
        raise AssertionError("samples require one to nine active colors")
    boxes = []
    for cells in positions.values():
        if len(cells) != 2:
            raise AssertionError("each sampled color must occur at exactly two corners")
        (r0, c0), (r1, c1) = cells
        top, bottom = sorted((r0, r1))
        left, right = sorted((c0, c1))
        if bottom - top < 2 or right - left < 2:
            raise AssertionError("sampled rectangle pairs must be diagonal and have an interior")
        box = (top, left, bottom, right)
        for other in boxes:
            if not (bottom < other[0] or other[2] < top or right < other[1] or other[3] < left):
                raise AssertionError("sampled rectangle bounding boxes must be disjoint")
        boxes.append(box)


def input_banks(seed: int) -> dict[str, list[list[list[int]]]]:
    """Return all six train inputs and four queries, independent of settings.

    SHA-derived local streams bind each candidate to (seed, split, slot,
    retry).  Retries only prevent duplicate grids in the complete ten-input
    bank; they never reject a rule output or consult a parameter setting.
    """
    if type(seed) is not int:
        raise TypeError("seed must be an integer, excluding bool")
    if not 0 <= seed <= MAX_SEED:
        raise ValueError("seed must be in 0..2**63-1")
    banks: dict[str, list[list[list[int]]]] = {"train": [], "test": []}
    seen: set[str] = set()
    for split, count in (("train", 6), ("test", 4)):
        for slot in range(count):
            for retry in range(MAX_DUPLICATE_ATTEMPTS):
                rng = _local_rng(seed, split, slot, retry)
                grid = _teaching_template(slot, rng) if split == "train" else _query_profile(slot, rng)
                _validate_grid(grid)
                identity = json.dumps(grid, separators=(",", ":"))
                if identity not in seen:
                    seen.add(identity)
                    banks[split].append(grid)
                    break
            else:
                raise RuntimeError(f"could not construct a unique {split} input at slot {slot} in 64 attempts")
    return banks
