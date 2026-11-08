"""Independent, portable authoring oracle and geometry observations (not labels).

Never import this module during a visible-only solve: canonical() exposes answers.
The production reference remains Racket. This oracle supports regression tests.
"""
from pathlib import Path
import importlib.util
import os
from collections import deque

TASK_ID = 'f47990415137'


def load_generator():
    path = Path(os.environ.get('GENERATOR_UNDER_TEST', Path(__file__).resolve().parents[1] / 'generator.py'))
    spec = importlib.util.spec_from_file_location('reviewed_aspect_generator', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical():
    from reviewer_support import canonical_pairs, find_root
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def objects(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    result = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        queue = deque([start]); cells = []
        remaining.remove(start)
        while queue:
            r, c = queue.popleft(); cells.append((r, c))
            for p in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
                if p in remaining and grid[p[0]][p[1]] == color:
                    remaining.remove(p); queue.append(p)
        result.append((color, cells))
    return result


def dimensions(cells):
    return (max(r for r,c in cells)-min(r for r,c in cells)+1,
            max(c for r,c in cells)-min(c for r,c in cells)+1)


def aspect(cells):
    h, w = dimensions(cells)
    return 2 if h > w else 3 if w > h else 4


def python_oracle(grid, *, by_color=False, fill=False):
    groups = objects(grid)
    if by_color:
        merged = {}
        for color, cells in groups: merged.setdefault(color, []).extend(cells)
        groups = list(merged.items())
    out = [[0] * len(grid[0]) for _ in grid]
    for _, cells in groups:
        value = aspect(cells)
        if fill:
            cells = [(r,c) for r in range(min(r for r,c in cells),max(r for r,c in cells)+1)
                     for c in range(min(c for r,c in cells),max(c for r,c in cells)+1)]
        for r,c in cells: out[r][c] = value
    return out


def observation(grid):
    groups = objects(grid)
    return {'grid_h': len(grid), 'grid_w': len(grid[0]), 'n_blobs': len(groups),
            'n_distinct_colors': len({color for color, _ in groups})}
