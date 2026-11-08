from collections import deque


def _one_components(grid):
    """Return 4-connected components made from color 1."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue

            todo = deque([(row, col)])
            seen.add((row, col))
            component = []

            while todo:
                current_row, current_col = todo.popleft()
                component.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] != 1:
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    todo.append((next_row, next_col))

            yield component


def solve(grid):
    """Complete each framed pattern's top/bottom reflection using color 7."""
    result = [row[:] for row in grid]

    for component in _one_components(grid):
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)

        # Each color-1 component is the rectangular frame around one pattern.
        # Reflection across the horizontal midline maps row r to top+bottom-r.
        source_fours = [
            (row, col)
            for row in range(top + 1, bottom)
            for col in range(left + 1, right)
            if grid[row][col] == 4
        ]
        for row, col in source_fours:
            reflected_row = top + bottom - row
            if result[reflected_row][col] == 0:
                result[reflected_row][col] = 7

    return result
