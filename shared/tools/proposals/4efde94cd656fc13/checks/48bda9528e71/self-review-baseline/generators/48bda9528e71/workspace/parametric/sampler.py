"""Constructive native inputs for rare-color extent projection.

Roles vary actual geometry and color frequencies on square canvases up to 30.
Crosses, notches and stairs teach concave row/column extents; rectangles and
diamonds supply controls. Each role has a private deterministic random stream.
No input depends on the output-mode setting and no generation retry is used.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import random

from reviewer_support import load_selected_generator

HERE = Path(__file__).resolve().parent
_selected, _, _ = load_selected_generator('48bda9528e71', root=HERE.parents[3])
_COLORS = tuple(color for color in range(10) if color != 8)


def _rng(seed, role):
    data = hashlib.sha256(f'48bda9528e71:native-inputs-v1:{seed}:{role}'.encode()).digest()
    return random.Random(int.from_bytes(data, 'big'))


def _cross(height, width, arm):
    row0, col0 = (height - arm) // 2, (width - arm) // 2
    return {(r, c) for r in range(height) for c in range(width)
            if row0 <= r < row0 + arm or col0 <= c < col0 + arm}


def _notch(height, width, arm_h, arm_w):
    return {(r, c) for r in range(height) for c in range(width)
            if r < arm_h or c < arm_w}


def _stairs(height):
    return {(r, c) for r in range(height) for c in range(3 + 2 * (r // 2))}


def _diamond(radius):
    return {(r, c) for r in range(2 * radius + 1) for c in range(2 * radius + 1)
            if abs(r - radius) + abs(c - radius) <= radius}


def _shifted_stair(height, width):
    return {(r, c) for r in range(height) for c in range(r // 2, r // 2 + width)}


def _size(cells):
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _orient(grid, rng):
    for _ in range(rng.randrange(4)):
        grid = _selected._rotate90(grid)
    if rng.randrange(2):
        grid = _selected._reflect(grid)
    return grid


def _paint(size, mask, offset, rng, *, rare_count, color_count,
           rare_color=None, rare_cells=None, common_patch=None):
    height, width = _size(mask)
    row0, col0 = offset
    if not (0 <= row0 <= size - height and 0 <= col0 <= size - width):
        raise ValueError('constructed shape does not fit its canvas')
    if not 7 <= len(mask) <= (size * size - 1) // 2:
        raise ValueError('constructed shape violates the occupied-cell budget')
    if not _selected._is_connected(mask) or not _selected._is_orthogonally_convex(mask):
        raise ValueError('constructed shape must be connected and orthogonally convex')
    interior = _selected._interior_cells(mask)
    if rare_cells is None:
        # Avoid making the bounding-box center a rare-color locator when the
        # shape admits other choices. The minimum 5x5 role has one interior.
        centers = {(r, c) for r in {(height - 1) // 2, height // 2}
                   for c in {(width - 1) // 2, width // 2}}
        candidates = sorted(interior - centers)
        if len(candidates) < rare_count:
            candidates = sorted(interior)
        rare_cells = set(rng.sample(candidates, rare_count))
    else:
        rare_cells = set(rare_cells)
    if len(rare_cells) != rare_count or not rare_cells <= interior:
        raise ValueError('rare cells must have all four occupied cardinal neighbors')
    if rare_color is None:
        rare_color = rng.choice(_COLORS)
    common_colors = rng.sample([color for color in _COLORS if color != rare_color], color_count - 1)
    if color_count == 3:
        if common_patch is None:
            center_r, center_c = (height - 1) / 2, (width - 1) / 2
            candidates = sorted(mask - rare_cells,
                                key=lambda p: (abs(p[0] - center_r) + abs(p[1] - center_c), p))
            patch = set(candidates[:rare_count + 5])
            patch_color = common_colors[1]
        else:
            patch, patch_color = set(common_patch[0]), common_patch[1]
            # A deliberate color-zero distractor is a normal foreground patch.
            common_colors = [rng.choice([c for c in _COLORS if c not in (rare_color, patch_color)])]
        if patch & rare_cells or not patch <= mask:
            raise ValueError('common-color patch overlaps rare cells or background')
        if not rare_count < len(patch) < len(mask) - len(patch) - rare_count:
            raise ValueError('common colors must have distinct frequencies above the rare count')
    else:
        patch, patch_color = set(), None
    grid = [[8] * size for _ in range(size)]
    for r, c in mask:
        color = rare_color if (r, c) in rare_cells else (patch_color if (r, c) in patch else common_colors[0])
        grid[row0 + r][col0 + c] = color
    return _orient(grid, rng)


def _role(seed, role):
    rng = _rng(seed, role)
    if role == 'demo0':
        height, width, arm = rng.choice((9, 11)), rng.choice((11, 13)), 5
        mask = _cross(height, width, arm)
        size = max(height, width) + rng.randint(3, 5)
        offset = (rng.randint(1, size - height - 1), rng.randint(1, size - width - 1))
        center_r, center_c = height // 2, width // 2
        rare_count = rng.choice((3, 4))
        rare_cells = [(1, center_c), (center_r, 1), (center_r, width - 2)]
        if rare_count == 4:
            rare_cells.append((height - 2, center_c))
        patch = {(r, c) for r in (center_r - 1, center_r)
                 for c in (center_c - 1, center_c, center_c + 1)}
        return _paint(size, mask, offset, rng, rare_count=rare_count, color_count=3,
                      rare_color=rng.choice([c for c in _COLORS if c != 0]),
                      rare_cells=rare_cells, common_patch=(patch, 0))
    if role == 'demo1':
        height, width = rng.randint(7, 10), rng.randint(8, 11)
        mask = _notch(height, width, 3, rng.choice((3, 4)))
        size = rng.randint(12, 15)
        offset = (0, size - width)
        options = dict(rare_count=rng.choice((1, 2)), color_count=2, rare_color=0)
    elif role == 'demo2':
        height = rng.choice((10, 12))
        mask = _stairs(height)
        width = _size(mask)[1]
        size = rng.randint(15, 18)
        offset = (size - height, rng.randint(0, size - width))
        options = dict(rare_count=5, color_count=3)
    elif role == 'demo3':
        height, width = rng.randint(5, 7), rng.randint(6, 9)
        mask = {(r, c) for r in range(height) for c in range(width)}
        size = rng.randint(12, 18)
        offset = (rng.randint(0, size - height), rng.randint(0, size - width))
        options = dict(rare_count=rng.randint(1, 4), color_count=2)
    elif role == 'demo4':
        mask = _diamond(rng.randint(5, 7))
        height, width = _size(mask)
        size = rng.randint(18, 23)
        offset = (rng.randint(0, size - height), rng.randint(0, size - width))
        options = dict(rare_count=rng.randint(4, 7), color_count=3)
    elif role == 'demo5':
        mask = _shifted_stair(rng.randint(9, 12), rng.randint(5, 7))
        height, width = _size(mask)
        size = rng.randint(16, 20)
        offset = (rng.randint(0, size - height), rng.randint(0, size - width))
        options = dict(rare_count=5, color_count=3)
    elif role == 'query0':
        mask = _notch(4, 4, 2, 2)
        size = 5
        offset = (rng.randrange(2), rng.randrange(2))
        options = dict(rare_count=1, color_count=2)
    elif role == 'query1':
        mask = _stairs(12)
        size = 16
        offset = (rng.randrange(5), rng.randrange(4))
        options = dict(rare_count=5, color_count=3)
    elif role == 'query2':
        mask = _diamond(10)
        size = 24
        offset = (rng.randrange(4), rng.randrange(4))
        options = dict(rare_count=rng.randint(6, 9), color_count=3)
    elif role == 'query3':
        mask = _cross(30, 30, rng.choice((5, 7)))
        size = 30
        offset = (0, 0)
        options = dict(rare_count=rng.randint(9, 11), color_count=3)
    else:
        raise ValueError('unknown native role')
    return _paint(size, mask, offset, rng, **options)


def sample_inputs(seed, demos=3, queries=4):
    """Return independent fresh input banks, with stable count prefixes."""
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError('seed must be an integer in 0..2**63-1')
    if type(demos) is not int or not 3 <= demos <= 6:
        raise ValueError('demos must be an integer in 3..6')
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError('queries must be an integer in 1..4')
    train = [_role(seed, f'demo{index}') for index in range(6)]
    test = [_role(seed, f'query{index}') for index in range(4)]
    return train[:demos], test[:queries]
