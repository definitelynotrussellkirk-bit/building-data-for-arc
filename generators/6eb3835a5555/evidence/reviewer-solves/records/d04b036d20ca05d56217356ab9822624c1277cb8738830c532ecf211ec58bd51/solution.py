from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill a non-gray room iff it contains one distinct nonzero seed color."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height, width = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    seen: set[tuple[int, int]] = set()

    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] == 5 or (start_row, start_col) in seen:
                continue

            room: list[tuple[int, int]] = []
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            while stack:
                row, col = stack.pop()
                room.append((row, col))
                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row, next_col = row + drow, col + dcol
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] == 5 or (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            colors = {grid[row][col] for row, col in room if grid[row][col] not in (0, 5)}
            if len(colors) == 1:
                color = next(iter(colors))
                for row, col in room:
                    if grid[row][col] == 0:
                        output[row][col] = color

    return output
