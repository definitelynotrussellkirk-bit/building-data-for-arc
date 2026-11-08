"""Ten deterministic hole-matching scenes for current public parent8698868d.

The constructors use fixed layouts and mask families, with no retry or search.
Copy constructor source explicitly; the checking CLI is not part of the sampler.
"""
from collections import Counter


def _hole_mask(side, count):
    if side == 4:
        masks = {0: set(), 1: {(0, 0), (1, 0), (1, 1)}, 2: {(0, 0), (1, 1)}}
    elif side == 5:
        masks = {
            0: set(),
            1: {(0, 0), (0, 1), (1, 0), (1, 1), (2, 1)},
            2: {(0, 0), (0, 1), (1, 0), (2, 1), (2, 2)},
            3: {(0, 0), (0, 1), (2, 0), (2, 2)},
            4: {(0, 0), (0, 2), (1, 1), (2, 0)},
            5: {(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)},
        }
    elif side == 6:
        masks = {
            0: set(),
            1: {(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 1), (3, 1)},
            2: {(0, 0), (0, 1), (1, 0), (1, 1), (2, 2), (2, 3), (3, 2), (3, 3)},
            3: {(0, 0), (0, 1), (1, 0), (1, 1), (0, 3), (3, 0), (3, 1), (3, 2)},
            4: {(0, 0), (0, 2), (0, 3), (2, 0), (3, 0), (2, 2), (3, 2), (3, 3)},
            5: {(0, 0), (0, 2), (1, 1), (2, 0), (2, 2), (2, 3), (3, 3)},
        }
    else:
        raise ValueError("template side must be4,5,or6")
    return {(r + 1, c + 1) for r, c in masks[count]}


def _marker_mask(side, count):
    edge = side - 1
    return {
        0: set(),
        1: {(1, 1), (1, 2), (2, 1)},
        2: {(1, 1), (2, 1), (3, 3)},
        3: {(1, 1), (1, 2), (1, edge), (edge, 1)},
        4: {(0, 0), (0, edge), (edge, 0), (edge, edge)},
        5: {(0, 0), (0, edge), (edge, 0), (edge, edge), (side // 2, side // 2)},
    }[count]


def _orient(cells, side, turns, reflected):
    result = set()
    for r, c in cells:
        if reflected:
            c = side - 1 - c
        for _ in range(turns):
            r, c = c, side - 1 - r
        result.add((r, c))
    return result


def _scene(side, counts, board_rows, variant, vertical=False, stress=False):
    assert len(counts) == len(set(counts)) and len(counts) % board_rows == 0
    count = len(counts)
    block = side + 2
    board_cols = count // board_rows
    board_h, board_w = board_rows * block, board_cols * block
    if vertical:
        source_rows = min(3, count)
        source_cols = (count + source_rows - 1) // source_rows
    else:
        source_cols = 2 if count == 4 else min(3, count)
        source_rows = (count + source_cols - 1) // source_cols
    source_h = source_rows * side + source_rows - 1
    source_w = source_cols * side + source_cols - 1
    if vertical:
        raw_h, raw_w = max(board_h, source_h), board_w + 1 + source_w
    else:
        raw_h, raw_w = board_h + 1 + source_h, max(board_w, source_w)
    assert raw_h <= 30 and raw_w <= 30
    height = 30 if stress else min(30, raw_h + 2)
    width = 30 if stress else min(30, raw_w + 4)
    bg = 8 if variant % 2 == 0 else 4
    palette = [v for v in (0, 9, 2, 7, 1, 6, 3, 5, 8, 4) if v != bg]
    grid = [[bg] * width for _ in range(height)]
    if vertical:
        board_top = (height - board_h) // 2
        source_top = (height - source_h) // 2
        if variant % 2:
            board_left, source_left = width - board_w, 0
        else:
            board_left, source_left = 0, width - source_w
    else:
        board_left = 0 if variant % 2 == 0 else width - board_w
        source_left = (width - source_w) // 2
        if variant % 2:
            board_top, source_top = 0, height - source_h
        else:
            board_top, source_top = height - board_h, 0 if raw_h == height else 1
    pattern_masks = {}
    for key in counts:
        turns, reflected = (variant + key) % 4, bool((variant + key) % 2)
        pattern_masks[key] = _orient(_hole_mask(side, key), side, turns, reflected)
    for index, key in enumerate(counts):
        top = board_top + (index // board_cols) * block
        left = board_left + (index % board_cols) * block
        color = palette[(3 * index + variant) % len(palette)]
        markers = _orient(_marker_mask(side, key), side, (variant + key) % 4, bool((variant + key) % 2))
        for r in range(block):
            for c in range(block):
                assert grid[top + r][left + c] == bg
                grid[top + r][left + c] = bg if (r - 1, c - 1) in markers else color
    order = sorted(counts, key=lambda key: ((5 * key + 3 * variant) % 7, key))
    for index, key in enumerate(order):
        top = source_top + (index // source_cols) * (side + 1)
        left = source_left + (index % source_cols) * (side + 1)
        color = palette[(2 * key + 5 + variant) % len(palette)]
        for r in range(side):
            for c in range(side):
                assert grid[top + r][left + c] == bg
                grid[top + r][left + c] = bg if (r, c) in pattern_masks[key] else color
    color_counts = Counter(v for row in grid for v in row)
    assert color_counts[bg] > max(v for color, v in color_counts.items() if color != bg)
    return grid


def input_templates():
    demos = [
        _scene(5, (2, 0, 3, 1), 2, 0),
        _scene(6, (4, 1, 0, 3, 2, 5), 2, 1, stress=True),
        _scene(4, (1, 0), 1, 2),
        _scene(5, (3, 1, 2), 1, 3),
        _scene(6, (2, 4, 1, 0), 2, 4),
        _scene(5, (5, 2, 0, 4, 1, 3), 2, 5),
    ]
    queries = [
        _scene(4, (0, 2, 1), 1, 6),
        _scene(5, (4, 0, 1, 3), 2, 7),
        _scene(6, (3, 0, 2), 1, 8),
        _scene(5, (1, 5, 3, 0, 4, 2), 3, 9, vertical=True, stress=True),
    ]
    return demos, queries
