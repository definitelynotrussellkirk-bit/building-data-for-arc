from collections import deque


def _components(grid, color):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            component = []
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(component)

    return components


def solve(grid):
    """Extract the main object whose color is selected at the upper-left corner."""
    if not grid or not grid[0]:
        return []

    selected_color = grid[0][0]
    components = _components(grid, selected_color)
    candidates = [component for component in components if (0, 0) not in component]
    if not candidates:
        # Defensive fallback for malformed inputs: crop the selector component itself.
        candidates = components
    if not candidates:
        return []

    target = max(candidates, key=len)
    min_row = min(row for row, _ in target)
    max_row = max(row for row, _ in target)
    min_col = min(col for _, col in target)
    max_col = max(col for _, col in target)

    target_cells = set(target)
    return [
        [selected_color if (row, col) in target_cells else 0 for col in range(min_col, max_col + 1)]
        for row in range(min_row, max_row + 1)
    ]
