from __future__ import annotations


def _normalize(cells: set[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _transform(
    cells: tuple[tuple[int, int], ...], code: int
) -> tuple[tuple[int, int], ...]:
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    out = []
    for r, c in cells:
        if code == 1:       # identity
            nr, nc = r, c
        elif code == 2:     # left-right mirror
            nr, nc = r, w - 1 - c
        elif code == 3:     # top-bottom mirror
            nr, nc = h - 1 - r, c
        elif code == 4:     # clockwise quarter-turn
            nr, nc = c, h - 1 - r
        elif code == 5:     # half-turn
            nr, nc = h - 1 - r, w - 1 - c
        elif code == 6:     # counter-clockwise quarter-turn
            nr, nc = w - 1 - c, r
        else:
            raise ValueError(f"unknown transform code {code}")
        out.append((nr, nc))
    return _normalize(set(out))


def _panel(cells: tuple[tuple[int, int], ...], color: int) -> list[list[int]]:
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    grid = [[0] * w for _ in range(h)]
    for r, c in cells:
        grid[r][c] = color
    return grid


def solve(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    codes = [grid[0][c] for c in range(1, w) if grid[0][c] != 0]
    colors = [grid[r][0] for r in range(1, h) if grid[r][0] != 0]
    body = {
        (r, c)
        for r in range(1, h)
        for c in range(1, w)
        if grid[r][c] != 0
    }
    shape = _normalize(body)

    transformed = [_transform(shape, code) for code in codes]
    panels = [[_panel(cells, color) for cells in transformed] for color in colors]

    # The examples use the first transformed panel as the common gallery cell
    # footprint and clip any spill from a differently shaped quarter-turn.
    panel_h = len(panels[0][0])
    panel_w = len(panels[0][0][0])
    out_h = len(colors) * panel_h + len(colors) - 1
    out_w = len(codes) * panel_w + len(codes) - 1
    out = [[0] * out_w for _ in range(out_h)]
    for color_index, row_panels in enumerate(panels):
        for code_index, panel in enumerate(row_panels):
            r0 = color_index * (panel_h + 1)
            c0 = code_index * (panel_w + 1)
            for r, row in enumerate(panel):
                for c, value in enumerate(row):
                    rr, cc = r0 + r, c0 + c
                    if value and 0 <= rr < out_h and 0 <= cc < out_w:
                        out[rr][cc] = value
    return out
