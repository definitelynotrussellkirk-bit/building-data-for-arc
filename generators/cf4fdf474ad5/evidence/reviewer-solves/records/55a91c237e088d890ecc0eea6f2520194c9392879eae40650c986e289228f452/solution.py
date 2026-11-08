"""Visible-example solution for the post-repair cf4fdf474ad5 episode."""
from __future__ import annotations


def solve(grid):
    """Crop the eligible nonzero patch with the strongest color-3 count.

    Nonzero cells form separated 4-connected rectangular patches.  Patches
    taller than eight rows are decoys.  Among the remaining patches, choose the
    greatest number of color-3 cells; visible tie evidence indicates smaller
    bounding-box area, then top-left position.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    patches = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and grid[rr][cc] != 0
                        and (rr, cc) not in seen
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))

            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            r1, r2 = min(rows), max(rows)
            c1, c2 = min(cols), max(cols)
            patch_h = r2 - r1 + 1
            patch_w = c2 - c1 + 1
            patches.append(
                {
                    "r1": r1,
                    "c1": c1,
                    "r2": r2,
                    "c2": c2,
                    "height": patch_h,
                    "area": patch_h * patch_w,
                    "green": sum(grid[r][c] == 3 for r, c in cells),
                }
            )

    eligible = [patch for patch in patches if patch["height"] <= 8]
    if not eligible:
        raise ValueError("no eligible patch")
    chosen = min(
        eligible,
        key=lambda patch: (
            -patch["green"],
            patch["area"],
            patch["r1"],
            patch["c1"],
        ),
    )
    return [
        list(row[chosen["c1"] : chosen["c2"] + 1])
        for row in grid[chosen["r1"] : chosen["r2"] + 1]
    ]
