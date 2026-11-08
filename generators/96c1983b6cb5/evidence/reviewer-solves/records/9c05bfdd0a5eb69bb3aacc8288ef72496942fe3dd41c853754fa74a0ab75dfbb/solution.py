from __future__ import annotations


def _rotate90(panel: list[list[int]]) -> list[list[int]]:
    """Rotate a square panel 90 degrees clockwise."""
    n = len(panel)
    return [[panel[n - 1 - r][c] for r in range(n)] for c in range(n)]


def _transforms(panel: list[list[int]]) -> list[list[list[int]]]:
    """Return the eight dihedral images in a stable order."""
    r0 = [row[:] for row in panel]
    r1 = _rotate90(r0)
    r2 = _rotate90(r1)
    r3 = _rotate90(r2)
    # Reflect left/right, then rotate that reflection to obtain the other four.
    f0 = [list(reversed(row)) for row in r0]
    f1 = _rotate90(f0)
    f2 = _rotate90(f1)
    f3 = _rotate90(f2)
    return [r0, r1, r2, r3, f0, f1, f2, f3]


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid or not grid[0]:
        raise ValueError("grid must be nonempty")
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    separators = [
        col
        for col in range(width)
        if all(grid[row][col] == 8 for row in range(height))
    ]
    if len(separators) != 2:
        raise ValueError("expected two full color-8 separator columns")
    first, second = separators
    panel_a = [row[:first] for row in grid]
    panel_b = [row[first + 1 : second] for row in grid]
    panel_c = [row[second + 1 :] for row in grid]
    if not (
        len(panel_a) == len(panel_b) == len(panel_c) == height
        and all(len(row) == height for panel in (panel_a, panel_b, panel_c) for row in panel)
    ):
        raise ValueError("expected three equal square panels")

    matches = [index for index, image in enumerate(_transforms(panel_a)) if image == panel_b]
    if len(matches) != 1:
        raise ValueError(f"expected a unique A-to-B transform, found {len(matches)}")
    return _transforms(panel_c)[matches[0]]
