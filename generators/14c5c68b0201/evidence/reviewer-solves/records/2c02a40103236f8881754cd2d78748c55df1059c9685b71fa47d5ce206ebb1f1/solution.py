from collections import deque


def solve(grid):
    """Repeat each colored seed rectangle through its non-9 compartment."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]
    seen = set()

    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] == 9 or (start_r, start_c) in seen:
                continue

            component = []
            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 9
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            colored = [(r, c) for r, c in component if grid[r][c] != 0]
            if not colored:
                continue

            top = min(r for r, _ in colored)
            bottom = max(r for r, _ in colored)
            left = min(c for _, c in colored)
            right = max(c for _, c in colored)
            tile = [row[left : right + 1] for row in grid[top : bottom + 1]]
            tile_h = len(tile)
            tile_w = len(tile[0])

            for r, c in component:
                result[r][c] = tile[(r - top) % tile_h][(c - left) % tile_w]

    return result
