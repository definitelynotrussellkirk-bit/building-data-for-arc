from collections import deque


def solve(grid):
    """Keep the body component whose area equals the number of row-0 blue cells."""
    h, w = len(grid), len(grid[0])
    target_area = sum(value == 1 for value in grid[0])
    output = [[0 for _ in range(w)] for _ in range(h)]
    seen = set()

    for start_r in range(1, h):
        for start_c in range(w):
            color = grid[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue
            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        1 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            if len(cells) == target_area:
                for r, c in cells:
                    output[r][c] = color

    return output
