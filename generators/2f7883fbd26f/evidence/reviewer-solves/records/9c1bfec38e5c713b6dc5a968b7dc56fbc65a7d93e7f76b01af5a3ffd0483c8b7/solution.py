"""Visible-example solution for the final-source post-repair episode."""


def solve(grid):
    if not grid or not grid[0]:
        return [[0, 0, 0, 0, 0]]

    height = len(grid)
    width = len(grid[0])
    count = 0
    for row in range(height - 1):
        for col in range(width - 1):
            if all(
                grid[row + dr][col + dc] == 1
                for dr in (0, 1)
                for dc in (0, 1)
            ):
                count += 1

    if not 0 <= count <= 5:
        raise ValueError(f"visible task count {count} is outside the five-cell encoding")
    return [[1] * count + [0] * (5 - count)]
