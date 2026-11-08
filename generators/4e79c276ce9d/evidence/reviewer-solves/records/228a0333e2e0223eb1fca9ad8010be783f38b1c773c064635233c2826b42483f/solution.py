"""Infer the requested object from the public examples only."""


def solve(grid):
    """Return a tight crop of the smallest nonzero monochromatic component."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    smallest = None

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            cells = []
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            if smallest is None or len(cells) < len(smallest[1]):
                smallest = (color, cells)

    if smallest is None:
        raise ValueError('The visible examples all contain a nonzero object.')

    color, cells = smallest
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    output = [[0] * (right - left + 1) for _ in range(bottom - top + 1)]
    for r, c in cells:
        output[r - top][c - left] = color
    return output
