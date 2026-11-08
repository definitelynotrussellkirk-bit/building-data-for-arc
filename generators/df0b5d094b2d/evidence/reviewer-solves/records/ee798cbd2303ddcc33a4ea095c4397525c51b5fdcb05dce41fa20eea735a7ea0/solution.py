from collections import Counter, deque


def solve(grid):
    """Move each marked colored object one diagonal step toward its marker corner."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    background = 7
    marker = 8
    output = [[background for _ in range(width)] for _ in range(height)]
    seen = set()

    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] == background or (start_r, start_c) in seen:
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
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != background
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            marker_cells = [(r, c) for r, c in cells if grid[r][c] == marker]
            object_colors = [grid[r][c] for r, c in cells if grid[r][c] != marker]
            if len(marker_cells) != 1 or not object_colors:
                # The visible examples always use one marker per object. Preserve any
                # malformed component rather than silently deleting it.
                for r, c in cells:
                    output[r][c] = grid[r][c]
                continue

            object_color = Counter(object_colors).most_common(1)[0][0]
            marker_r, marker_c = marker_cells[0]
            min_r = min(r for r, _ in cells)
            max_r = max(r for r, _ in cells)
            min_c = min(c for _, c in cells)
            max_c = max(c for _, c in cells)

            dr = -1 if marker_r == min_r else 1 if marker_r == max_r else (-1 if marker_r * 2 < min_r + max_r else 1)
            dc = -1 if marker_c == min_c else 1 if marker_c == max_c else (-1 if marker_c * 2 < min_c + max_c else 1)

            for r, c in cells:
                nr, nc = r + dr, c + dc
                if 0 <= nr < height and 0 <= nc < width:
                    output[nr][nc] = object_color

    return output
