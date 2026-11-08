from collections import deque


def solve(grid):
    """Move each marked colored object one diagonal step toward its marker corner."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    background = 7
    marker = 8
    output = [[background for _ in range(width)] for _ in range(height)]
    seen = set()

    # Objects of different colors may touch, so components must be split by color
    # rather than by merely being non-background.
    for start_r in range(height):
        for start_c in range(width):
            object_color = grid[start_r][start_c]
            if object_color in (background, marker) or (start_r, start_c) in seen:
                continue

            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))
            color_cells = []

            while queue:
                r, c = queue.popleft()
                color_cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == object_color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            marker_cells = {
                (nr, nc)
                for r, c in color_cells
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                for nr, nc in [(r + dr, c + dc)]
                if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] == marker
            }

            if len(marker_cells) != 1:
                for r, c in color_cells:
                    output[r][c] = object_color
                continue

            marker_r, marker_c = next(iter(marker_cells))
            object_cells = color_cells + [(marker_r, marker_c)]
            min_r = min(r for r, _ in object_cells)
            max_r = max(r for r, _ in object_cells)
            min_c = min(c for _, c in object_cells)
            max_c = max(c for _, c in object_cells)

            dr = -1 if marker_r == min_r else 1
            dc = -1 if marker_c == min_c else 1

            for r, c in object_cells:
                nr, nc = r + dr, c + dc
                if 0 <= nr < height and 0 <= nc < width:
                    output[nr][nc] = object_color

    return output
