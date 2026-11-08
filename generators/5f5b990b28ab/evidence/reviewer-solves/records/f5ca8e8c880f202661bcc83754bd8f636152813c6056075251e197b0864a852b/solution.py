from collections import deque


RANK_COLORS = (2, 4, 6, 7)


def _components(grid):
    """Return 4-connected nonzero components as coordinate lists."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    found = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue

            color = grid[row][col]
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []

            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            found.append(cells)

    return found


def _bounding_box_area(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def solve(grid):
    """Recolor gray rectangular objects by descending bounding-box size."""
    result = [row[:] for row in grid]
    components = sorted(_components(grid), key=_bounding_box_area, reverse=True)

    for rank, cells in enumerate(components):
        replacement = RANK_COLORS[rank]
        for row, col in cells:
            result[row][col] = replacement

    return result
