from __future__ import annotations


def solve(grid):
    """Sort separator-delimited 3x3 tiles by increasing nonzero occupancy."""
    if not grid or len(grid) != 3 or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("expected a nonempty rectangular three-row grid")
    width = len(grid[0])
    if (width + 1) % 4 != 0:
        raise ValueError("expected 3-column tiles separated by one column")

    tiles = []
    for start in range(0, width, 4):
        tile = [row[start : start + 3] for row in grid]
        occupancy = sum(cell != 0 for row in tile for cell in row)
        tiles.append((occupancy, tile))
    tiles.sort(key=lambda item: item[0])

    output = [[], [], []]
    for index, (_, tile) in enumerate(tiles):
        if index:
            for row in output:
                row.append(9)
        for row_index, row in enumerate(tile):
            output[row_index].extend(row)
    return output
