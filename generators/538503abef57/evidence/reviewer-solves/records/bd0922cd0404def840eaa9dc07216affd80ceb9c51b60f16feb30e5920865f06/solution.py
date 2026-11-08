"""Infer each object's anti-diagonal reflection from the visible examples."""


def components(grid):
    """Return four-connected, monochromatic nonzero components."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            cells = []
            pending = [(row, col)]
            seen.add((row, col))
            while pending:
                r, c = pending.pop()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            found.append((color, cells))
    return found


def solve(grid):
    """Reflect each component across its bounding box's other diagonal."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0] * width for _ in range(height)]
    for color, cells in components(grid):
        top = min(r for r, _ in cells)
        left = min(c for _, c in cells)
        box_height = max(r for r, _ in cells) - top + 1
        box_width = max(c for _, c in cells) - left + 1
        for r, c in cells:
            new_r = top + box_width - 1 - (c - left)
            new_c = left + box_height - 1 - (r - top)
            output[new_r][new_c] = color
    return output
