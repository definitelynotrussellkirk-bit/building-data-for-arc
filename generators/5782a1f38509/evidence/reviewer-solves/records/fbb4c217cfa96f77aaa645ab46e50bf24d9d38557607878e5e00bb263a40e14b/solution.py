from collections import deque


def solve(grid):
    """Pack monochromatic 4-connected objects by increasing cell count."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    objects = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
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
                        queue.append((nr, nc))

            min_row = min(r for r, _ in cells)
            max_row = max(r for r, _ in cells)
            min_col = min(c for _, c in cells)
            max_col = max(c for _, c in cells)
            crop = [
                [
                    color if (r, c) in cells else 0
                    for c in range(min_col, max_col + 1)
                ]
                for r in range(min_row, max_row + 1)
            ]
            objects.append((len(cells), min_row, min_col, crop))

    if not objects:
        return []

    objects.sort(key=lambda item: (item[0], item[1], item[2]))
    crops = [item[3] for item in objects]
    out_height = max(len(crop) for crop in crops)
    out_width = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    output = [[0] * out_width for _ in range(out_height)]

    offset = 0
    for crop in crops:
        for r, row_values in enumerate(crop):
            output[r][offset : offset + len(row_values)] = row_values
        offset += len(crop[0]) + 1

    return output
