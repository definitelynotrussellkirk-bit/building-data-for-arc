from collections import Counter


def solve(grid):
    """Use the enlarged monochrome stencil to mask the small colored grid."""
    counts = Counter(value for row in grid for value in row if value != 0)
    stencil_color = counts.most_common(1)[0][0]
    colored = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
               if value != 0 and value != stencil_color]
    r0, r1 = min(r for r, _ in colored), max(r for r, _ in colored)
    c0, c1 = min(c for _, c in colored), max(c for _, c in colored)
    h, w = r1 - r0 + 1, c1 - c0 + 1
    stencil = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
               if value == stencil_color and not (r0 <= r <= r1 and c0 <= c <= c1)]
    top, bottom = min(r for r, _ in stencil), max(r for r, _ in stencil)
    left, right = min(c for _, c in stencil), max(c for _, c in stencil)
    if (bottom - top + 1) % h or (right - left + 1) % w:
        raise ValueError("Stencil does not have an integral scale")
    sy, sx = (bottom - top + 1) // h, (right - left + 1) // w
    return [[grid[r0 + r][c0 + c]
             if grid[top + r * sy][left + c * sx] == stencil_color else 0
             for c in range(w)] for r in range(h)]
