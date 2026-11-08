"""Infer corner-marked rectangles and complete their blue mirror patterns.

This solver was derived only from solve-blind/challenge.json.
"""


def _rectangles(grid):
    """Yield rectangles whose twelve marker cells form four L corners."""
    height, width = len(grid), len(grid[0])
    marker_colors = {cell for row in grid for cell in row} - {0, 1}
    for color in sorted(marker_colors):
        for top in range(height - 3):
            for left in range(width - 3):
                if not (
                    grid[top][left]
                    == grid[top][left + 1]
                    == grid[top + 1][left]
                    == color
                ):
                    continue
                for bottom in range(top + 3, height):
                    if not (
                        grid[bottom][left]
                        == grid[bottom][left + 1]
                        == grid[bottom - 1][left]
                        == color
                    ):
                        continue
                    for right in range(left + 3, width):
                        corners = {
                            (top, left), (top, left + 1), (top + 1, left),
                            (top, right), (top, right - 1), (top + 1, right),
                            (bottom, left), (bottom, left + 1),
                            (bottom - 1, left), (bottom, right),
                            (bottom, right - 1), (bottom - 1, right),
                        }
                        if not all(grid[r][c] == color for r, c in corners):
                            continue
                        enclosed_markers = {
                            (r, c)
                            for r in range(top, bottom + 1)
                            for c in range(left, right + 1)
                            if grid[r][c] not in (0, 1)
                        }
                        if enclosed_markers == corners:
                            yield top, left, bottom, right


def solve(grid):
    """Return the completed grid without mutating the input."""
    if not grid:
        return []
    output = [[0 if cell == 1 else cell for cell in row] for row in grid]
    for top, left, bottom, right in _rectangles(grid):
        seed = [
            (r, c)
            for r in range(top, bottom + 1)
            for c in range(left, right + 1)
            if grid[r][c] == 1
        ]
        if not seed:
            continue

        min_row = min(r for r, c in seed)
        max_row = max(r for r, c in seed)
        min_col = min(c for r, c in seed)
        max_col = max(c for r, c in seed)
        row_sum = top + bottom
        col_sum = left + right

        # A seed occupying the top/bottom half is copied across a horizontal
        # center line. A seed in the left/right half uses a vertical line.
        row_reflection = 2 * max_row < row_sum or 2 * min_row > row_sum
        col_reflection = 2 * max_col < col_sum or 2 * min_col > col_sum
        if row_reflection != col_reflection:
            reflect_rows = row_reflection
        else:
            # No visible case needs this fallback. Prefer the direction in
            # which the pattern's bounding box is further from frame center.
            reflect_rows = (
                abs(min_row + max_row - row_sum)
                > abs(min_col + max_col - col_sum)
            )

        for r, c in seed:
            output[r][c] = 1
            mirror_r = row_sum - r if reflect_rows else r
            mirror_c = c if reflect_rows else col_sum - c
            if output[mirror_r][mirror_c] in (0, 1):
                output[mirror_r][mirror_c] = 1
    return output
