from collections import deque


def solve(grid):
    """Recolor every orthogonally isolated nonzero cell to 9."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            component = []
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                current_row, current_col = queue.popleft()
                component.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor_row = current_row + delta_row
                    neighbor_col = current_col + delta_col
                    if not (0 <= neighbor_row < height and 0 <= neighbor_col < width):
                        continue
                    if (neighbor_row, neighbor_col) in seen:
                        continue
                    if grid[neighbor_row][neighbor_col] != color:
                        continue
                    seen.add((neighbor_row, neighbor_col))
                    queue.append((neighbor_row, neighbor_col))

            if len(component) == 1:
                only_row, only_col = component[0]
                out[only_row][only_col] = 9

    return out
