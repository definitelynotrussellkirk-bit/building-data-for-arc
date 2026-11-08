"""Path-joining hypothesis derived from this episode's visible demonstrations."""
from __future__ import annotations


def _pieces(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    pieces = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        cells, stack = {first}, [first]
        while stack:
            r, c = stack.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == dc == 0:
                        continue
                    neighbor = r + dr, c + dc
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        cells.add(neighbor)
                        stack.append(neighbor)
        pieces.append(cells)
    return sorted(pieces, key=lambda cells: min(c for r, c in cells))


def solve(grid):
    """Keep the first path fixed; join later entry/exit endpoints in order."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('a nonempty rectangular grid is required')
    pieces = _pieces(grid)
    if not pieces:
        return [row[:] for row in grid]
    placed = []
    previous_exit = None
    for cells in pieces:
        entry = min(cells, key=lambda p: (p[1], p[0]))
        endpoints = [p for p in cells if sum((p[0] + dr, p[1] + dc) in cells
                     for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))) == 1]
        if len(endpoints) != 2 or entry not in endpoints:
            raise ValueError('piece is not an endpoint-entered orthogonal path')
        exit_cell = next(p for p in endpoints if p != entry)
        dr, dc = (0, 0) if previous_exit is None else (
            previous_exit[0] - entry[0], previous_exit[1] + 1 - entry[1])
        placed.extend((r + dr, c + dc, grid[r][c]) for r, c in cells)
        previous_exit = exit_cell[0] + dr, exit_cell[1] + dc
    width = max(c for r, c, value in placed) + 1
    result = [[0] * width for _ in grid]
    occupied = set()
    for r, c, value in placed:
        if not (0 <= r < len(grid) and 0 <= c < width) or (r, c) in occupied:
            raise ValueError('joining would clip or overlap a piece')
        occupied.add((r, c))
        result[r][c] = value
    return result
