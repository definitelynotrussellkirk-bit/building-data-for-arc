def solve(grid):
    """Keep monochromatic four-connected components away from the border."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]
    visited = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in visited:
                continue

            component = []
            stack = [(row, col)]
            visited.add((row, col))
            touches_border = False

            while stack:
                r, c = stack.pop()
                component.append((r, c))
                if r == 0 or r == height - 1 or c == 0 or c == width - 1:
                    touches_border = True

                for nr, nc in ((r - 1, c), (r + 1, c),
                               (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in visited
                            and grid[nr][nc] == color):
                        visited.add((nr, nc))
                        stack.append((nr, nc))

            if not touches_border:
                for r, c in component:
                    output[r][c] = color

    return output
