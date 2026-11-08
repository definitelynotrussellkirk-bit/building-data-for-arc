from collections import deque


def _components_of_one(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            component = []
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(component)

    return components


def solve(grid):
    """Recolor the three 1-components by ascending area: 2, then 3, then 8."""
    result = [row[:] for row in grid]
    components = _components_of_one(grid)
    ordered = sorted(components, key=len)
    palette = (2, 3, 8)

    if len(ordered) != len(palette) or len({len(comp) for comp in ordered}) != 3:
        raise ValueError("expected exactly three 1-components with distinct sizes")

    for component, color in zip(ordered, palette):
        for row, col in component:
            result[row][col] = color
    return result
