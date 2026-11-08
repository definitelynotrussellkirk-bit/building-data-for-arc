"""Visible-example solution for the blind ARC episode.

For each 4-connected non-background object, erase the object and place one
pixel of its color at the upper-left-biased center of its bounding box.
"""


def solve(grid):
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen = [[False for _ in range(width)] for _ in range(height)]

    for start_r in range(height):
        for start_c in range(width):
            color = grid[start_r][start_c]
            if color == 0 or seen[start_r][start_c]:
                continue

            stack = [(start_r, start_c)]
            seen[start_r][start_c] = True
            min_r = max_r = start_r
            min_c = max_c = start_c

            while stack:
                r, c = stack.pop()
                min_r = min(min_r, r)
                max_r = max(max_r, r)
                min_c = min(min_c, c)
                max_c = max(max_c, c)

                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] == color
                    ):
                        seen[nr][nc] = True
                        stack.append((nr, nc))

            center_r = (min_r + max_r) // 2
            center_c = (min_c + max_c) // 2
            output[center_r][center_c] = color

    return output
