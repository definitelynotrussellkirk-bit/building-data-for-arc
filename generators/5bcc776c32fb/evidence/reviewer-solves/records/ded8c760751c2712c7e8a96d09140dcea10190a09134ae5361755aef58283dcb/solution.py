from __future__ import annotations


def solve(grid):
    """Mark the midpoint of each qualifying blue horizontal component."""
    output = [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen or grid[next_row][next_col] != 1:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            rows = {r for r, _ in cells}
            if len(rows) != 1 or len(cells) < 3 or len(cells) % 2 == 0:
                continue
            target_row = next(iter(rows))
            columns = sorted(c for _, c in cells)
            # Connectivity plus one-row shape implies a contiguous run, but
            # this guard keeps the inferred condition explicit.
            if columns != list(range(columns[0], columns[-1] + 1)):
                continue
            output[target_row][columns[len(columns) // 2]] = 2

    return output
