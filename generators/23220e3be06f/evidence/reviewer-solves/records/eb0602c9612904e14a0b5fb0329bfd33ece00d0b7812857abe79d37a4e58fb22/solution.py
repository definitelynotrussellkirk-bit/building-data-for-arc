from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Crop the remote object, then apply the flip encoded at (0, 0)."""
    if not grid or not grid[0]:
        return []

    marker = grid[0][0]
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) != (0, 0)
    ]
    if not points:
        return []

    r0 = min(r for r, _ in points)
    r1 = max(r for r, _ in points)
    c0 = min(c for _, c in points)
    c1 = max(c for _, c in points)
    cropped = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]

    if marker == 5:
        return [list(reversed(row)) for row in cropped]
    if marker == 6:
        return list(reversed(cropped))
    raise ValueError(f"unsupported transform marker: {marker}")
