"""Boundary-touching monochromatic objects become orange (7)."""
def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid or not grid[0]:
        return [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError('Grid must be rectangular')
    output = [row[:] for row in grid]
    seen = set()
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            pending = [(row, col)]
            seen.add((row, col))
            component = []
            touches_edge = False
            while pending:
                r, c = pending.pop()
                component.append((r, c))
                touches_edge |= r in (0, height - 1) or c in (0, width - 1)
                for nr, nc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            if touches_edge:
                for r, c in component:
                    output[r][c] = 7
    return output
