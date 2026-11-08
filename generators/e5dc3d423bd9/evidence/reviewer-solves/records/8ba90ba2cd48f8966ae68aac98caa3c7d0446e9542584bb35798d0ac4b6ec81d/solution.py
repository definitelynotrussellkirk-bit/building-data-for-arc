from collections import deque


def solve(grid):
    """Fill the unique center of each odd-by-odd nonzero object."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for r0 in range(height):
        for c0 in range(width):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue

            queue = deque([(r0, c0)])
            seen.add((r0, c0))
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
            max_r = max(r for r, _ in cells)
            min_c = min(c for _, c in cells)
            max_c = max(c for _, c in cells)
            box_h = max_r - min_r + 1
            box_w = max_c - min_c + 1
            if box_h % 2 == 1 and box_w % 2 == 1:
                out[(min_r + max_r) // 2][(min_c + max_c) // 2] = color

    return out
