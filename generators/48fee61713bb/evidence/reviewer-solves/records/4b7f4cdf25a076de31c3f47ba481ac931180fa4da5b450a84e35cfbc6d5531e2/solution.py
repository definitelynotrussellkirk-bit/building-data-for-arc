"""Decode hollow-square cells and apply border-directed stable packing."""

from functools import reduce
from math import gcd


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    edges = {
        'top': list(grid[0]),
        'right': [row[-1] for row in grid],
        'bottom': list(grid[-1]),
        'left': [row[0] for row in grid],
    }
    marked = [side for side, values in edges.items()
              if values[0] != 0 and all(value == values[0] for value in values)]
    if len(marked) != 1:
        raise ValueError('Expected one uniform nonzero border, as in the public examples.')

    ring_offsets = [(r, c) for r in range(3) for c in range(3) if (r, c) != (1, 1)]
    rings = []
    for r in range(height - 2):
        for c in range(width - 2):
            color = grid[r][c]
            if (color != 0 and grid[r + 1][c + 1] == 0
                    and all(grid[r + dr][c + dc] == color for dr, dc in ring_offsets)):
                rings.append((r, c, color))
    if not rings:
        raise ValueError('Expected hollow 3 by 3 squares.')

    row_positions = sorted({r for r, _, _ in rings})
    col_positions = sorted({c for _, c, _ in rings})
    row_gaps = [b - a for a, b in zip(row_positions, row_positions[1:])]
    col_gaps = [b - a for a, b in zip(col_positions, col_positions[1:])]
    row_step = reduce(gcd, row_gaps) if row_gaps else 4
    col_step = reduce(gcd, col_gaps) if col_gaps else 4
    top, left = row_positions[0], col_positions[0]
    rows = (row_positions[-1] - top) // row_step + 1
    cols = (col_positions[-1] - left) // col_step + 1
    cells = [[0] * cols for _ in range(rows)]
    for r, c, color in rings:
        cells[(r - top) // row_step][(c - left) // col_step] = color

    direction = {'top': 'right', 'right': 'down', 'bottom': 'left', 'left': 'up'}[marked[0]]
    if direction in ('left', 'right'):
        packed_rows = [[color for color in row if color != 0] for row in cells]
        output_width = max(map(len, packed_rows))
        if direction == 'right':
            return [[0] * (output_width - len(row)) + row for row in packed_rows]
        return [row + [0] * (output_width - len(row)) for row in packed_rows]

    packed_cols = [[cells[r][c] for r in range(rows) if cells[r][c] != 0]
                   for c in range(cols)]
    output_height = max(map(len, packed_cols))
    output = [[0] * cols for _ in range(output_height)]
    for c, column in enumerate(packed_cols):
        start = output_height - len(column) if direction == 'down' else 0
        for offset, color in enumerate(column):
            output[start + offset][c] = color
    return output
