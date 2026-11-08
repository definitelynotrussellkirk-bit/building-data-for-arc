from collections import deque


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    marker_cols = [c for c, value in enumerate(grid[-1]) if value == 1]

    seen = set()
    components = []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color in (0, 1) or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append((len(cells), color, cells))

    components.sort(key=lambda item: item[0])
    output = [[0] * width for _ in range(height)]
    for col in marker_cols:
        output[-1][col] = 1

    for marker_col, (_, color, cells) in zip(marker_cols, components):
        top = min(r for r, _ in cells)
        left = min(c for _, c in cells)
        normalized = [(r - top, c - left) for r, c in cells]
        shape_height = max(r for r, _ in normalized) + 1
        output_top = height - 1 - shape_height
        for dr, dc in normalized:
            output[output_top + dr][marker_col + dc] = color

    return output
