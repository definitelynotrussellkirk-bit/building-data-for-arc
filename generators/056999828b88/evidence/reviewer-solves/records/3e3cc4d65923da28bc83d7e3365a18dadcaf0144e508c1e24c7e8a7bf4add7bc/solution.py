from collections import deque


def solve(grid):
    """Pack nonzero 4-connected objects by increasing cell count."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = [[False] * width for _ in range(height)]
    objects = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or seen[row][col]:
                continue

            color = grid[row][col]
            queue = deque([(row, col)])
            seen[row][col] = True
            cells = []

            while queue:
                r, c = queue.popleft()
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
                        queue.append((nr, nc))

            min_r = min(r for r, _ in cells)
            max_r = max(r for r, _ in cells)
            min_c = min(c for _, c in cells)
            max_c = max(c for _, c in cells)
            crop = [
                [grid[r][c] for c in range(min_c, max_c + 1)]
                for r in range(min_r, max_r + 1)
            ]
            objects.append((len(cells), row, col, crop))

    objects.sort(key=lambda item: (item[0], item[1], item[2]))
    if not objects:
        return []

    out_height = max(len(crop) for _, _, _, crop in objects)
    out_width = sum(len(crop[0]) for _, _, _, crop in objects) + len(objects) - 1
    output = [[0] * out_width for _ in range(out_height)]

    offset = 0
    for _, _, _, crop in objects:
        for r, crop_row in enumerate(crop):
            output[r][offset : offset + len(crop_row)] = crop_row
        offset += len(crop[0]) + 1

    return output
