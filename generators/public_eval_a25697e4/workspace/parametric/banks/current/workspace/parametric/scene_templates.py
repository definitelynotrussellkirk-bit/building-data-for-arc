"""Two fresh constructive teaching templates for the current public parent.

The constructors use only built-in Python and are suitable for explicit source
copying into the task-owned sampler. No generator or prior packet is imported.
"""


def _turn(point, turns, reflected):
    r, c = point
    if reflected:
        c = -c
    for _ in range(turns):
        r, c = c, -r
    return r, c


def _socket(grid, background, origin, h, w, holes, color):
    for r in range(h):
        for c in range(w):
            if (r, c) not in holes:
                rr, cc = origin[0] + r, origin[1] + c
                assert grid[rr][cc] == background
                grid[rr][cc] = color


def _key(grid, background, origin, head, tail, colors, turns, reflected):
    assert not head & tail
    colored = [(_turn(p, turns, reflected), color)
               for color, cells in zip(colors, (head, tail)) for p in cells]
    r0 = min(r for (r, c), color in colored)
    c0 = min(c for (r, c), color in colored)
    for (r, c), color in colored:
        rr, cc = origin[0] + r - r0, origin[1] + c - c0
        assert grid[rr][cc] == background
        grid[rr][cc] = color


def core0():
    """Two same-color sockets; nearest pairing wrong; mixed rotation/reflection.

    The L head has a second geometric fit when its attached tail is ignored.
    That orientation sends a tail cell into the socket's left wall. Both keys
    share colors, so a global per-color object extraction is also incorrect.
    """
    background = 0
    grid = [[background] * 24 for _ in range(20)]
    left_holes = {(0, 1), (0, 2), (0, 3), (1, 1), (2, 1)}
    top_holes = {(0, 2), (1, 2), (1, 3), (2, 2), (2, 3), (2, 4)}
    _socket(grid, background, (17, 2), 3, 5, left_holes, 9)
    _socket(grid, background, (0, 16), 3, 6, top_holes, 9)
    l_head = {(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)}
    l_tail = {(-1, 0), (-2, 0), (-2, -1), (-3, -1), (-3, -2), (-4, -2)}
    triangle = {(0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2)}
    triangle_tail = {(3, 1), (4, 1), (4, 2), (5, 2), (5, 3), (6, 3)}
    _key(grid, background, (7, 14), l_head, l_tail, (2, 6), 1, False)
    _key(grid, background, (10, 7), triangle, triangle_tail, (2, 6), 0, True)
    return grid


def core1():
    """Shared key/socket colors, new sizes and directions, reversed parity roles.

    The L key's two parts have equal areas but different geometry. Its reflected
    placement swaps colors; the triangle undergoes a half-turn without a swap.
    A final whole-canvas quarter-turn makes the sockets left/right instead of
    top/bottom. Color2 occurs in a socket and in both free keys. The two keys
    use opposite head/tail color roles, so both numeric head-color orderings
    occur under every bijective palette permutation.
    """
    background = 8
    grid = [[background] * 26 for _ in range(22)]
    l_holes = {(0, c) for c in range(1, 5)} | {(r, 1) for r in range(1, 4)}
    triangle_holes = {(r, 2 + c) for r in range(4) for c in range(r + 1)}
    _socket(grid, background, (18, 3), 4, 6, l_holes, 2)
    _socket(grid, background, (0, 18), 4, 7, triangle_holes, 7)
    l_head = {(0, c) for c in range(4)} | {(r, 0) for r in range(1, 4)}
    l_tail = {(-1, 0), (-2, 0), (-2, 1), (-3, 1), (-3, 2), (-4, 2), (-4, 3)}
    triangle = {(r, c) for r in range(4) for c in range(r + 1)}
    triangle_tail = {(4, 2), (5, 2), (6, 2), (6, 1), (7, 1), (7, 0)}
    _key(grid, background, (8, 17), l_head, l_tail, (5, 2), 0, True)
    _key(grid, background, (8, 8), triangle, triangle_tail, (2, 5), 2, False)
    return [list(row) for row in zip(*grid[::-1])]


def teaching_cores():
    return [core0(), core1()]
