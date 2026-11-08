"""Visible-example solution for the blind ARC task."""

from collections import Counter, deque


def _components(grid, background):
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if seen[r][c] or grid[r][c] == background:
                continue
            seen[r][c] = True
            q = deque([(r, c)])
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and grid[nr][nc] != background
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))
            yield cells


def _draw_inset_x(out, top, left, bottom, right, frame_color, ink_color):
    """Replace a solid rectangle by its frame and centered inset-X skeleton."""
    # Clear the component's rectangular support, then restore its frame.
    for r in range(top, bottom + 1):
        for c in range(left, right + 1):
            out[r][c] = 0
    for c in range(left, right + 1):
        out[top][c] = frame_color
        out[bottom][c] = frame_color
    for r in range(top, bottom + 1):
        out[r][left] = frame_color
        out[r][right] = frame_color

    ih = bottom - top - 1
    iw = right - left - 1
    if ih <= 0 or iw <= 0:
        return

    max_dr = (ih - 1) // 2
    max_dc = (iw - 1) // 2
    for ir in range(ih):
        dr = min(ir, ih - 1 - ir)
        for ic in range(iw):
            dc = min(ic, iw - 1 - ic)
            on_diagonal = dr == dc
            horizontal_bridge = max_dr < max_dc and dr == max_dr and dc >= dr
            vertical_bridge = max_dc < max_dr and dc == max_dc and dr >= dc
            if on_diagonal or horizontal_bridge or vertical_bridge:
                out[top + 1 + ir][left + 1 + ic] = ink_color


def solve(grid):
    """Transform every marked solid rectangle seen in the visible examples."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    out = [row[:] for row in grid]

    for cells in _components(grid, background):
        top = min(r for r, _ in cells)
        bottom = max(r for r, _ in cells)
        left = min(c for _, c in cells)
        right = max(c for _, c in cells)
        colors = Counter(grid[r][c] for r, c in cells)
        if len(colors) < 2:
            continue
        frame_color = colors.most_common(1)[0][0]
        # The examples contain exactly one anomalous marker; choosing the least
        # frequent color also handles a future marker repeated more than once.
        ink_color = min(colors, key=lambda color: (colors[color], color))
        _draw_inset_x(out, top, left, bottom, right, frame_color, ink_color)

    return out
