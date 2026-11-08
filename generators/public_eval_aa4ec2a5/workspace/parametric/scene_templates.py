"""Constructive binary topology scenes for public parentaa4ec2a5.

All constructors use foreground1/background4. Scene augmentations may rename
those two roles while keeping semantic output colors2,6,8 reserved.
"""


def _ring(height, width, thickness=1, divide=False, arm=0, leak=False):
    cells = {(r, c) for r in range(height) for c in range(width)
             if r < thickness or r >= height - thickness
             or c < thickness or c >= width - thickness}
    if divide:
        cells |= {(r, width // 2) for r in range(height)}
    if arm:
        cells |= {(height // 2, c) for c in range(width, width + arm)}
    if leak:
        cells -= {(d, d) for d in range(thickness)}
    return cells


def _u(height, width, thickness=1):
    return {(r, c) for r in range(height) for c in range(width)
            if c < thickness or c >= width - thickness or r >= height - thickness}


def _solid(height, width, upper=None, lower_width=None):
    upper = height if upper is None else upper
    lower_width = width if lower_width is None else lower_width
    return {(r, c) for r in range(height) for c in range(width)
            if r < upper or c < lower_width}


def _turn(cells, turns=0, reflected=False):
    changed = []
    for r, c in cells:
        if reflected:
            c = -c
        for _ in range(turns):
            r, c = c, -r
        changed.append((r, c))
    r0, c0 = min(r for r, c in changed), min(c for r, c in changed)
    return {(r - r0, c - c0) for r, c in changed}


def _scene(height, width, placements):
    grid = [[4] * width for _ in range(height)]
    occupied = set()
    for origin, shape in placements:
        cells = {(origin[0] + r, origin[1] + c) for r, c in shape}
        assert all(0 <= r < height and 0 <= c < width for r, c in cells)
        expanded = {(r + dr, c + dc) for r, c in cells
                    for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
        assert not expanded & occupied, "foreground objects must have no8-neighbor contacts"
        for r, c in cells:
            grid[r][c] = 1
        occupied |= cells
    assert len(occupied) * 2 < height * width, "background must remain the unique modal color"
    return grid


def core0():
    return _scene(22, 29, [
        ((2, 2), _ring(7, 11, divide=True, arm=4)),
        ((2, 21), _ring(6, 6, leak=True)),
        ((12, 2), _u(7, 7)),
        ((12, 10), _solid(6, 7, upper=3, lower_width=4)),
        ((21, 28), {(0, 0)}),
    ])


def core1():
    return _scene(24, 28, [
        ((1, 2), _turn(_ring(7, 11, divide=True, arm=4), 1)),
        ((2, 16), _turn(_ring(7, 7, leak=True), 2)),
        ((13, 15), _turn(_u(7, 8), 1)),
        ((18, 0), _solid(4, 11)),
        ((23, 27), {(0, 0)}),
    ])


def dense30_demo():
    return _scene(30, 30, [
        ((0, 1), _ring(12, 12, thickness=2, divide=True, arm=3)),
        ((0, 18), _ring(12, 12, thickness=2, leak=True)),
        ((18, 1), _u(12, 12, thickness=2)),
        ((18, 18), _solid(12, 12, upper=6, lower_width=8)),
    ])


def dense30_query():
    return _scene(30, 30, [
        ((1, 1), _ring(13, 13, thickness=2, divide=True, arm=1)),
        ((1, 16), _turn(_ring(13, 13, thickness=2, leak=True), 3)),
        ((16, 1), _turn(_u(13, 13, thickness=2), 2)),
        ((16, 16), _solid(13, 13, upper=6, lower_width=8)),
    ])


def input_templates():
    demos = [core0(), core1(),
        _scene(10, 14, [((1, 1), _ring(6, 7, arm=3)), ((8, 12), {(0, 0)})]),
        _scene(14, 18, [((1, 1), _ring(5, 5, leak=True)),
                       ((1, 11), _solid(3, 5)), ((8, 9), _u(5, 6))]),
        _scene(20, 30, [((1, 1), _ring(8, 12, divide=True, arm=3)),
                       ((1, 21), _ring(8, 8, thickness=2, leak=True)),
                       ((12, 2), _turn(_u(6, 8), 2)),
                       ((12, 15), _solid(6, 9, upper=2, lower_width=5))]),
        dense30_demo(),
    ]
    queries = [
        _scene(9, 19, [((0, 1), _ring(4, 6, arm=3)),
                      ((0, 14), _ring(4, 4, leak=True)), ((6, 5), _u(3, 5))]),
        _scene(17, 23, [((0, 1), _ring(9, 9, leak=True)),
                       ((1, 15), _solid(6, 7, upper=2, lower_width=3)),
                       ((11, 2), _u(6, 7)), ((12, 15), _ring(4, 6))]),
        _scene(26, 19, [((1, 1), _turn(_ring(7, 9, divide=True, arm=3), 1)),
                       ((1, 11), _ring(7, 7, leak=True)),
                       ((17, 1), _turn(_u(6, 7), 2)),
                       ((18, 11), _solid(6, 7, upper=2, lower_width=4))]),
        dense30_query(),
    ]
    return demos, queries
