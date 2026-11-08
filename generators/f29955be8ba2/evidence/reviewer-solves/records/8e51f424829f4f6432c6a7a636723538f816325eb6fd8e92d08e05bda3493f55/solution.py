from typing import List

Grid = List[List[int]]


def solve(grid: Grid) -> Grid:
    """Drop the three-row key column and stack the three body bands in key order."""
    if not grid or not isinstance(grid, list):
        raise ValueError("grid must be a non-empty rectangular list")
    width = len(grid[0])
    if width < 2 or any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular with a key column and body")
    if len(grid) % 3:
        raise ValueError("grid height must split into three equal bands")

    order = [grid[row][0] for row in range(3)]
    if sorted(order) != [1, 2, 3]:
        raise ValueError("top key cells must be a permutation of 1, 2, 3")

    band_height = len(grid) // 3
    bands = [
        [row[1:] for row in grid[index * band_height : (index + 1) * band_height]]
        for index in range(3)
    ]
    return [row[:] for label in order for row in bands[label - 1]]
