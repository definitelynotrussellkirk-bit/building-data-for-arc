"""Visible-example solution. No generator, Racket, or reference imports."""
from __future__ import annotations


def _bands(length: int, separators: set[int]) -> list[list[int]]:
    groups: list[list[int]] = []
    for index in range(length):
        if index in separators:
            continue
        if not groups or index != groups[-1][-1] + 1:
            groups.append([])
        groups[-1].append(index)
    return groups


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    height, width = len(grid), len(grid[0])
    divider_rows = {r for r in range(height) if all(v == 9 for v in grid[r])}
    divider_cols = {c for c in range(width) if all(grid[r][c] == 9 for r in range(height))}
    row_groups, col_groups = _bands(height, divider_rows), _bands(width, divider_cols)
    tiles = [(rows, cols) for rows in row_groups for cols in col_groups]
    red_counts = [sum(grid[r][c] == 2 for r in rows for c in cols) for rows, cols in tiles]
    if not red_counts or max(red_counts) == 0 or red_counts.count(max(red_counts)) != 1:
        raise ValueError('Visible examples require a unique strongest red tile')
    source_index = red_counts.index(max(red_counts))
    marked = [i for i, (rows, cols) in enumerate(tiles)
              if any(grid[r][c] == 3 for r in rows for c in cols)]
    if len(marked) != 1 or marked[0] == source_index:
        raise ValueError('Expected one distinct marked target tile')
    sr, sc = tiles[source_index]
    tr, tc = tiles[marked[0]]
    if len(sr) != len(tr) or len(sc) != len(tc):
        raise ValueError('Source and target tiles must have equal dimensions')
    answer = [row[:] for row in grid]
    for i, r in enumerate(tr):
        for j, c in enumerate(tc):
            answer[r][c] = 8 if grid[sr[i]][sc[j]] == 2 else 0
    return answer
