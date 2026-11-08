from collections import deque


def solve(grid):
    """Fill each gray-walled room with its sorted-color diagonal cycle."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] == 5 or (start_r, start_c) in seen:
                continue

            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))
            room = []

            while queue:
                r, c = queue.popleft()
                room.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if grid[nr][nc] == 5 or (nr, nc) in seen:
                        continue
                    seen.add((nr, nc))
                    queue.append((nr, nc))

            colors = sorted({grid[r][c] for r, c in room if grid[r][c] != 0})
            if not colors:
                continue

            top = min(r for r, _ in room)
            left = min(c for _, c in room)
            period = len(colors)
            for r, c in room:
                out[r][c] = colors[((r - top) + (c - left)) % period]

    return out
