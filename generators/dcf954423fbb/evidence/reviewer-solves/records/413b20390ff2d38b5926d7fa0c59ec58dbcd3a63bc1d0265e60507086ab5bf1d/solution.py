"""Visible-example solution for the reviewer-authored dcf954423fbb episode."""


def solve(grid):
    """Recolor each 4-connected blue component that touches any border."""
    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]
    seen = set()

    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] != 1 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            component = []
            touches_border = False
            while stack:
                row, col = stack.pop()
                component.append((row, col))
                touches_border |= row in (0, height - 1) or col in (0, width - 1)
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            if touches_border:
                for row, col in component:
                    output[row][col] = 2
    return output
