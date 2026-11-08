from __future__ import annotations


def _runs(indices: list[int]) -> list[tuple[int, int]]:
    """Return inclusive contiguous runs from an ordered index list."""
    if not indices:
        return []
    runs: list[tuple[int, int]] = []
    start = previous = indices[0]
    for value in indices[1:]:
        if value != previous + 1:
            runs.append((start, previous))
            start = value
        previous = value
    runs.append((start, previous))
    return runs


def solve(grid: list[list[int]]) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0])

    # The all-zero rows and columns are dividers.  Discover the three occupied
    # row/column bands rather than hard-coding their coordinates.
    occupied_rows = [r for r in range(height) if any(grid[r][c] != 0 for c in range(width))]
    occupied_cols = [c for c in range(width) if any(grid[r][c] != 0 for r in range(height))]
    row_runs = _runs(occupied_rows)
    col_runs = _runs(occupied_cols)

    blocks: list[tuple[int, list[list[int]]]] = []
    for r0, r1 in row_runs:
        for c0, c1 in col_runs:
            block = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]
            blocks.append((sum(value == 1 for row in block for value in row), block))

    blocks.sort(key=lambda item: item[0])
    output = [[0 for _ in range(width)] for _ in range(height)]

    # Smallest blocks go left-to-right in the bottom band, then the middle
    # band, then the largest blocks in the top band.
    destinations = [
        (row_run, col_run)
        for row_run in reversed(row_runs)
        for col_run in col_runs
    ]
    for (_, block), ((r0, r1), (c0, c1)) in zip(blocks, destinations):
        assert len(block) == r1 - r0 + 1
        assert all(len(row) == c1 - c0 + 1 for row in block)
        for dr, row in enumerate(block):
            for dc, value in enumerate(row):
                output[r0 + dr][c0 + dc] = value
    return output
