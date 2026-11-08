"""Fill horizontal gaps within each same-colored connected object."""


def solve(grid):
    if not grid:
        return []

    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            seen.add((row, col))
            pending = [(row, col)]
            spans = {}
            while pending:
                r, c = pending.pop()
                if r in spans:
                    left, right = spans[r]
                    spans[r] = (min(left, c), max(right, c))
                else:
                    spans[r] = (c, c)

                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        pending.append((nr, nc))

            for r, (left, right) in spans.items():
                for c in range(left, right + 1):
                    if grid[r][c] == 0:
                        output[r][c] = color

    return output
