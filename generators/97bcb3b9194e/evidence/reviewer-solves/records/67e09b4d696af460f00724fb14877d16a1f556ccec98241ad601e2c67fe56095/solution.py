"""Visible-example hypothesis: crop the blue panel with the fewest accent cells."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    panels = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            cells = [(row, col)]
            seen.add((row, col))
            for rr, cc in cells:
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] != 0 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        cells.append((nr, nc))
            accents = sum(grid[rr][cc] != 1 for rr, cc in cells)
            panels.append((accents, cells))
    if not panels:
        return [row[:] for row in grid]
    _, selected = min(panels, key=lambda panel: panel[0])
    top = min(row for row, _ in selected)
    bottom = max(row for row, _ in selected)
    left = min(col for _, col in selected)
    right = max(col for _, col in selected)
    return [row[left:right + 1] for row in grid[top:bottom + 1]]
