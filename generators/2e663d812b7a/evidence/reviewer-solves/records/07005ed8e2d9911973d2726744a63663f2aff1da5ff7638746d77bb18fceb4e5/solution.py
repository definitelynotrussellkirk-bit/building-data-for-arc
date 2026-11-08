from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Expand the key in row 0 into square Chebyshev-distance rings.

    Row 1 is a fixed separator.  The first key color marks the center below
    the separator; each later key cell supplies the next outward ring color.
    Trailing zero cells are padding, while zeroes before the last nonzero key
    are real transparent/background rings.
    """
    out = [row[:] for row in grid]
    if len(out) < 3 or not out[0]:
        return out

    height = len(out)
    width = len(out[0])
    separator_row = 1
    drawing_top = separator_row + 1

    # The key occupies row 0 through its last nonzero cell.  This preserves
    # interior zero rings while excluding the zero padding to the right.
    try:
        key_end = max(i for i, value in enumerate(out[0]) if value != 0)
    except ValueError:
        return out
    key = out[0][: key_end + 1]
    center_color = key[0]

    centers: list[tuple[int, int]] = []
    for r in range(drawing_top, height):
        for c, value in enumerate(out[r]):
            if value == center_color:
                centers.append((r, c))

    if not centers:
        return out

    for center_r, center_c in centers:
        for radius, color in enumerate(key[1:], start=1):
            top = center_r - radius
            bottom = center_r + radius
            left = center_c - radius
            right = center_c + radius

            # A non-background key is crossed out with separator color when
            # its complete square cannot fit in the lower drawing field.
            if color != 0 and (
                top < drawing_top
                or bottom >= height
                or left < 0
                or right >= width
            ):
                if radius < width:
                    out[0][radius] = out[separator_row][0]

            # Draw only the visible part of the exact square ring, never over
            # the key or separator rows.
            for r in range(max(drawing_top, top), min(height - 1, bottom) + 1):
                for c in range(max(0, left), min(width - 1, right) + 1):
                    if max(abs(r - center_r), abs(c - center_c)) == radius:
                        out[r][c] = color

    return out
