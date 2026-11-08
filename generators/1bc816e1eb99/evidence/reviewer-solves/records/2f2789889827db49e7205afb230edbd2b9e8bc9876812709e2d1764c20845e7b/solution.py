from collections import deque


def _components(grid):
    """Return four-connected components of non-background cells."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
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
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(component)
    return components


def _encloses_hole(component):
    """Whether a component surrounds at least one background cell."""
    occupied = set(component)
    min_row = min(r for r, _ in component)
    max_row = max(r for r, _ in component)
    min_col = min(c for _, c in component)
    max_col = max(c for _, c in component)

    outside = set()
    queue = deque()

    # Within the component's bounding box, every empty boundary cell is
    # connected to the exterior. Flood from all such cells.
    for row in range(min_row, max_row + 1):
        for col in (min_col, max_col):
            if (row, col) not in occupied and (row, col) not in outside:
                outside.add((row, col))
                queue.append((row, col))
    for col in range(min_col, max_col + 1):
        for row in (min_row, max_row):
            if (row, col) not in occupied and (row, col) not in outside:
                outside.add((row, col))
                queue.append((row, col))

    while queue:
        row, col = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = row + dr, col + dc
            if not (min_row <= nr <= max_row and min_col <= nc <= max_col):
                continue
            if (nr, nc) in occupied or (nr, nc) in outside:
                continue
            outside.add((nr, nc))
            queue.append((nr, nc))

    for row in range(min_row, max_row + 1):
        for col in range(min_col, max_col + 1):
            if (row, col) not in occupied and (row, col) not in outside:
                return True
    return False


def solve(grid):
    """Recolor objects with enclosed holes azure (8), all others red (2)."""
    result = [row[:] for row in grid]
    for component in _components(grid):
        replacement = 8 if _encloses_hole(component) else 2
        for row, col in component:
            result[row][col] = replacement
    return result
