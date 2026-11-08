from collections import deque


def solve(grid):
    """Return the second-largest 4-connected color-6 object, cropped and recolored 2."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 6 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            component = []
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 6
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(component)

    if len(components) < 2:
        raise ValueError("expected at least two color-6 components")

    # The two color-5 cells are a rank key: select rank 2 by component area.
    components.sort(key=len, reverse=True)
    chosen = components[1]
    chosen_cells = set(chosen)
    min_row = min(r for r, _ in chosen)
    max_row = max(r for r, _ in chosen)
    min_col = min(c for _, c in chosen)
    max_col = max(c for _, c in chosen)

    return [
        [2 if (r, c) in chosen_cells else 0 for c in range(min_col, max_col + 1)]
        for r in range(min_row, max_row + 1)
    ]
