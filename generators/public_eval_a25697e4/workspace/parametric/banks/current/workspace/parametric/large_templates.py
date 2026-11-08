"""Deterministic scalable socket/key scenes; no search or rejection sampling.

Copy this construction source explicitly into the current task if adopted.
Independent checking in __main__ does not import the candidate native family.
"""


def _transform_cell(point, turns, reflected):
    r, c = point
    if reflected:
        c = -c
    for _ in range(turns):
        r, c = c, -r
    return r, c


def _paint_socket(grid, bg, origin, height, width, holes, color):
    assert color != bg
    for r in range(height):
        for c in range(width):
            if (r, c) not in holes:
                rr, cc = origin[0] + r, origin[1] + c
                assert grid[rr][cc] == bg
                grid[rr][cc] = color


def _paint_key(grid, bg, origin, head, tail, colors, turns, reflected):
    assert len(set(colors)) == 2 and bg not in colors and not head & tail
    colored = [(_transform_cell(p, turns, reflected), color)
               for color, cells in zip(colors, (head, tail)) for p in cells]
    r0 = min(r for (r, c), color in colored)
    c0 = min(c for (r, c), color in colored)
    occupied = set()
    for (r, c), color in colored:
        rr, cc = origin[0] + r - r0, origin[1] + c - c0
        assert 0 < rr < len(grid) - 1 and 0 < cc < len(grid[0]) - 1
        assert grid[rr][cc] == bg
        occupied.add((rr, cc))
    # One background cell separates every free key from other foreground.
    for r, c in occupied:
        for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            assert grid[rr][cc] == bg
    for (r, c), color in colored:
        grid[origin[0] + r - r0][origin[1] + c - c0] = color


def scene(height, width, l_size, triangle_size, frame, tail_size, reversed_roles=False):
    """Create two unique docks with fixed disjoint source-key placements.

    Supported profiles are listed in profiles(); constraints are checked by the
    construction and independently verified there. The sizes affect occupied
    shapes, not only padding. No alternate candidate placement is tried.
    """
    assert 3 <= triangle_size <= l_size <= 8
    assert 2 <= frame <= 3 and 2 <= tail_size <= 4
    assert 1 <= height <= 30 and 1 <= width <= 30
    if reversed_roles:
        bg, bottom_color, top_color = 8, 2, 7
        l_colors, triangle_colors = (5, 2), (7, 5)
    else:
        bg, bottom_color, top_color = 0, 9, 9
        l_colors = triangle_colors = (2, 6)
    grid = [[bg] * width for _ in range(height)]
    bottom_width, top_width = l_size + 2 * frame, triangle_size + 2 * frame
    bottom_origin = height - l_size, 2
    top_origin = 0, width - top_width - 2
    assert bottom_origin[0] > triangle_size and top_origin[1] > 0
    assert bottom_origin[1] + bottom_width < width - 1
    l_head = {(0, c) for c in range(l_size)} | {(r, 0) for r in range(1, l_size)}
    triangle = {(r, c) for r in range(triangle_size) for c in range(r + 1)}
    l_holes = {(r, c + frame) for r, c in l_head}
    triangle_holes = {(r, c + frame) for r, c in triangle}
    _paint_socket(grid, bg, bottom_origin, l_size, bottom_width, l_holes, bottom_color)
    _paint_socket(grid, bg, top_origin, triangle_size, top_width, triangle_holes, top_color)
    # The cells immediately above the L head become socket collisions under
    # its diagonal head symmetry. The same property holds for the triangle's
    # anti-diagonal symmetry, with its tail below the triangle's broad side.
    l_tail = {(r, c) for r in range(-tail_size, 0)
              for c in range(min(tail_size, l_size))}
    triangle_tail = {(r, c) for r in range(triangle_size, triangle_size + tail_size)
                     for c in range(1, 1 + min(tail_size, triangle_size - 1))}
    if reversed_roles:
        l_origin = triangle_size + 2, width - l_size - 3
        triangle_origin = height - l_size - triangle_size - tail_size - 2, 2
        _paint_key(grid, bg, l_origin, l_head, l_tail, l_colors, 0, True)
        _paint_key(grid, bg, triangle_origin, triangle, triangle_tail,
                   triangle_colors, 2, False)
    else:
        l_origin = 2, 2
        triangle_origin = height - triangle_size - tail_size - 2, width - triangle_size - 3
        _paint_key(grid, bg, l_origin, l_head, l_tail, l_colors, 1, False)
        _paint_key(grid, bg, triangle_origin, triangle, triangle_tail,
                   triangle_colors, 0, True)
    return grid


def large_scene(height, width, variant):
    """Root-facing API: explicitly supported dimensions, two parity roles."""
    assert type(variant) is int and variant in (0, 1)
    if (height, width) == (24, 28):
        sizes = (6, 5, 3, 4)
    elif (height, width) == (26, 28):
        sizes = (7, 5, 3, 4)
    elif (height, width) == (30, 30):
        sizes = (7, 6, 3, 4) if variant == 0 else (8, 7, 3, 4)
    else:
        raise ValueError("large_scene supports24x28,26x28,and30x30")
    return scene(height, width, *sizes, reversed_roles=bool(variant))


def profiles():
    return [
        ("rectangle16x22", scene(16, 22, 4, 3, 2, 2)),
        ("rectangle24x28_query", large_scene(24, 28, 0)),
        ("rectangle26x28_demo", large_scene(26, 28, 1)),
        ("dense30_demo", large_scene(30, 30, 0)),
        ("dense30_query", large_scene(30, 30, 1)),
    ]
