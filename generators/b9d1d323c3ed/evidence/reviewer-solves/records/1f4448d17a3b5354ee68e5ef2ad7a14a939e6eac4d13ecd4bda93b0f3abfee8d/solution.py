"""Visible-example solution: tightly crop nonzero cells and repeat sideways."""


def solve(grid):
    positions = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    if not positions:
        raise ValueError("The visible examples require nonzero foreground cells")
    top = min(r for r, _ in positions)
    bottom = max(r for r, _ in positions)
    left = min(c for _, c in positions)
    right = max(c for _, c in positions)
    cropped = [list(row[left:right + 1]) for row in grid[top:bottom + 1]]
    return [row + row for row in cropped]
