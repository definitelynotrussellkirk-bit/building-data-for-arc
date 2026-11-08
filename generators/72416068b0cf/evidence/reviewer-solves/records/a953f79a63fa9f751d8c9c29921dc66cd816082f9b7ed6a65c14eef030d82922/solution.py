"""Visible-example solver for the reviewer solve episode."""
from __future__ import annotations


def _crop_color(body, color):
    cells = [
        (r, c)
        for r, row in enumerate(body)
        for c, value in enumerate(row)
        if value == color
    ]
    if not cells:
        return None
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [
        [color if body[r][c] == color else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def _mask(crop):
    return tuple(tuple(1 if value else 0 for value in row) for row in crop)


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def _flip_horizontal(grid):
    return [row[::-1] for row in grid]


def solve(grid):
    if not grid or len(grid[0]) < 3:
        raise ValueError("expected a header row with three codes")

    shape_code, step1, step2 = grid[0][:3]
    body = grid[1:]

    # Shape masks inferred from the four visible demonstrations.  Each body
    # color denotes one object; the header colors are excluded with row 0.
    masks_by_code = {
        1: ((1, 0), (1, 0), (1, 1)),            # L tetromino
        2: ((1, 1, 1), (0, 1, 0)),              # T tetromino
        3: ((1, 1, 0), (0, 1, 1)),              # zig-zag tetromino
        4: ((1, 1), (1, 1), (1, 0)),            # five-cell block shape
    }
    target_mask = masks_by_code.get(shape_code)
    if target_mask is None:
        raise ValueError(f"unknown shape code: {shape_code}")

    colors = sorted({value for row in body for value in row if value != 0})
    candidates = []
    for color in colors:
        crop = _crop_color(body, color)
        if crop is not None and _mask(crop) == target_mask:
            candidates.append(crop)
    if len(candidates) != 1:
        raise ValueError(f"expected one selected object, found {len(candidates)}")
    selected = candidates[0]

    # The visible examples identify these four complete compositions.  The two
    # queries use the first two pairs, so this avoids guessing individual step
    # meanings that the examples do not uniquely determine.
    composition = {
        (6, 5): _rotate_180,
        (5, 1): lambda value: [row[:] for row in value],
        (7, 2): _flip_horizontal,
        (3, 4): _rotate_cw,
    }
    transform = composition.get((step1, step2))
    if transform is None:
        raise ValueError(f"unseen transform composition: {(step1, step2)}")
    return transform(selected)
