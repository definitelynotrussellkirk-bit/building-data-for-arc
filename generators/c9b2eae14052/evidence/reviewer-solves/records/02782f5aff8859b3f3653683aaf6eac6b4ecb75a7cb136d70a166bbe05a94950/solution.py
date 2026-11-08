from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Keep same-color 4-connected objects touching exactly one border."""
    if not grid or not grid[0]:
        return []

    height, width = len(grid), len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen: set[tuple[int, int]] = set()

    for row0 in range(height):
        for col0 in range(width):
            color = grid[row0][col0]
            if color == 0 or (row0, col0) in seen:
                continue

            stack = [(row0, col0)]
            seen.add((row0, col0))
            cells: list[tuple[int, int]] = []
            borders: set[str] = set()

            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                if row == 0:
                    borders.add("top")
                if row == height - 1:
                    borders.add("bottom")
                if col == 0:
                    borders.add("left")
                if col == width - 1:
                    borders.add("right")

                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row, next_col = row + drow, col + dcol
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))

            if len(borders) == 1:
                for row, col in cells:
                    output[row][col] = color

    return output
