"""Visible-example solution for the orthogonal-neighbor-shell task."""

CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = set()
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, cells))
    return components


def solve(grid):
    """Erase each colored blob and color all zero cardinal neighbors."""
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    for color, cells in _components(grid):
        for row, col in cells:
            for dr, dc in CARDINAL:
                nr, nc = row + dr, col + dc
                if (
                    0 <= nr < height
                    and 0 <= nc < width
                    and (nr, nc) not in cells
                    and grid[nr][nc] == 0
                ):
                    output[nr][nc] = color
    return output
