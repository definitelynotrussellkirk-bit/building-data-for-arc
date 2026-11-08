from __future__ import annotations


def _orientations(points: set[tuple[int, int]], height: int, width: int):
    """Yield the distinct dihedral orientations of a marker mask."""
    transforms = (
        (height, width, lambda r, c: (r, c)),
        (width, height, lambda r, c: (c, height - 1 - r)),
        (height, width, lambda r, c: (height - 1 - r, width - 1 - c)),
        (width, height, lambda r, c: (width - 1 - c, r)),
        (height, width, lambda r, c: (r, width - 1 - c)),
        (height, width, lambda r, c: (height - 1 - r, c)),
        (width, height, lambda r, c: (c, r)),
        (width, height, lambda r, c: (width - 1 - c, height - 1 - r)),
    )

    seen: set[tuple[int, int, tuple[tuple[int, int], ...]]] = set()
    for out_h, out_w, transform in transforms:
        oriented = tuple(sorted(transform(r, c) for r, c in points))
        key = (out_h, out_w, oriented)
        if key not in seen:
            seen.add(key)
            yield out_h, out_w, set(oriented)


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    source = [row[:] for row in grid]
    result = [row[:] for row in grid]

    blue = [(r, c) for r in range(height) for c in range(width) if source[r][c] == 1]
    if not blue:
        return result

    top = min(r for r, _ in blue)
    bottom = max(r for r, _ in blue)
    left = min(c for _, c in blue)
    right = max(c for _, c in blue)
    box_h = bottom - top + 1
    box_w = right - left + 1

    markers = {
        (r - top, c - left)
        for r in range(top, bottom + 1)
        for c in range(left, right + 1)
        if source[r][c] == 4
    }
    if not markers:
        return result

    minimum_visible = min(2, len(markers))

    for oriented_h, oriented_w, oriented_markers in _orientations(markers, box_h, box_w):
        # Origins may lie just outside the grid.  Such a placement is accepted
        # when at least two of its marker cells remain visible, matching the
        # clipped examples at the lower edge.
        for origin_r in range(-oriented_h + 1, height):
            row_start = max(0, origin_r)
            row_stop = min(height, origin_r + oriented_h)
            if row_start >= row_stop:
                continue

            for origin_c in range(-oriented_w + 1, width):
                col_start = max(0, origin_c)
                col_stop = min(width, origin_c + oriented_w)
                if col_start >= col_stop:
                    continue

                visible_markers = {
                    (origin_r + r, origin_c + c)
                    for r, c in oriented_markers
                    if 0 <= origin_r + r < height and 0 <= origin_c + c < width
                }
                if len(visible_markers) < minimum_visible:
                    continue
                if any(source[r][c] != 4 for r, c in visible_markers):
                    continue

                actual_markers = {
                    (r, c)
                    for r in range(row_start, row_stop)
                    for c in range(col_start, col_stop)
                    if source[r][c] == 4
                }
                if actual_markers != visible_markers:
                    continue

                for r in range(row_start, row_stop):
                    for c in range(col_start, col_stop):
                        if result[r][c] == 0:
                            result[r][c] = 1

    return result
