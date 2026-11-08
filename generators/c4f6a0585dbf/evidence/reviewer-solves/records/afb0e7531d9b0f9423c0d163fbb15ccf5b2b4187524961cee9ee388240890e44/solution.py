"""Visible-example solution for blind task c4f6a0585dbf."""


def _rotations(pattern, height, width):
    """Return unique clockwise rotations as (height, width, coordinates)."""
    variants = []
    seen = set()
    current = set(pattern)
    h, w = height, width
    for _ in range(4):
        key = (h, w, tuple(sorted(current)))
        if key not in seen:
            seen.add(key)
            variants.append((h, w, set(current)))
        current = {(c, h - 1 - r) for r, c in current}
        h, w = w, h
    return variants


def solve(grid):
    """Box every exact rotated copy of the pattern embedded in the 1-region."""
    height = len(grid)
    width = len(grid[0])
    original = [row[:] for row in grid]
    result = [row[:] for row in grid]

    ones = [(r, c) for r, row in enumerate(original) for c, value in enumerate(row) if value == 1]
    if not ones:
        return result

    top = min(r for r, _ in ones)
    bottom = max(r for r, _ in ones)
    left = min(c for _, c in ones)
    right = max(c for _, c in ones)
    box_h = bottom - top + 1
    box_w = right - left + 1

    pattern = {
        (r - top, c - left)
        for r in range(top, bottom + 1)
        for c in range(left, right + 1)
        if original[r][c] == 4
    }
    if not pattern:
        return result

    for stamp_h, stamp_w, rotated_pattern in _rotations(pattern, box_h, box_w):
        # The frame may be clipped by an outer grid edge, but every defining 4
        # remains visible.  Negative origins therefore need to be considered.
        for origin_r in range(-stamp_h + 1, height):
            for origin_c in range(-stamp_w + 1, width):
                expected = {
                    (origin_r + r, origin_c + c)
                    for r, c in rotated_pattern
                }
                if not all(0 <= r < height and 0 <= c < width for r, c in expected):
                    continue
                if any(original[r][c] != 4 for r, c in expected):
                    continue

                visible_top = max(0, origin_r)
                visible_bottom = min(height, origin_r + stamp_h)
                visible_left = max(0, origin_c)
                visible_right = min(width, origin_c + stamp_w)

                actual_fours = {
                    (r, c)
                    for r in range(visible_top, visible_bottom)
                    for c in range(visible_left, visible_right)
                    if original[r][c] == 4
                }
                if actual_fours != expected:
                    continue

                for r in range(visible_top, visible_bottom):
                    for c in range(visible_left, visible_right):
                        if result[r][c] == 0:
                            result[r][c] = 1

    return result
