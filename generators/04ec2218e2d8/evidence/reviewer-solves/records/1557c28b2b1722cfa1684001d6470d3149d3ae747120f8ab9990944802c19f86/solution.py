from collections import deque


def _components_of_eight(grid):
    """Yield 4-connected components consisting of color 8 cells."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 8 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            component = []
            while queue:
                current_row, current_col = queue.popleft()
                component.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and grid[next_row][next_col] == 8
                        and (next_row, next_col) not in seen
                    ):
                        seen.add((next_row, next_col))
                        queue.append((next_row, next_col))
            yield component


def solve(grid):
    """Recolor each cyan object by its own bbox center and quadrants."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]
    if any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be rectangular")

    output = [list(row) for row in grid]
    for component in _components_of_eight(grid):
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        height = bottom - top + 1
        width = right - left + 1
        inset = max(2, min(height, width) // 4)

        for row, col in component:
            relative_row = row - top
            relative_col = col - left
            if (
                inset <= relative_row < height - inset
                and inset <= relative_col < width - inset
            ):
                color = 4
            elif 2 * relative_row < height and 2 * relative_col < width:
                color = 6
            elif 2 * relative_row < height:
                color = 1
            elif 2 * relative_col < width:
                color = 2
            else:
                color = 3
            output[row][col] = color

    return output
