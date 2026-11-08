from __future__ import annotations


def _border_edge(grid: list[list[int]]) -> str:
    """Return the edge marked by the solid line of color 1."""
    height = len(grid)
    width = len(grid[0])
    edges = {
        "top": all(grid[0][c] == 1 for c in range(width)),
        "right": all(grid[r][width - 1] == 1 for r in range(height)),
        "bottom": all(grid[height - 1][c] == 1 for c in range(width)),
        "left": all(grid[r][0] == 1 for r in range(height)),
    }
    marked = [name for name, present in edges.items() if present]
    if len(marked) != 1:
        raise ValueError(f"expected exactly one solid color-1 border, found {marked}")
    return marked[0]


def _decode_cells(grid: list[list[int]], edge: str) -> list[list[int]]:
    """Decode the 7x7 lattice of hollow 3x3 glyphs into one color per cell."""
    # A border on the low-coordinate side consumes the first line and one spacer;
    # otherwise the first glyph begins at coordinate 1.
    row0 = 2 if edge == "top" else 1
    col0 = 2 if edge == "left" else 1
    cells: list[list[int]] = []
    for r in range(7):
        row: list[int] = []
        for c in range(7):
            value = grid[row0 + 4 * r][col0 + 4 * c]
            row.append(0 if value == 1 else value)
        cells.append(row)
    return cells


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Remove gaps along the direction clockwise from the marked border."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be a non-empty rectangle")

    edge = _border_edge(grid)
    cells = _decode_cells(grid, edge)

    if edge in {"top", "bottom"}:
        packed = [[value for value in row if value != 0] for row in cells]
        width = max((len(row) for row in packed), default=0)
        if edge == "bottom":  # clockwise from bottom is left
            return [row + [0] * (width - len(row)) for row in packed]
        # clockwise from top is right
        return [[0] * (width - len(row)) + row for row in packed]

    columns = [
        [cells[r][c] for r in range(7) if cells[r][c] != 0]
        for c in range(7)
    ]
    height = max((len(column) for column in columns), default=0)
    result = [[0 for _ in range(7)] for _ in range(height)]
    for c, column in enumerate(columns):
        start = 0 if edge == "left" else height - len(column)
        for offset, value in enumerate(column):
            result[start + offset][c] = value
    return result
