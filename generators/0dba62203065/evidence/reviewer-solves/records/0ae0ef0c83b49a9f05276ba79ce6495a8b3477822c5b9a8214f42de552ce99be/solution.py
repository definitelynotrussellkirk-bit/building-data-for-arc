from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Recolor each 4-connected body object from the header over its left edge."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]
    seen: set[tuple[int, int]] = set()

    for start_row in range(1, height):
        for start_col in range(width):
            if grid[start_row][start_col] != 1 or (start_row, start_col) in seen:
                continue

            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            component: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                component.append((row, col))
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = row + drow
                    next_col = col + dcol
                    if (
                        1 <= next_row < height
                        and 0 <= next_col < width
                        and grid[next_row][next_col] == 1
                        and (next_row, next_col) not in seen
                    ):
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))

            leftmost_col = min(col for _, col in component)
            replacement = grid[0][leftmost_col]
            for row, col in component:
                output[row][col] = replacement

    return output
