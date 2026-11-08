"""Constructive input banks for the separate native orbit/link family.

The first three demos teach the source-independent clockwise orbit, long
first-hit links, and even-width centering. Six demos and four novel queries
are always constructed before slicing. No setting, label, global RNG, retry
loop, production generator, or reference-runtime process enters sampling.
"""
from __future__ import annotations

import hashlib
from random import Random


_SECTORS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
_DIAGONALS = ("NE", "SE", "SW", "NW")
_CANONICAL_L = frozenset({(0, 0), (0, 1), (1, 1)})
_SMALL_SHAPES = (
    frozenset({(0, 0), (0, 1), (0, 2), (1, 0)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 1)}),
    frozenset({(0, 0), (1, 0), (1, 1), (2, 0), (2, 1)}),
    frozenset({(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)}),
)


def _rng(seed: int, stream: str) -> Random:
    material = f"7fe59337a0b4/native-input-v1/{stream}/{seed}".encode("ascii")
    return Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _dims(shape):
    return max(row for row, col in shape) + 1, max(col for row, col in shape) + 1


def _rotate(shape):
    height, _ = _dims(shape)
    return frozenset((col, height - 1 - row) for row, col in shape)


def _reflect(shape, rng):
    if rng.randrange(2):
        _, width = _dims(shape)
        return frozenset((row, width - 1 - col) for row, col in shape)
    return frozenset(shape)


def _branched_shape(rng, height, *, min_branches=2, tail=2):
    """A connected irregular comb, optionally with a real enclosed hole.

    The top bar and lowest branch have an empty center-column row between
    them. The final `tail` rows are spine-only, so links must look inside the
    crop instead of stopping at its bounding box. Horizontal reflection is
    lawful; arbitrary quarter turns need not preserve disjoint orbit arms.
    """
    lowest = rng.randint(max(2, min_branches), height - tail)
    branch_count = rng.randint(min_branches, lowest)
    branches = {0, lowest, *rng.sample(range(1, lowest - 1), branch_count - 2)}
    shape = {(row, 0) for row in range(height)}
    shape.update((row, col) for row in branches for col in (1, 2))
    if rng.randrange(2):
        # A bridge creates holes without closing the axial gap below the hit.
        start, end = sorted(rng.sample(sorted(branches), 2))
        shape.update((row, 2) for row in range(start, end + 1))
    return _reflect(shape, rng)


def _even_shape(rng, height):
    """Width four makes opposite ray pairs sample different crop columns."""
    upper_branch = rng.randint(2, height - 3)
    shape = {(row, 0) for row in range(height)}
    shape.update((row, col) for row in (0, upper_branch) for col in (1, 2, 3))
    shape.add((height - 2, 1))
    # Only one bottom corner is occupied, avoiding the width-four NW contact.
    return _reflect(shape, rng)


def _placement_sets(shape, marker):
    """Geometry only: verify exact nonzero occupancy before emitting input."""
    mr, mc = marker
    parts = [shape]
    for _ in range(3):
        parts.append(_rotate(parts[-1]))
    assert len(set(parts)) == 4, "internal symmetric motif"
    heights, widths = zip(*map(_dims, parts))
    anchors = (
        (mr - 1 - heights[0], mc - widths[0] // 2),
        (mr - heights[1] // 2, mc + 2),
        (mr + 2, mc - widths[2] // 2),
        (mr - heights[3] // 2, mc - 1 - widths[3]),
    )
    return [frozenset((top + row, left + col) for row, col in part)
            for part, (top, left) in zip(parts, anchors)]


def _box_sector(top, left, height, width, marker):
    mr, mc = marker
    vertical = "N" if top + height <= mr else "S" if top > mr else ""
    horizontal = "W" if left + width <= mc else "E" if left > mc else ""
    return vertical + horizontal


def _scene(rng, size, shape, sector, color, *, boundary=False):
    height, width = _dims(shape)
    low, high = height + 1, size - height - 2
    assert low <= high, "internal motif/canvas mismatch"
    if boundary:
        marker = (rng.choice((low, high)), rng.choice((low, high)))
    else:
        marker = (rng.randint(low, high), rng.randint(low, high))
    placements = _placement_sets(shape, marker)
    occupied = {marker}
    for part in placements:
        assert all(0 <= row < size and 0 <= col < size for row, col in part)
        assert not occupied.intersection(part), "internal overlapping orbit arms"
        occupied.update(part)

    candidates = []
    for top in range(size - height + 1):
        for left in range(size - width + 1):
            if _box_sector(top, left, height, width, marker) != sector:
                continue
            if boundary and not (top == 0 or left == 0 or top + height == size or left + width == size):
                continue
            source = {(top + row, left + col) for row, col in shape}
            if source == placements[0]:
                continue
            candidates.append((top, left))
    assert candidates, "internal source-sector placement failure"
    top, left = rng.choice(candidates)
    grid = [[0] * size for _ in range(size)]
    grid[marker[0]][marker[1]] = 9
    for row, col in shape:
        grid[top + row][left + col] = color
    return grid


def _demo_bank(rng):
    palette = rng.sample(range(1, 9), 6)
    # Its off-center marker (3 or 5 on each axis) rules out canvas anchoring.
    demos = [_scene(rng, 9, _CANONICAL_L, "N", palette[0], boundary=True)]

    size = rng.choice((15, 17))
    height = rng.randint(5, (size - 3) // 2)
    notch = _branched_shape(rng, height, tail=3)
    demos.append(_scene(rng, size, notch, rng.choice(_DIAGONALS), palette[1]))

    size = rng.choice((16, 18))
    rectangle = _even_shape(rng, rng.randint(6, min(7, (size - 3) // 2)))
    demos.append(_scene(rng, size, rectangle, rng.choice(("E", "S", "W")), palette[2]))

    small = rng.choice(_SMALL_SHAPES)
    for _ in range(rng.randrange(4)):
        small = _rotate(small)
    demos.append(_scene(rng, rng.choice((10, 11)), small, rng.choice(_SECTORS), palette[3]))

    for index, sizes, heights in ((4, (19, 20), (6, 8)), (5, (23, 24), (8, 10))):
        size = rng.choice(sizes)
        height = rng.randint(heights[0], min(heights[1], (size - 3) // 2))
        shape = _branched_shape(rng, height)
        demos.append(_scene(rng, size, shape, rng.choice(_SECTORS), palette[index]))
    return demos


def _query_bank(rng):
    sizes = [13, 21, 26, 30]
    rng.shuffle(sizes)
    sectors = rng.sample(_SECTORS, 4)
    palette = rng.sample(range(1, 9), 4)
    height_ranges = {13: (4, 5), 21: (7, 9), 26: (10, 11), 30: (12, 12)}
    queries = []
    for size, sector, color in zip(sizes, sectors, palette):
        height = rng.randint(*height_ranges[size])
        shape = _branched_shape(rng, height, min_branches=5 if size == 30 else 2)
        queries.append(_scene(rng, size, shape, sector, color, boundary=size == 30))
    return queries


def inputs(seed: int, demos: int = 3, queries: int = 4) -> dict:
    """Return fresh grids only; the native adapter owns settings and labels.

    Three demos are the supported teaching floor. Query construction and order
    use a dedicated stream, and neither requested count affects either bank.
    """
    for name, value, low, high in (("seed", seed, 0, 2**63 - 1),
                                   ("demos", demos, 3, 6),
                                   ("queries", queries, 1, 4)):
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    train = _demo_bank(_rng(seed, "demos"))
    test = _query_bank(_rng(seed, "queries"))
    return {"train": train[:demos], "test": test[:queries]}
