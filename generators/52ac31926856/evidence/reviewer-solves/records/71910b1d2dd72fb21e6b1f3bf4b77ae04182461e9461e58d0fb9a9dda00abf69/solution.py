"""Visible-example solution for blind task 52ac31926856."""


def solve(grid):
    """Move color 1 into the first intact aligned basin, else the floor.

    Color 2 draws one or more U-shaped basins.  The single color-1 cell is a
    vertical drop marker.  A basin is usable when two vertical color-2 walls
    bracket the marker column and a solid color-2 floor joins them.  Broken
    basins are skipped.  If none can hold the drop, color 1 spreads along the
    bottom edge.
    """
    out = [row[:] for row in grid]
    height = len(out)
    width = len(out[0]) if height else 0

    markers = [
        (r, c)
        for r, row in enumerate(out)
        for c, value in enumerate(row)
        if value == 1
    ]
    if not markers or not height or not width:
        return out

    marker_row, marker_col = markers[0]
    for r, c in markers:
        out[r][c] = 0

    candidates = []
    for left in range(marker_col):
        for right in range(marker_col + 1, width):
            row = marker_row + 1
            while row < height:
                if out[row][left] != 2 or out[row][right] != 2:
                    row += 1
                    continue

                top = row
                while (
                    row + 1 < height
                    and out[row + 1][left] == 2
                    and out[row + 1][right] == 2
                ):
                    row += 1
                bottom = row

                if (
                    bottom > top
                    and all(out[bottom][c] == 2 for c in range(left, right + 1))
                    and all(
                        out[r][c] == 0
                        for r in range(top, bottom)
                        for c in range(left + 1, right)
                    )
                ):
                    # First by vertical encounter; narrower basin breaks ties.
                    candidates.append((top, right - left, left, right, bottom))
                row += 1

    if candidates:
        _, _, left, right, bottom = min(candidates)
        top = min(candidates)[0]
        for r in range(top, bottom):
            for c in range(left + 1, right):
                if out[r][c] == 0:
                    out[r][c] = 1
    else:
        for c in range(width):
            if out[-1][c] == 0:
                out[-1][c] = 1

    return out
