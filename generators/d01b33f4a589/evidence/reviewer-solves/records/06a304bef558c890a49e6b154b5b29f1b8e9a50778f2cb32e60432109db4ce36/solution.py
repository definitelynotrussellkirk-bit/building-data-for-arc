"""Corner-command hypothesis inferred from the visible demonstrations.

The accompanying visible_probe.py fits all eight D4 operations and four common
quadrant alignments. Only upper-left padding and the mapping below survive.
This module does not read examples, source generators, or reference labels.
"""
from __future__ import annotations


def _clockwise(a: list[list[int]]) -> list[list[int]]:
    rows, cols = len(a), len(a[0])
    return [[a[rows - 1 - r][c] for r in range(rows)] for c in range(cols)]


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid, list) or len(grid) < 2 or not isinstance(grid[0], list) or len(grid[0]) < 2:
        raise ValueError('Expected a rectangular grid with four distinct corners')
    rows, cols = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != cols for row in grid):
        raise ValueError('Ragged grid')
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError('Grid values must be integer colors 0..9')
    corners = [(0,0), (0,cols-1), (rows-1,0), (rows-1,cols-1)]
    commands = [grid[r][c] for r,c in corners]
    if any(command not in (1,2,3,4) for command in commands):
        raise ValueError('The demonstrations only identify commands 1..4')
    corner_set = set(corners)
    points = [(r,c,grid[r][c]) for r in range(rows) for c in range(cols)
              if grid[r][c] != 0 and (r,c) not in corner_set]
    if not points:
        raise ValueError('Missing non-corner motif')
    top, bottom = min(r for r,c,v in points), max(r for r,c,v in points)
    left, right = min(c for r,c,v in points), max(c for r,c,v in points)
    motif = [[0]*(right-left+1) for _ in range(bottom-top+1)]
    for r,c,value in points:
        motif[r-top][c-left] = value
    transforms = {
        1: _clockwise(motif),
        2: _clockwise(_clockwise(motif)),
        3: [row[::-1] for row in motif],
        4: [row[:] for row in motif[::-1]],
    }
    tiles = [transforms[command] for command in commands]
    cell_rows = max(len(tile) for tile in tiles)
    cell_cols = max(len(tile[0]) for tile in tiles)
    output = [[0]*(2*cell_cols) for _ in range(2*cell_rows)]
    for q, tile in enumerate(tiles):
        r0, c0 = (q//2)*cell_rows, (q%2)*cell_cols
        for r, row in enumerate(tile):
            output[r0+r][c0:c0+len(row)] = row
    return output
