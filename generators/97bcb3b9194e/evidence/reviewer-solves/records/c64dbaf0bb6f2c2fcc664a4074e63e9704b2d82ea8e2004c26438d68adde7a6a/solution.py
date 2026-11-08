def solve(grid):
    """Crop the separated nonzero rectangle with the fewest non-blue marks."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    seen = set()
    objects = []

    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] == 0 or (start_r, start_c) in seen:
                continue

            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            r1 = min(r for r, _ in cells)
            r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            c2 = max(c for _, c in cells)
            marks = sum(grid[r][c] != 1 for r, c in cells)
            objects.append((marks, r1, c1, r2, c2))

    if not objects:
        return []

    _, r1, c1, r2, c2 = min(objects, key=lambda item: item[0])
    return [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]
