from collections import Counter, deque


def _components(grid, background):
    """Return 4-connected, same-color non-background components."""
    height = len(grid)
    width = len(grid[0])
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == background or (row, col) in seen:
                continue

            todo = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while todo:
                r, c = todo.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            yield color, cells


def solve(grid):
    """Expand each small L's corner orientation into a large border-corner L."""
    height = len(grid)
    width = len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    result = [[background for _ in range(width)] for _ in range(height)]

    for color, cells in _components(grid, background):
        cell_set = set(cells)
        # The elbow is the unique occupied cell with one vertical and one
        # horizontal occupied neighbor. Its position in the component's 2x2
        # bounding box names the output corner.
        elbow = None
        for r, c in cells:
            vertical = any((r + dr, c) in cell_set for dr in (-1, 1))
            horizontal = any((r, c + dc) in cell_set for dc in (-1, 1))
            if vertical and horizontal:
                elbow = (r, c)
                break
        if elbow is None:
            continue

        min_row = min(r for r, _ in cells)
        max_row = max(r for r, _ in cells)
        min_col = min(c for _, c in cells)
        max_col = max(c for _, c in cells)
        elbow_row, elbow_col = elbow
        top = elbow_row == min_row
        left = elbow_col == min_col

        row_edge = 0 if top else height - 1
        col_edge = 0 if left else width - 1
        row_range = range(0, height // 2) if top else range(height - height // 2, height)
        col_range = range(0, width // 2) if left else range(width - width // 2, width)

        for col in col_range:
            result[row_edge][col] = color
        for row in row_range:
            result[row][col_edge] = color

    return result
