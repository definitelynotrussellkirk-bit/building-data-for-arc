"""Independent geometry oracle and inspection helpers for task 96d4a788da47.

This module deliberately does not import generator.py.  Task tests use it to
check the selected sampler against the canonical rule: each monochromatic
4-connected object is translated left by its own bounding-box minimum column.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from pathlib import Path
from typing import Iterable

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "96d4a788da47"


def load_generator():
    root = find_root(__file__)
    return load_selected_generator(TASK_ID, root=root)[0]


def labeled_canonical_pairs():
    return canonical_pairs(
        TASK_ID,
        root=find_root(__file__),
        labeled_only=True,
    )


def _rectangular_grid(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    rows = [list(row) for row in grid]
    if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("expected a nonempty rectangular grid")
    return rows


def color_components(grid) -> list[tuple[int, tuple[tuple[int, int], ...]]]:
    """Return deterministic monochromatic 4-connected components."""
    rows = _rectangular_grid(grid)
    h, w = len(rows), len(rows[0])
    unseen = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if rows[r][c] != 0
    }
    components = []
    while unseen:
        start = min(unseen)
        color = rows[start[0]][start[1]]
        unseen.remove(start)
        queue = deque([start])
        cells = [start]
        while queue:
            r, c = queue.popleft()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                nr, nc = nxt
                if (
                    0 <= nr < h
                    and 0 <= nc < w
                    and nxt in unseen
                    and rows[nr][nc] == color
                ):
                    unseen.remove(nxt)
                    queue.append(nxt)
                    cells.append(nxt)
        components.append((color, tuple(sorted(cells))))
    return components


def slide_left_reference(grid) -> list[list[int]]:
    """Independent Python mirror of the selected canonical rule."""
    rows = _rectangular_grid(grid)
    out = [[0 for _ in row] for row in rows]
    for color, cells in color_components(rows):
        left = min(c for _, c in cells)
        for r, c in cells:
            target = (r, c - left)
            if out[target[0]][target[1]] not in (0, color):
                raise ValueError("objects collide after independent left translation")
            out[target[0]][target[1]] = color
    return out


def bbox_fill_left_rival(grid) -> list[list[int]]:
    """Plausible canonical-fitting shortcut that destroys irregular shapes."""
    rows = _rectangular_grid(grid)
    out = [[0 for _ in row] for row in rows]
    for color, cells in color_components(rows):
        r0 = min(r for r, _ in cells)
        r1 = max(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        c1 = max(c for _, c in cells)
        width = c1 - c0 + 1
        for r in range(r0, r1 + 1):
            for c in range(width):
                if out[r][c] not in (0, color):
                    raise ValueError("rival rectangles collide")
                out[r][c] = color
    return out


def observed_axes(grid) -> dict[str, int]:
    rows = _rectangular_grid(grid)
    return {
        "grid_h": len(rows),
        "grid_w": len(rows[0]),
        "n_blobs": len(color_components(rows)),
    }


def component_is_filled_rectangle(cells) -> bool:
    cells = set(cells)
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return len(cells) == (r1 - r0 + 1) * (c1 - c0 + 1)


def has_nonrectangular_object(grid) -> bool:
    return any(not component_is_filled_rectangle(cells)
               for _, cells in color_components(grid))


def copy_grid(grid):
    return deepcopy(grid)
