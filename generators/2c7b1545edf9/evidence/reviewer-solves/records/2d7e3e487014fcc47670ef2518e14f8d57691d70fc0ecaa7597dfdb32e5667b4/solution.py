from __future__ import annotations


def solve(grid):
    """Extract the largest 4-connected non-background object.

    Objects are connected components of one non-zero color.  Equal-sized
    components are resolved in reading order (topmost, then leftmost), which
    matches the visible tie cases.  The chosen object is returned in its tight
    bounding box with all other cells set to background.
    """
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    seen = [[False] * width for _ in range(height)]
    components = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or seen[row][col]:
                continue

            stack = [(row, col)]
            seen[row][col] = True
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] == color
                    ):
                        seen[nr][nc] = True
                        stack.append((nr, nc))

            top = min(r for r, _ in cells)
            left = min(c for _, c in cells)
            bottom = max(r for r, _ in cells)
            right = max(c for _, c in cells)
            components.append((len(cells), top, left, bottom, right, color, cells))

    if not components:
        return [[0 for _ in range(width)] for _ in range(height)]

    # max cell count; stable row-major tie break
    _, top, left, bottom, right, color, cells = max(
        components, key=lambda item: (item[0], -item[1], -item[2])
    )
    output = [[0] * (right - left + 1) for _ in range(bottom - top + 1)]
    for row, col in cells:
        output[row - top][col - left] = color
    return output
