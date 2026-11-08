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
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
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
    """Stamp the largest red object's shape at every blue marker.

    A blue marker denotes the top-left corner of the red object's bounding box.
    The marker itself remains blue even when the corresponding template corner
    is empty. Existing non-background cells are preserved.
    """
    result = [row[:] for row in grid]
    if not grid or not grid[0]:
        return result

    red_components = _components(grid, 2)
    if not red_components:
        return result

    template = max(red_components, key=lambda cells: (len(cells), -min(cells)))
    min_row = min(row for row, _ in template)
    min_col = min(col for _, col in template)
    offsets = [(row - min_row, col - min_col) for row, col in template]

    markers = [
        (row, col)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if value == 1
    ]
    height = len(grid)
    width = len(grid[0])
    for anchor_row, anchor_col in markers:
        for dr, dc in offsets:
            row, col = anchor_row + dr, anchor_col + dc
            if 0 <= row < height and 0 <= col < width and result[row][col] in (0, 1):
                result[row][col] = 1
    return result
