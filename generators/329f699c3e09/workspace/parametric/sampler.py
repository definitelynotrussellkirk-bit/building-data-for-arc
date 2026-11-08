"""Constructive matched-input banks for the reflected-probe route family."""
from __future__ import annotations

import hashlib
from random import Random


def _rng(seed, stream):
    digest = hashlib.sha256(f"329f699c3e09/probe-route-v1/{stream}/{seed}".encode()).digest()
    return Random(int.from_bytes(digest, "big"))


def _paint_rect(grid, top, left, height, width, color):
    for r in range(top, top + height):
        for c in range(left, left + width):
            grid[r][c] = color


def _vertical_scene(rng, size, side, *, large=False):
    grid = [[0] * size for _ in range(size)]
    div = size // 2
    for r in range(size): grid[r][div] = 7
    gap = 2 if size < 20 else 3
    source_col = div - gap if side == "left" else div + gap
    probe_col = div + gap if side == "left" else div - gap
    target_dir = 1 if side == "left" else -1
    source_dir = -target_dir
    route_rows = [size // 3, (2 * size) // 3]
    target_colors = rng.sample([1, 2, 5, 9], 2)
    source_colors = rng.sample([3, 4], 2)
    if large:
        heights = [4, 5]; widths = [5, 6]
    else:
        heights = [2 + rng.randrange(2), 2 + rng.randrange(2)]
        widths = [2 + rng.randrange(2), 2 + rng.randrange(2)]
    for i, row in enumerate(route_rows):
        grid[row][source_col] = 6
        th, tw = heights[i], widths[i]
        top = max(0, min(size - th, row - th // 2))
        # Keep one blank ray cell between each probe/source and its object.
        # The chosen half widths intentionally make a distance of two fit even
        # for the smallest 13x13 scene and the widest 6-cell stress object.
        first_target = probe_col + target_dir * 2
        left = first_target if target_dir > 0 else first_target - tw + 1
        assert 0 <= left and left + tw <= size
        _paint_rect(grid, top, left, th, tw, target_colors[i])
        dh, dw = heights[1 - i], widths[i]
        dtop = max(0, min(size - dh, row - dh // 2))
        first_source = source_col + source_dir * 2
        dleft = first_source if source_dir > 0 else first_source - dw + 1
        assert 0 <= dleft and dleft + dw <= size
        _paint_rect(grid, dtop, dleft, dh, dw, source_colors[i])

    # Anti-shortcut controls.  A selected color is cloned on the source side so
    # the correct rule must apply the ray-selected color globally, not only to
    # the hit object or opposite half.  A substantial unused-color rectangle on
    # the probe side defeats the shortcut "recolor every object over there."
    source_edge = 0 if side == "left" else size - 1
    grid[size - 2][source_edge] = target_colors[0]
    grid[size - 1][source_edge] = target_colors[0]
    unused = next(color for color in (1, 2, 5, 9) if color not in target_colors)
    distractor_left = div + 1 if side == "left" else div - 3
    _paint_rect(grid, 0, distractor_left, 2, 3, unused)
    return grid


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _scene(rng, size, orientation, side, *, large=False):
    grid = _vertical_scene(rng, size, side, large=large)
    return grid if orientation == "vertical" else _transpose(grid)


def _bank(rng, specs):
    return [_scene(rng, size, orientation, side, large=large)
            for size, orientation, side, large in specs]


def inputs(seed, demos=3, queries=4):
    for name, value, low, high in (("seed", seed, 0, 2**63 - 1),
                                   ("demos", demos, 2, 6),
                                   ("queries", queries, 1, 4)):
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    demos_all = _bank(_rng(seed, "demos"), [
        (13, "vertical", "left", False),
        (15, "horizontal", "right", False),
        (17, "vertical", "right", False),
        (19, "horizontal", "left", False),
        (21, "vertical", "left", True),
        (23, "horizontal", "right", True),
    ])
    queries_all = _bank(_rng(seed, "queries"), [
        (16, "horizontal", "left", False),
        (20, "vertical", "right", False),
        (24, "horizontal", "right", True),
        (30, "vertical", "left", True),
    ])
    return {"train": demos_all[:demos], "test": queries_all[:queries]}
