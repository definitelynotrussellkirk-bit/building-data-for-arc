"""Complete aligned interior marks between original anchors."""
from collections import Counter


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("Expected a rectangular grid")
    height, width = len(grid), len(grid[0])
    row_edges = [r for r in range(height) if all(value == 0 for value in grid[r])]
    col_edges = [c for c in range(width) if all(grid[r][c] == 0 for r in range(height))]
    if len(row_edges) < 2 or len(col_edges) < 2:
        raise ValueError("Expected framed cells separated by black lines")
    row_centers = [list(range(a + 2, b - 1)) for a, b in zip(row_edges, row_edges[1:])]
    col_centers = [list(range(a + 2, b - 1)) for a, b in zip(col_edges, col_edges[1:])]
    if any(len(rows) != 2 for rows in row_centers) or any(len(cols) != 2 for cols in col_centers):
        raise ValueError("Expected four-by-four frames with two-by-two interiors")
    common = Counter(grid[r][c] for rows in row_centers for cols in col_centers
                     for r in rows for c in cols).most_common(1)[0][0]
    out = [row[:] for row in grid]
    for dy in range(2):
        for dx in range(2):
            layer = [[grid[rows[dy]][cols[dx]] for cols in col_centers] for rows in row_centers]
            colors = sorted({value for row in layer for value in row} - {0, common})
            for color in colors:
                for r, row in enumerate(layer):
                    anchors = [c for c, value in enumerate(row) if value == color]
                    if len(anchors) >= 2:
                        for c in range(min(anchors), max(anchors) + 1):
                            out[row_centers[r][dy]][col_centers[c][dx]] = color
                for c in range(len(col_centers)):
                    anchors = [r for r in range(len(row_centers)) if layer[r][c] == color]
                    if len(anchors) >= 2:
                        for r in range(min(anchors), max(anchors) + 1):
                            out[row_centers[r][dy]][col_centers[c][dx]] = color
    return out
