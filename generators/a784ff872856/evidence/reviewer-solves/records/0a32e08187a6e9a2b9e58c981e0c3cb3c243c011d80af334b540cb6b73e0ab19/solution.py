from collections import Counter, deque


def solve(grid):
    """Extract non-background objects and stack them by decreasing width."""
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    if not rows or not cols:
        return []

    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    seen = set()
    objects = []

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == background or (r, c) in seen:
                continue

            color = grid[r][c]
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []

            while queue:
                cr, cc = queue.popleft()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            min_r = min(r0 for r0, _ in cells)
            max_r = max(r0 for r0, _ in cells)
            min_c = min(c0 for _, c0 in cells)
            max_c = max(c0 for _, c0 in cells)
            height = max_r - min_r + 1
            width = max_c - min_c + 1
            crop = [[background for _ in range(width)] for _ in range(height)]
            for r0, c0 in cells:
                crop[r0 - min_r][c0 - min_c] = color
            objects.append((width, min_r, min_c, crop))

    if not objects:
        return [[background]]

    objects.sort(key=lambda item: (-item[0], item[1], item[2]))
    output_width = max(width for width, _, _, _ in objects)
    output = []
    for index, (_, _, _, crop) in enumerate(objects):
        if index:
            output.append([background] * output_width)
        for row in crop:
            output.append(row + [background] * (output_width - len(row)))
    return output
