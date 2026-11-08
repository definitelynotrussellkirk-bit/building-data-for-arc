from collections import Counter


def solve(grid):
    """Rebuild the framed hourglass/X encoded by the off-color marker cells."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height, width = len(grid), len(grid[0])
    background = grid[0][0]
    occupied = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != background
    ]
    if not occupied:
        return [row[:] for row in grid]

    top = min(r for r, _ in occupied)
    bottom = max(r for r, _ in occupied)
    left = min(c for _, c in occupied)
    right = max(c for _, c in occupied)

    counts = Counter(
        grid[r][c]
        for r in range(top, bottom + 1)
        for c in range(left, right + 1)
        if grid[r][c] != background
    )
    base = counts.most_common(1)[0][0]
    accents = [color for color in counts if color != base]
    if not accents:
        return [row[:] for row in grid]
    accent = min(accents, key=lambda color: counts[color])

    out = [[background for _ in range(width)] for _ in range(height)]

    # Restore the one-cell frame.
    for c in range(left, right + 1):
        out[top][c] = base
        out[bottom][c] = base
    for r in range(top, bottom + 1):
        out[r][left] = base
        out[r][right] = base

    inner_top, inner_bottom = top + 1, bottom - 1
    inner_left, inner_right = left + 1, right - 1
    inner_h = max(0, inner_bottom - inner_top + 1)
    inner_w = max(0, inner_right - inner_left + 1)
    if inner_h == 0 or inner_w == 0:
        return out

    inset = (min(inner_h, inner_w) - 1) // 2

    # Four inward 45-degree arms.
    for d in range(inset):
        out[inner_top + d][inner_left + d] = accent
        out[inner_top + d][inner_right - d] = accent
        out[inner_bottom - d][inner_left + d] = accent
        out[inner_bottom - d][inner_right - d] = accent

    # When the interior is rectangular (or even-sized), the arms meet in a strip.
    for r in range(inner_top + inset, inner_bottom - inset + 1):
        for c in range(inner_left + inset, inner_right - inset + 1):
            out[r][c] = accent

    return out
