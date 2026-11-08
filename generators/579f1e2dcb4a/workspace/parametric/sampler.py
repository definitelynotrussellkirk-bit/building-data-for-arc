"""Deterministic input banks for component extraction and color-count ordering.

No policy or label enters this module.  Each call builds all six demonstrations
and four queries before the caller chooses a prefix.  The first three inputs
are constructive teaching scenes; later inputs vary geometry and scale.
"""
from __future__ import annotations

from collections import Counter, deque
import hashlib
import json
import random


K, X, Y, Z, W = 1, 2, 3, 4, 5
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _rng(seed, split, slot, retry):
    payload = json.dumps(["579f1e2dcb4a-inputs-v1", seed, split, slot, retry],
                         separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _rect(top, left, height, width):
    return [(r, c) for r in range(top, top + height)
            for c in range(left, left + width)]


def _paint(grid, cells, histogram, rng=None):
    cells = sorted(cells)
    colors = [color for color, count in histogram for _ in range(count)]
    if len(cells) != len(colors) or len(set(cells)) != len(cells):
        raise ValueError("component color counts must match its distinct cells")
    if rng is not None:
        rng.shuffle(colors)
    for (row, col), color in zip(cells, colors):
        if not (0 <= row < len(grid) and 0 <= col < len(grid[0])) or grid[row][col]:
            raise ValueError("component placement overlaps or escapes its canvas")
        grid[row][col] = color


def _ring_growth(top, left, height, width, count, rng):
    """Grow a connected shape from its complete bounding-box perimeter."""
    cells = {(r, c) for r in range(height) for c in range(width)
             if r in (0, height - 1) or c in (0, width - 1)}
    if not len(cells) <= count <= height * width:
        raise ValueError("ring-growth area is outside its lawful range")
    while len(cells) < count:
        frontier = sorted({(r + dr, c + dc) for r, c in cells for dr, dc in DIR4
                           if 0 <= r + dr < height and 0 <= c + dc < width
                           and (r + dr, c + dc) not in cells})
        if not frontier:
            raise ValueError("connected growth exhausted its bounding box")
        cells.add(rng.choice(frontier))
    return sorted((top + r, left + c) for r, c in cells)


def _demo_zero():
    grid = [[0] * 22 for _ in range(16)]
    _paint(grid, _rect(10, 0, 2, 4), [(K, 6), (Y, 2)])             # B8
    _paint(grid, [(1, c) for c in range(6, 11)] + [(2, 6), (3, 6)], [(X, 7)])
    _paint(grid, _rect(6, 12, 3, 3), [(K, 5), (X, 4)])             # A9
    _paint(grid, _rect(12, 18, 2, 2), [(X, 4)])                    # D4
    return grid


def _demo_one():
    grid = [[0] * 24 for _ in range(18)]
    _paint(grid, _rect(1, 1, 5, 1), [(K, 2), (Y, 3)])             # C5
    _paint(grid, _rect(9, 5, 3, 4), [(K, 7), (X, 5)])             # A12
    _paint(grid, _rect(3, 12, 2, 5), [(K, 3), (X, 7)])            # B10
    _paint(grid, _rect(14, 19, 2, 3), [(X, 6)])                   # D6
    return grid


def _demo_two():
    grid = [[0] * 19 for _ in range(14)]
    _paint(grid, [(10, 1), (10, 2), (11, 2)], [(Z, 3)])          # T3
    _paint(grid, [(12, 1)], [(Z, 1)])                            # S1
    anchor = [(1, c) for c in range(6, 11)] + [(r, 6) for r in range(2, 6)]
    _paint(grid, anchor, [(K, 5), (X, 4)])                       # A9
    _paint(grid, _rect(3, 8, 2, 3), [(K, 2), (X, 4)])            # E6, inside A's raw crop
    _paint(grid, _rect(8, 14, 2, 4), [(K, 6), (Y, 2)])           # B8
    return grid


def _query_zero(rng):
    grid = [[0] * 9 for _ in range(6)]
    _paint(grid, [(3, 0), (3, 1), (3, 2), (4, 0), (4, 1)], [(K, 3), (X, 2)], rng)
    _paint(grid, [(0, 6), (1, 6), (1, 7)], [(K, 1), (Y, 2)], rng)
    return grid


def _query_one(rng):
    # The palette-6, four-component canonical topology, including its diagonal
    # same-color split.  Only vertical reflection is allowed for this profile.
    grid = [[0] * 12 for _ in range(9)]
    _paint(grid, [(1, 1), (2, 1)], [(X, 2)])
    _paint(grid, [(1, 3), (2, 2), (2, 3)], [(K, 3)])
    _paint(grid, [(5, 6), (6, 6), (6, 7)], [(Y, 2), (Z, 1)])
    _paint(grid, [(2, 10), (2, 11), (3, 11)], [(W, 3)])
    _paint(grid, [(4, 10)], [(W, 1)])
    return grid


def _query_two(rng):
    grid = [[0] * 26 for _ in range(24)]
    specifications = (
        (14, 0, 6, 5, 24, [(K, 13), (X, 11)]),
        (0, 6, 4, 6, 20, [(K, 16), (Y, 4)]),
        (6, 13, 5, 4, 16, [(K, 4), (X, 12)]),
        (18, 18, 4, 3, 11, [(K, 2), (Y, 9)]),
        (11, 22, 3, 2, 6, [(Z, 6)]),
        (21, 25, 3, 1, 3, [(K, 2), (W, 1)]),
    )
    for top, left, height, width, count, histogram in specifications:
        _paint(grid, _ring_growth(top, left, height, width, count, rng), histogram, rng)
    return grid


def _query_three(rng):
    grid = [[0] * 30 for _ in range(30)]
    specifications = (
        (0, 0, 30, 8, 180, [(K, 110), (X, 70)]),
        (5, 9, 25, 9, 160, [(K, 140), (Y, 20)]),
        (9, 19, 21, 11, 120, [(K, 50), (Z, 70)]),
    )
    for top, left, height, width, count, histogram in specifications:
        _paint(grid, _ring_growth(top, left, height, width, count, rng), histogram, rng)
    return grid


_QUERY_BUILDERS = (_query_zero, _query_one, _query_two, _query_three)


def _validate_input(grid, expected_key):
    """Check construction invariants only; no output grids or ordering labels."""
    height, width = len(grid), len(grid[0])
    if not 1 <= height <= 30 or not 1 <= width <= 30:
        raise ValueError("input side exceeds 30")
    if any(len(row) != width or any(type(v) is not int or not 0 <= v <= 9 for v in row)
           for row in grid):
        raise ValueError("input is not a rectangular ARC grid")
    seen, components = set(), []
    for row in range(height):
        for col in range(width):
            if not grid[row][col] or (row, col) in seen:
                continue
            cells, pending = [], deque([(row, col)])
            seen.add((row, col))
            while pending:
                r, c = pending.popleft()
                cells.append((r, c))
                for dr, dc in DIR4:
                    nxt = r + dr, c + dc
                    if (0 <= nxt[0] < height and 0 <= nxt[1] < width
                            and grid[nxt[0]][nxt[1]] and nxt not in seen):
                        seen.add(nxt)
                        pending.append(nxt)
            components.append(cells)
    if not 2 <= len(components) <= 6:
        raise ValueError("scene must have two to six nonzero 4-components")
    largest = max(map(len, components))
    anchors = [cells for cells in components if len(cells) == largest]
    if len(anchors) != 1:
        raise ValueError("largest component must be unique")
    histogram = Counter(grid[r][c] for r, c in anchors[0])
    maximum = max(histogram.values())
    modes = [color for color, count in histogram.items() if count == maximum]
    if modes != [expected_key]:
        raise ValueError("largest component must have the intended unique mode")
    packed_width = sum(max(c for _, c in cells) - min(c for _, c in cells) + 1
                       for cells in components) + len(components) - 1
    if packed_width > 30:
        raise ValueError("raw component crops would pack wider than 30")


def _scene(seed, split, slot, retry, key_schedule):
    rng = _rng(seed, split, slot, retry)
    if split == "train" and slot < 3:
        grid = (_demo_zero, _demo_one, _demo_two)[slot]()
        profile = "demo_" + str(slot)
        key = key_schedule[slot]
    else:
        index = slot if split == "test" else slot - 3
        grid = _QUERY_BUILDERS[index](rng)
        profile = "query_" + str(index)
        key = rng.choice(tuple(range(1, 10)))
    other_colors = [color for color in range(1, 10) if color != key]
    rng.shuffle(other_colors)
    if profile in {"demo_0", "demo_1"}:
        # K is the anchor's majority color and X its minority color. Opposite
        # numeric relationships teach frequency instead of numeric min/max.
        # Reorder this existing permutation without another RNG draw, keeping
        # the reflection stream and all component geometry unchanged.
        accent = next(color for color in other_colors
                      if (color > key if profile == "demo_0" else color < key))
        other_colors = [accent] + [color for color in other_colors if color != accent]
    palette = [0, key] + other_colors
    grid = [[palette[value] for value in row] for row in grid]
    # Same-left singleton/triomino ties survive vertical reflection. Quarter
    # turns are excluded throughout, since packing is specifically horizontal.
    if profile != "query_3" and rng.randrange(2):
        grid = list(reversed(grid))
    if profile not in {"demo_2", "query_1"} and rng.randrange(2):
        grid = [list(reversed(row)) for row in grid]
    # Stress stays bottom-offset under horizontal reflection: its canonical
    # top alignment therefore remains visible instead of becoming an identity.
    _validate_input(grid, key)
    return grid


def input_banks(seed):
    """Return six train and four test inputs, using no settings or labels."""
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be a literal integer in 0..2**63-1")
    palette_order = _rng(seed, "key_schedule", 0, 0).sample(range(1, 10), 9)
    first_key = next(color for color in palette_order if color < 9)
    second_key = next(color for color in palette_order if color > 1 and color != first_key)
    third_key = next(color for color in palette_order if color not in {first_key, second_key})
    key_schedule = [first_key, second_key, third_key]
    banks, seen = {}, set()
    for split, count in (("train", 6), ("test", 4)):
        grids = []
        for slot in range(count):
            for retry in range(64):
                grid = _scene(seed, split, slot, retry, key_schedule)
                identity = json.dumps(grid, separators=(",", ":"))
                if identity not in seen:
                    seen.add(identity)
                    grids.append(grid)
                    break
            else:
                raise RuntimeError("bounded 64-attempt distinct-input construction exhausted")
        banks[split] = grids
    return banks
