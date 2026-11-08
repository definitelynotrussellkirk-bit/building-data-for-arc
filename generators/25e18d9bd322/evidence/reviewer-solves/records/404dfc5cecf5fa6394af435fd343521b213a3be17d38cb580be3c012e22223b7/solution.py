from collections import deque


def solve(grid):
    """Crop the nonzero, non-9 object nearest the singleton 9 marker."""
    height = len(grid)
    width = len(grid[0])
    marker = next(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 9
    )

    seen = set()
    objects = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color in (0, 9) or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor = (current_row + dr, current_col + dc)
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and neighbor not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            top = min(r for r, _ in cells)
            left = min(c for _, c in cells)
            bottom = max(r for r, _ in cells)
            right = max(c for _, c in cells)
            nearest = min(
                abs(marker[0] - r) + abs(marker[1] - c) for r, c in cells
            )
            objects.append((nearest, top, left, bottom, right, color, cells))

    _, top, left, bottom, right, color, cells = min(objects)
    output = [[0] * (right - left + 1) for _ in range(bottom - top + 1)]
    for row, col in cells:
        output[row - top][col - left] = color
    return output
