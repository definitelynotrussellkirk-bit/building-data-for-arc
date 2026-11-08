from __future__ import annotations


def solve(grid):
    """Collapse the gray marker mass into a centered bar between separators."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    # This task consistently uses orange background, black separators, and gray
    # marker cells.  A separator row/column can be interrupted by gray cells, so
    # identify it by the absence of background rather than by requiring all zeroes.
    background = 7
    separator = 0
    marker = 5

    separator_rows = [
        r
        for r, row in enumerate(grid)
        if separator in row and all(value in (separator, marker) for value in row)
    ]
    separator_cols = [
        c
        for c in range(width)
        if any(grid[r][c] == separator for r in range(height))
        and all(grid[r][c] in (separator, marker) for r in range(height))
    ]

    marker_count = sum(value == marker for row in grid for value in row)
    if marker_count == 0:
        return [row[:] for row in grid]

    out = [[background for _ in range(width)] for _ in range(height)]

    if len(separator_rows) == 2 and len(separator_cols) == 1:
        center_r = (separator_rows[0] + separator_rows[1]) // 2
        center_c = separator_cols[0]

        for r in range(height):
            out[r][center_c] = separator
        for r in (center_r - 1, center_r + 1):
            if 0 <= r < height:
                out[r] = [separator] * width

        start_c = center_c - marker_count // 2
        end_c = start_c + marker_count
        if start_c < 0 or end_c > width:
            raise ValueError("marker bar does not fit horizontally")
        for c in range(start_c, end_c):
            out[center_r][c] = marker
        return out

    if len(separator_cols) == 2 and len(separator_rows) == 1:
        center_c = (separator_cols[0] + separator_cols[1]) // 2
        center_r = separator_rows[0]

        out[center_r] = [separator] * width
        for c in (center_c - 1, center_c + 1):
            if 0 <= c < width:
                for r in range(height):
                    out[r][c] = separator

        start_r = center_r - marker_count // 2
        end_r = start_r + marker_count
        if start_r < 0 or end_r > height:
            raise ValueError("marker bar does not fit vertically")
        for r in range(start_r, end_r):
            out[r][center_c] = marker
        return out

    raise ValueError(
        f"expected either two separator rows and one column or vice versa; "
        f"got rows={separator_rows}, cols={separator_cols}"
    )
