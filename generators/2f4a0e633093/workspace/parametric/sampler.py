"""Constructive matched-input banks for the area-ranked gallery family."""
from __future__ import annotations

import hashlib
from random import Random


def _rng(seed, stream):
    digest = hashlib.sha256(f"2f4a0e633093/area-gallery-v1/{stream}/{seed}".encode()).digest()
    return Random(int.from_bytes(digest, "big"))


def _palette(rng):
    colors = rng.sample(range(1, 10), 6)
    return colors[:3], colors[3:]


def _put_mask(grid, top, left, mask, color):
    for r, row in enumerate(mask):
        for c, value in enumerate(row):
            if value:
                if grid[top + r][left + c] != 0:
                    raise AssertionError("shape collision")
                grid[top + r][left + c] = color


def _fixed_scene(rng, variant):
    grid = [[0] * 11 for _ in range(5)]
    legend, panel_colors = _palette(rng)
    for col, color in zip(rng.sample(range(11), 3), legend):
        grid[0][col] = color
    masks = [
        [[1, 1, 1], [1, 0, 0], [1, 1, 0]],  # area 6
        [[1, 1, 0], [0, 1, 0], [0, 0, 0]],  # area 3
        [[1, 1, 0], [0, 1, 0], [0, 1, 1]],  # area 5
    ]
    if variant % 2:
        masks[0] = [[1, 1, 0], [1, 0, 0], [1, 1, 0]]  # area 5
        masks[2] = [[1, 1, 1], [0, 1, 0], [1, 1, 0]]  # area 6
    for c0, color, mask in zip((0, 4, 8), panel_colors, masks):
        _put_mask(grid, 2, c0, mask, color)
    return grid


def _dense_mask(height, width, holes):
    mask = [[1] * width for _ in range(height)]
    candidates = [(r, c) for r in range(1, height - 1) for c in range(1, width - 1)]
    for r, c in candidates[:holes]:
        mask[r][c] = 0
    return mask


def _dynamic_scene(rng, height, width, specs, phase):
    grid = [[0] * width for _ in range(height)]
    legend, object_colors = _palette(rng)
    for col, color in zip(rng.sample(range(width), 3), legend):
        grid[0][col] = color
    # Specs are intentionally source-ordered largest, smallest, middle so the
    # area-ranked intermediate is never the encounter order.
    masks = [_dense_mask(h, w, holes) for h, w, holes in specs]
    areas = [sum(map(sum, mask)) for mask in masks]
    if not (areas[1] < areas[2] < areas[0]):
        raise AssertionError(f"bad area ordering: {areas}")
    gap = 1
    used_width = sum(len(mask[0]) for mask in masks) + gap * 2
    left = max(0, (width - used_width) // 2)
    top = 2 + (phase % max(1, height - 2 - max(len(mask) for mask in masks) + 1))
    for mask, color in zip(masks, object_colors):
        _put_mask(grid, top, left, mask, color)
        left += len(mask[0]) + gap
    return grid


def _scene(rng, spec, phase):
    kind = spec[0]
    if kind == "fixed":
        return _fixed_scene(rng, phase)
    _, height, width, shapes = spec
    return _dynamic_scene(rng, height, width, shapes, phase)


def _bank(rng, specs):
    return [_scene(rng, spec, index) for index, spec in enumerate(specs)]


def inputs(seed, demos=3, queries=4):
    for name, value, low, high in (("seed", seed, 0, 2**63 - 1),
                                   ("demos", demos, 2, 6),
                                   ("queries", queries, 1, 4)):
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    demos_all = _bank(_rng(seed, "demos"), [
        ("fixed",),
        ("fixed",),
        ("dynamic", 9, 13, ((3, 4, 0), (2, 3, 1), (3, 3, 1))),
        ("dynamic", 11, 15, ((4, 4, 0), (2, 3, 1), (3, 4, 1))),
        ("dynamic", 13, 17, ((4, 5, 0), (3, 3, 1), (4, 4, 1))),
        ("dynamic", 15, 19, ((5, 5, 1), (3, 4, 1), (4, 5, 1))),
    ])
    queries_all = _bank(_rng(seed, "queries"), [
        ("dynamic", 10, 14, ((3, 4, 0), (2, 3, 1), (3, 3, 1))),
        ("dynamic", 14, 18, ((4, 5, 0), (3, 3, 1), (4, 4, 1))),
        ("dynamic", 18, 22, ((5, 6, 1), (3, 4, 1), (4, 5, 1))),
        ("dynamic", 30, 30, ((7, 8, 0), (5, 6, 0), (6, 7, 0))),
    ])
    return {"train": demos_all[:demos], "test": queries_all[:queries]}
