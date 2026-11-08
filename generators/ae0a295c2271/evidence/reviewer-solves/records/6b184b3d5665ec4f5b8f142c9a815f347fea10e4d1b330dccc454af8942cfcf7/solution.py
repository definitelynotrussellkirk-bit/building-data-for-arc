from collections import Counter, deque


def _objects(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    objects = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
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
            min_r = min(r for r, _ in cells)
            min_c = min(c for _, c in cells)
            signature = tuple(sorted((r - min_r, c - min_c) for r, c in cells))
            objects.append((cells, signature))

    return objects


def solve(grid):
    """Colour exact translated shape classes blue when repeated, red when unique."""
    objects = _objects(grid)
    frequencies = Counter(signature for _, signature in objects)
    output = [[0 for _ in row] for row in grid]
    for cells, signature in objects:
        colour = 1 if frequencies[signature] > 1 else 2
        for row, col in cells:
            output[row][col] = colour
    return output
