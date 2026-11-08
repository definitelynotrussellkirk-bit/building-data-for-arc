from collections import deque


def _vertical_red_bars(grid):
    """Return vertical 4-connected components of red (2) cells as (top,bottom,col)."""
    h, w = len(grid), len(grid[0])
    seen = set()
    bars = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 2 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 2 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cols = {cc for _, cc in cells}
            rows = sorted(rr for rr, _ in cells)
            if len(cols) == 1 and rows == list(range(rows[0], rows[-1] + 1)):
                bars.append((rows[0], rows[-1], next(iter(cols))))
    return bars


def solve(grid):
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    bars = _vertical_red_bars(grid)
    if len(bars) != 2:
        return out

    # The bar whose row band contains the azure markers is the measured bar.
    marker_counts = []
    for top, bottom, col in bars:
        inward = 1 if col < w / 2 else -1
        count = 0
        markers = []
        for r in range(top, bottom + 1):
            for c in range(w):
                if grid[r][c] == 8 and (c - col) * inward > 0:
                    count += 1
                    markers.append((r, c))
        marker_counts.append((count, markers))

    marker_idx = 0 if marker_counts[0][0] >= marker_counts[1][0] else 1
    source = bars[marker_idx]
    target = bars[1 - marker_idx]
    markers = marker_counts[marker_idx][1]
    if not markers:
        return out

    s_top, s_bottom, s_col = source
    t_top, t_bottom, t_col = target
    if (s_bottom - s_top) != (t_bottom - t_top):
        return out

    s_dir = 1 if s_col < w / 2 else -1
    t_dir = 1 if t_col < w / 2 else -1

    for r, marker_col in markers:
        # On the measured bar, extend azure from the bar up to the marker and
        # recolor the terminal marker green.
        c = s_col + s_dir
        while c != marker_col:
            out[r][c] = 8
            c += s_dir
        out[r][marker_col] = 4

        # Copy the active relative row to the opposite bar, extending inward
        # all the way to that side's far edge.
        target_r = t_top + (r - s_top)
        c = t_col + t_dir
        while 0 <= c < w:
            out[target_r][c] = 8
            c += t_dir

    return out
