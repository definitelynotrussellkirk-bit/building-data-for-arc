from __future__ import annotations


def _find_frame(grid: list[list[int]]) -> tuple[int, int, int, int, int]:
    """Return (color, top, left, bottom, right) for the largest solid rectangle border."""
    height = len(grid)
    width = len(grid[0])
    best: tuple[int, int, int, int, int] | None = None
    best_area = -1

    colors = {value for row in grid for value in row if value != 0}
    for color in colors:
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        if not cells:
            continue
        top = min(r for r, _ in cells)
        bottom = max(r for r, _ in cells)
        left = min(c for _, c in cells)
        right = max(c for _, c in cells)
        if top == bottom or left == right:
            continue

        perimeter = (
            [(top, c) for c in range(left, right + 1)]
            + [(bottom, c) for c in range(left, right + 1)]
            + [(r, left) for r in range(top + 1, bottom)]
            + [(r, right) for r in range(top + 1, bottom)]
        )
        if all(grid[r][c] == color for r, c in perimeter):
            area = (bottom - top + 1) * (right - left + 1)
            if area > best_area:
                best = (color, top, left, bottom, right)
                best_area = area

    if best is None:
        raise ValueError("no solid rectangular frame found")
    return best


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Draw the Manhattan-distance bisector of the two markers inside the frame."""
    _, top, left, bottom, right = _find_frame(grid)

    markers = [
        (r, c)
        for r in range(top + 1, bottom)
        for c in range(left + 1, right)
        if grid[r][c] != 0
    ]
    if len(markers) != 2:
        raise ValueError(f"expected exactly two interior markers, found {len(markers)}")

    (r1, c1), (r2, c2) = markers
    result = [row[:] for row in grid]
    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            if result[r][c] != 0:
                continue
            d1 = abs(r - r1) + abs(c - c1)
            d2 = abs(r - r2) + abs(c - c2)
            if d1 == d2:
                result[r][c] = 9
    return result
