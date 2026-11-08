"""Move repeated-color corner objects inward by their own dimensions."""
from collections import Counter


def _components(grid, background):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if (row, col) in seen or grid[row][col] == background:
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c),
                               (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, cells))
    return components


def _moves(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    if not height or not width:
        return None, []
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    components = _components(grid, background)
    occurrence = Counter(color for color, cells in components)
    moves = []
    for color, cells in components:
        rows = [row for row, col in cells]
        cols = [col for row, col in cells]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        object_height = bottom - top + 1
        object_width = right - left + 1
        dr = dc = 0
        if occurrence[color] > 1:
            dr = object_height if top == 0 else -object_height if bottom == height - 1 else 0
            dc = object_width if left == 0 else -object_width if right == width - 1 else 0
        moves.append((color, cells, dr, dc))
    return background, moves


def solve(grid):
    output = [list(row) for row in grid]
    background, moves = _moves(grid)
    for color, cells, dr, dc in moves:
        if dr or dc:
            for row, col in cells:
                output[row][col] = background
    for color, cells, dr, dc in moves:
        for row, col in cells:
            output[row + dr][col + dc] = color
    return output
