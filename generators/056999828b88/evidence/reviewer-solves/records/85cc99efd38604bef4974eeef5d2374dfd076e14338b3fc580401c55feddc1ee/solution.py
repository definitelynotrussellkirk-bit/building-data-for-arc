"""Infer individual connected objects, then pack their tight crops by size."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("expected integer colors in 0..9")
    height = len(grid)
    visited: set[tuple[int, int]] = set()
    pieces = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in visited:
                continue
            pending = [(row, col)]
            visited.add((row, col))
            cells = []
            while pending:
                r, c = pending.pop()
                cells.append((r, c))
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= rr < height and 0 <= cc < width
                            and (rr, cc) not in visited and grid[rr][cc] == color):
                        visited.add((rr, cc))
                        pending.append((rr, cc))
            top = min(r for r, c in cells)
            left = min(c for r, c in cells)
            normalized = [(r - top, c - left) for r, c in cells]
            ph = max(r for r, c in normalized) + 1
            pw = max(c for r, c in normalized) + 1
            pieces.append((len(cells), color, ph, pw, normalized))
    if not pieces:
        return [[0]]
    pieces.sort(key=lambda piece: (piece[0], piece[1]))
    out_height = max(piece[2] for piece in pieces)
    out_width = sum(piece[3] for piece in pieces) + len(pieces) - 1
    output = [[0] * out_width for _ in range(out_height)]
    offset = 0
    for size, color, ph, pw, cells in pieces:
        for r, c in cells:
            output[r][offset + c] = color
        offset += pw + 1
    return output
