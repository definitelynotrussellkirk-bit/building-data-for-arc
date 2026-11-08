"""A solver inferred from the three public demonstrations in challenge.json."""


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("Expected a nonempty rectangular grid")
    # Insertion order records the first visible occurrence of each color.
    positions = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                positions.setdefault(value, []).append((r, c))
    result = [[0] * len(grid[0]) for _ in grid]
    for color, points in positions.items():
        if len(points) != 2:
            raise ValueError("The visible demonstrations use exactly two markers per color")
        top = min(r for r, _ in points)
        bottom = max(r for r, _ in points)
        left = min(c for _, c in points)
        right = max(c for _, c in points)
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                if r == top or r == bottom or c == left or c == right:
                    result[r][c] = color
    return result
