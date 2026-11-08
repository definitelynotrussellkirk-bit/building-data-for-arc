"""Constructive, setting-independent inputs for reflection then selection.

The first three demonstrations protect distinct semantic dependencies:
reflection joins source fragments and reverses component ranks; repeated colors
separate component area from color totals; diagonal contacts and sparse shapes
separate four-connectivity and occupied area from eight-connectivity and boxes.
No function in this module supplies an output label.
"""

from __future__ import annotations

import hashlib
import random


def _exact_integer(name, value, lower, upper):
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not lower <= value <= upper:
        raise ValueError(f"{name} must be in {lower}..{upper}")


def _rng(seed, purpose):
    digest = hashlib.sha256(f"reflection-components:v1:{seed}:{purpose}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _cells(kind, size):
    """Return palette slots and occupied source coordinates, never labels."""
    if kind == "merge":
        # Two disconnected dominoes complete to two zigzag tetrominoes.
        # A separate diagonal square ties them, including a boundary winner.
        return [
            (0, [(1, 4), (1, 5), (5, 2), (6, 2),
                 (size - 2, size - 2), (size - 2, size - 1),
                 (size - 1, size - 1)]),
            (1, [(8, 4), (8, 5), (8, 6)]),
        ]
    if kind == "color_totals":
        # Color zero totals twelve completed cells in six area-two objects.
        # Color one has both extrema: area-three lines and area-one points.
        return [
            (0, [(0, 4), (0, 5), (2, 8), (2, 9), (4, 11), (4, 12)]),
            (1, [(6, 10), (6, 11), (6, 12), (8, size - 1), (6, 6)]),
        ]
    if kind == "connectivity":
        # The four completed Ls each occupy five cells in a nine-cell box.
        # They touch diagonally; the area-six rectangles also touch a different
        # color orthogonally, exposing color-insensitive component detection.
        return [
            (0, [(0, 5), (0, 6), (0, 7), (1, 5), (2, 5),
                 (3, 6), (3, 7), (3, 8), (4, 6), (5, 6)]),
            (1, [(r, c) for r in (1, 2) for c in (8, 9, 10)]),
        ]
    if kind == "solid_minimum":
        return [
            (0, [(r, c) for r in (1, 2) for c in (7, 8)]),
            (1, [(4, 9), (4, 10), (4, 11), (5, 9), (6, 9)]),
        ]
    if kind == "hollow":
        # This upper half completes to a hollow square, preserving its hole.
        return [
            (0, [(2, 2), (2, 3), (2, 4), (2, 5), (3, 5), (4, 5), (5, 5)]),
            (1, [(0, c) for c in range(7, 12)]),
        ]
    if kind == "three_colors":
        return [
            (0, [(4, c) for c in range(2, 7)]),
            (1, [(1, 10), (1, 11), (2, 10)]),
            (2, [(r, c) for r in (9, 10) for c in (13, 14, 15)]),
        ]
    raise ValueError(f"unknown constructive scene: {kind}")


def _prefill_some_partners(grid, rng):
    """Exercise lawful matching pairs while reserving an incomplete orbit."""
    orbits = [(r, c) for r in range(len(grid)) for c in range(r + 1, len(grid))
              if bool(grid[r][c]) != bool(grid[c][r])]
    rng.shuffle(orbits)
    count = min(len(orbits) - 1, rng.randint(1, max(1, len(orbits) // 3)))
    for r, c in orbits[:count]:
        value = grid[r][c] or grid[c][r]
        grid[r][c] = grid[c][r] = value


def _grid(seed, name, kind, *, base_size=None, scale=1, margin=0, prefill=False):
    rng = _rng(seed, f"scene:{name}")
    minimum = {"merge": 10, "color_totals": 14, "connectivity": 12,
               "solid_minimum": 12, "hollow": 12, "three_colors": 16}[kind]
    size = rng.randint(minimum, minimum + 6) if base_size is None else base_size
    groups = _cells(kind, size)
    palette = rng.sample(range(1, 10), len(groups))
    side = size * scale + 2 * margin
    grid = [[0] * side for _ in range(side)]
    for slot, cells in groups:
        for row, col in cells:
            for dr in range(scale):
                for dc in range(scale):
                    grid[margin + row * scale + dr][margin + col * scale + dc] = palette[slot]
    if prefill:
        _prefill_some_partners(grid, rng)
    # These four board isometries commute with main-diagonal reflection.
    if rng.randrange(2):
        grid = [list(row) for row in zip(*grid)]
    if rng.randrange(2):
        grid = [list(reversed(row)) for row in reversed(grid)]
    return grid


def sample_inputs(seed: int, demos: int = 3, queries: int = 4) -> tuple[list, list]:
    """Return fresh demonstration/query inputs with prefixes fixed by seed.

    Settings are deliberately absent from this interface. Every call constructs
    the entire six-demo/four-query bank before slicing. A dedicated query-order
    stream prevents either requested count from changing query order. Queries
    use 14-, 24-, 28- and 30-square boards. The largest board contains scaled
    geometry spanning 27 rows and columns rather than extra empty padding.
    """
    _exact_integer("seed", seed, 0, (1 << 63) - 1)
    _exact_integer("demos", demos, 3, 6)
    _exact_integer("queries", queries, 1, 4)

    kinds = ("merge", "color_totals", "connectivity", "solid_minimum",
             "hollow", "three_colors")
    demo_bank = [_grid(seed, f"demo-{index}", kind, prefill=index >= 3)
                 for index, kind in enumerate(kinds)]
    query_bank = [
        _grid(seed, "query-merge", "merge", base_size=10, scale=3),
        _grid(seed, "query-color-totals", "color_totals", base_size=14,
              scale=2, prefill=True),
        _grid(seed, "query-connectivity", "connectivity", base_size=12,
              scale=2, prefill=True),
        _grid(seed, "query-solid-minimum", "solid_minimum", base_size=12,
              margin=1, prefill=True),
    ]
    _rng(seed, "query-order").shuffle(query_bank)
    return demo_bank[:demos], query_bank[:queries]
